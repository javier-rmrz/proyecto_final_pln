"""
Apoyo a la REVISION MANUAL de las consultas (Hito 1).

Calcula, para cada consulta, cuanto copia de su receta de origen, y genera la
tabla de `REVISION_consultas.md` con un veredicto *sugerido* que la persona que
revisa confirma o cambia en la columna "Revision manual".

Medidas (sobre palabras en minusculas, sin stopwords de spaCy ni la palabra
"recipe", que no aporta):
  - Solape   : % de palabras de la consulta que aparecen en el texto de la receta.
  - Titulo   : % de palabras del TITULO de la receta que la consulta repite.
               Es el indicador mas directo de "copiar el titulo".

Veredicto sugerido (umbral orientativo, NO sustituye a la revision humana):
  - DESCARTAR si Titulo >= 75 % y Solape >= 80 % (casi copia del titulo).
  - REVISAR   si Solape >= 70 %, o si un titulo de 3 o mas palabras se repite
              en un 75 % o mas (con titulos de 1-2 palabras, p. ej. "Egg
              Sandwich", nombrar el plato es inevitable y no se penaliza).
  - MANTENER  en otro caso.

Uso:
    python -m src.review_queries                      # imprime la tabla
    python -m src.review_queries --write REVISION.md  # la escribe en un fichero
"""

from __future__ import annotations

import argparse
import re

from src.corpus import load_jsonl
from src.generate_queries import load_queries

_EXTRA_STOP = {"recipe", "recipes"}


def _stopwords() -> set[str]:
    from spacy.lang.en.stop_words import STOP_WORDS

    return set(STOP_WORDS) | _EXTRA_STOP


def content_words(text: str, stop: set[str]) -> list[str]:
    """Palabras alfabeticas en minusculas que no son stopwords."""
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in stop]


def overlap_stats(query: str, doc_text: str, stop: set[str]) -> dict:
    """Solape consulta-receta y consulta-titulo (en %, redondeado)."""
    q = content_words(query, stop)
    doc = set(content_words(doc_text, stop))
    title = set(content_words(doc_text.splitlines()[0], stop))
    q_set = set(q)
    solape = 100 * sum(w in doc for w in q) / len(q) if q else 0.0
    tit = 100 * len(title & q_set) / len(title) if title else 0.0
    return {"solape": round(solape), "titulo": round(tit), "n_titulo": len(title)}


def suggest(stats: dict) -> tuple[str, str]:
    """Veredicto sugerido y motivo. Ver reglas en la cabecera del modulo."""
    long_title = stats["n_titulo"] >= 3
    if stats["titulo"] >= 75 and stats["solape"] >= 80:
        return "DESCARTAR", "Casi copia del título y del texto."
    if long_title and stats["titulo"] >= 85:
        return "REVISAR", "Repite el título completo."
    if stats["solape"] >= 70:
        return "REVISAR", "Solape alto con el texto de la receta."
    if long_title and stats["titulo"] >= 75:
        return "REVISAR", "Repite casi todo el título."
    return "MANTENER", ""


def review_rows(queries: list[dict], docs_by_id: dict[str, str]) -> list[dict]:
    stop = _stopwords()
    rows = []
    for q in queries:
        doc_text = docs_by_id[q["relevant_ids"][0]]
        stats = overlap_stats(q["query"], doc_text, stop)
        verdict, reason = suggest(stats)
        rows.append(
            {
                "qid": q["qid"],
                "query": q["query"],
                "title": doc_text.splitlines()[0].strip(),
                **stats,
                "sugerido": verdict,
                "motivo": reason,
            }
        )
    return rows


def to_markdown(rows: list[dict]) -> str:
    head = (
        "| qid | Consulta | Receta de origen (título) | Solape | Título "
        "| Sugerido | Motivo | Revisión manual |\n"
        "|-----|----------|---------------------------|:------:|:------:"
        "|----------|--------|-----------------|\n"
    )
    body = "".join(
        f"| {r['qid']} | {r['query']} | {r['title']} | {r['solape']}% | {r['titulo']}% "
        f"| {r['sugerido']} | {r['motivo']} |  |\n"
        for r in rows
    )
    return head + body


def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--corpus", default="data/corpus_foodcom.jsonl")
    ap.add_argument("--queries", default="data/queries_foodcom.jsonl")
    ap.add_argument("--write", default=None, help="fichero .md donde escribir la tabla")
    args = ap.parse_args()

    docs_by_id = {d["doc_id"]: d["text"] for d in load_jsonl(args.corpus)}
    rows = review_rows(load_queries(args.queries), docs_by_id)
    md = to_markdown(rows)
    if args.write:
        with open(args.write, "w", encoding="utf-8") as fh:
            fh.write(md)
    else:
        print(md)


if __name__ == "__main__":
    _main()
