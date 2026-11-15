"""
Adaptador Food.com -> corpus del Hito 1.

Convierte el dataset de recetas de Food.com en un
`corpus.jsonl` con una receta por documento, en el formato que espera el notebook:

    {"doc_id": "recipe_<id>", "text": "<titulo + ingredientes + instrucciones>"}

Dataset: https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews
Admite el Parquet de Food.com (columnas ya como
listas) o el CSV original de Kaggle (recipes.csv, listas en formato R: c("a","b")).

Uso por linea de comandos (desde la carpeta Hito1):
    python -m src.foodcom  --input C:\\ruta\\foodcom_recipes.parquet  \\
                           --output data\\corpus_foodcom.jsonl  --n 3000

Luego en el notebook:  CORPUS_PATH = "data/corpus_foodcom.jsonl"
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re


# Columnas de texto usadas del dataset; RecipeId se usa para el doc_id.
TEXT_COLS = ["Name", "RecipeIngredientParts", "RecipeInstructions"]
FILTER_COLS = ["Calories", "ProteinContent", "CarbohydrateContent", "FatContent"]


def _to_list(val) -> list[str]:
    """
    Normaliza un campo de lista a list[str]. Soporta:
      - listas / arrays de numpy (formato Parquet)
      - cadenas en formato R: c("a", "b")  (CSV de Kaggle)
      - cadena simple -> [cadena]
    """
    import numpy as np

    if isinstance(val, (list, tuple, np.ndarray)):
        return [str(v).strip() for v in val if str(v).strip()]
    if isinstance(val, str):
        s = val.strip()
        if s.startswith("c(") and s.endswith(")"):
            # c("huevo", "harina") -> ['huevo', 'harina']
            inner = s[2:-1]
            parts = re.findall(r'"((?:[^"\\]|\\.)*)"', inner)
            return [p.strip() for p in parts if p.strip()]
        return [s] if s else []
    return []


def recipe_to_text(row) -> str:
    """Construye el texto del documento: titulo + ingredientes + pasos."""
    name = html.unescape(str(row.get("Name", "") or "").strip())
    ingredients = [html.unescape(x) for x in _to_list(row.get("RecipeIngredientParts"))]
    steps = [html.unescape(x) for x in _to_list(row.get("RecipeInstructions"))]

    partes = []
    if name:
        partes.append(name)
    if ingredients:
        partes.append("Ingredients: " + ", ".join(ingredients))
    if steps:
        partes.append("Instructions: " + " ".join(steps))
    return "\n".join(partes)


def load_recipes(input_path: str | pathlib.Path):
    """Carga el dataset (Parquet o CSV) en un DataFrame de pandas."""
    import pandas as pd

    path = pathlib.Path(input_path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def build_corpus(
    input_path: str | pathlib.Path,
    output_path: str | pathlib.Path,
    n: int = 3000,
    seed: int = 42,
    apply_quality_filter: bool = True,
    stratify_col: str | None = "RecipeCategory",
) -> int:
    """
    Lee el dataset, aplica filtros de coherencia y muestrea n recetas (de forma
    estratificada por categoria si stratify_col existe, para asegurar variedad).
    Escribe el corpus.jsonl y devuelve el nº de documentos.
    """
    import pandas as pd  # noqa: F401

    df = load_recipes(input_path)

    # doc_id estable: RecipeId si existe (como entero), si no el indice original.
    def _clean_id(x):
        try:
            return str(int(float(x)))
        except (TypeError, ValueError):
            return str(x)

    if "RecipeId" in df.columns:
        df = df.assign(_doc_id=df["RecipeId"].map(_clean_id))
    else:
        df = df.assign(_doc_id=df.index.astype(str))

    if apply_quality_filter:
        df = _quality_filter(df)

    if stratify_col and stratify_col in df.columns:
        sampled = stratified_sample(df, n, stratify_col, seed=seed)
    else:
        n = min(n, len(df))
        sampled = df.sample(n, random_state=seed).reset_index(drop=True)

    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with output_path.open("w", encoding="utf-8") as fh:
        for _, row in sampled.iterrows():
            text = recipe_to_text(row)
            if not text.strip():
                continue
            doc = {"doc_id": f"recipe_{row['_doc_id']}", "text": text}
            fh.write(json.dumps(doc, ensure_ascii=False) + "\n")
            written += 1
    return written


def _quality_filter(df, min_steps: int = 2, min_instr_chars: int = 60):
    """
    Filtros de COHERENCIA. Exigen
    requisitos para que cada receta sea un documento con sentido: nombre presente,
    varios ingredientes, varios pasos e instrucciones con longitud razonable.
    """
    mask = df["Name"].notna() & (df["Name"].astype(str).str.strip() != "")
    # Nº de ingredientes, nº de pasos y longitud total de las instrucciones
    n_ing = df["RecipeIngredientParts"].apply(lambda x: len(_to_list(x)))
    steps = df["RecipeInstructions"].apply(_to_list)
    n_steps = steps.apply(len)
    instr_chars = steps.apply(lambda s: sum(len(x) for x in s))
    mask &= n_ing.between(2, 20) & (n_steps >= min_steps) & (instr_chars >= min_instr_chars)
    # Filtros nutricionales (solo si estan las columnas)
    if all(c in df.columns for c in FILTER_COLS):
        mask &= (
            df["Calories"].between(50, 2000)
            & df["ProteinContent"].between(0, 150)
            & df["CarbohydrateContent"].between(0, 300)
            & df["FatContent"].between(0, 150)
        )
    return df[mask]


def stratified_sample(df, n: int, cat_col: str, seed: int = 42, cap_ratio: float = 3.0):
    """
    Muestreo estratificado por categoria para asegurar VARIEDAD: ninguna categoria
    (p. ej. Dessert) puede dominar. Cada categoria aporta como mucho cap_ratio veces
    su cuota equitativa (n / nº_categorias). Si falta para llegar a n, se completa
    con recetas aleatorias del resto.
    """
    import pandas as pd

    if cat_col not in df.columns:
        return df.sample(min(n, len(df)), random_state=seed).reset_index(drop=True)

    work = df[df[cat_col].notna()].copy()
    n_cats = work[cat_col].nunique()
    cap = max(1, int(round((n / n_cats) * cap_ratio)))

    partes = []
    for _, grupo in work.groupby(cat_col):
        k = min(len(grupo), cap)
        partes.append(grupo.sample(k, random_state=seed))
    pool = pd.concat(partes)

    if len(pool) >= n:
        return pool.sample(n, random_state=seed).reset_index(drop=True)
    # completar con recetas que no entraron todavia
    resto = df.drop(index=pool.index)
    falta = min(n - len(pool), len(resto))
    if falta > 0:
        pool = pd.concat([pool, resto.sample(falta, random_state=seed)])
    return pool.sample(frac=1, random_state=seed).reset_index(drop=True)


def _main() -> None:
    ap = argparse.ArgumentParser(description="Food.com -> corpus.jsonl (Hito 1)")
    ap.add_argument("--input", required=True, help="Parquet o CSV de Food.com (Kaggle)")
    ap.add_argument("--output", default="data/corpus_foodcom.jsonl")
    ap.add_argument("--n", type=int, default=3000, help="nº de recetas a muestrear")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-filter", action="store_true", help="no aplicar filtros de calidad")
    args = ap.parse_args()

    written = build_corpus(
        args.input, args.output, n=args.n, seed=args.seed,
        apply_quality_filter=not args.no_filter,
    )
    print(f"Corpus escrito: {written} recetas -> {args.output}")


if __name__ == "__main__":
    _main()
