"""
Generacion del conjunto de consultas de evaluacion (`queries.jsonl`) con un LLM.

Enunciado: "Al menos 30 consultas de tipo known-item: se seleccionan documentos
al azar y se pide a un LLM que escriba, para cada uno, la consulta que haria un
usuario que buscara ese documento, SIN COPIAR sus frases. [...] Debeis revisar
manualmente al menos 10 consultas, descartando las triviales o ambiguas, y
documentar esta revision."

Formato de salida (una linea por consulta):
    {"qid": "q01", "query": "...", "relevant_ids": ["doc_123"]}

El cliente LLM hace un POST a la API de Ollama (/api/generate). Soporta:
  - Ollama local      (http://localhost:11434/api/generate)
  - Servidor UC3M     (https://yiyuan.tsc.uc3m.es/api/generate con X-API-KEY)
"""

from __future__ import annotations

import json
import pathlib
import random

# El prompt va en INGLES y exige la consulta en ingles, porque la consulta debe
# estar en el MISMO idioma que el corpus para que un baseline lexico (TF-IDF/BM25)
# tenga solape de terminos. (Para un corpus en espanol, traduce este prompt.)
PROMPT_TEMPLATE = (
    "You are a user of a search engine. Below is the content of a recipe. Imagine you "
    "vaguely remember this dish and want to find it again. Write ONE natural search "
    "query describing it from memory.\n"
    "Strict rules:\n"
    "- Write the query in ENGLISH.\n"
    "- Do NOT reuse the exact words of the recipe. In particular, AVOID copying the "
    "dish title and AVOID listing its exact ingredient names. Paraphrase with "
    "synonyms and describe it instead (type of dish, cuisine, cooking method, texture, "
    "flavour, occasion, or main idea).\n"
    "- Still make it specific enough to point to THIS recipe, not a generic one.\n"
    "- Between 6 and 18 words. Reply with ONLY the query, no quotes, no prefixes.\n\n"
    "RECIPE:\n{document}\n\nQUERY (describe it in your own words):"
)


def call_ollama(
    prompt: str,
    model: str = "qwen2.5:1.5b",
    url: str = "http://localhost:11434/api/generate",
    api_key: str | None = None,
    temperature: float = 0.7,
    timeout: int = 60,
) -> str:
    """Llama a un endpoint tipo Ollama /api/generate y devuelve el texto generado."""
    import requests

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-KEY"] = api_key

    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout, verify=False)
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def generate_queries(
    docs: list[dict],
    n_queries: int = 35,
    seed: int = 11235,
    max_chars: int = 1500,
    llm=call_ollama,
    **llm_kwargs,
) -> list[dict]:
    """
    Selecciona n_queries documentos al azar y genera una consulta known-item por
    cada uno con el LLM. Genera unas cuantas de mas (recomendado 35+) para poder
    descartar en la revision manual y conservar >= 30 validas.

    `llm` es una funcion (prompt, **kwargs) -> str; por defecto, Ollama.
    """
    rng = random.Random(seed)
    chosen = rng.sample(docs, min(n_queries, len(docs)))
    out: list[dict] = []
    for i, doc in enumerate(chosen, start=1):
        prompt = PROMPT_TEMPLATE.format(document=doc["text"][:max_chars])
        try:
            query = llm(prompt, **llm_kwargs)
        except Exception as exc:  # noqa: BLE001
            query = ""
            print(f"[q{i:02d}] error al generar: {exc}")
        out.append(
            {
                "qid": f"q{i:02d}",
                "query": query,
                "relevant_ids": [doc["doc_id"]],
                # Fragmento de origen (formato del enunciado). Como la unidad de
                # indexacion es el documento completo, el "chunk" es el propio
                # documento, por lo que source_chunk == doc_id.
                "source_chunk": doc["doc_id"],
                # campo auxiliar SOLO para la revision manual (se descarta al guardar):
                "_source_preview": doc["text"][:200],
            }
        )
    return out


def save_queries(queries: list[dict], path: str | pathlib.Path, drop_aux: bool = True) -> None:
    """Guarda las consultas en JSONL. Si drop_aux, elimina campos auxiliares '_*'."""
    path = pathlib.Path(path)
    with path.open("w", encoding="utf-8") as fh:
        for q in queries:
            obj = {k: v for k, v in q.items() if not (drop_aux and k.startswith("_"))}
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def load_queries(path: str | pathlib.Path) -> list[dict]:
    """Carga un queries.jsonl."""
    path = pathlib.Path(path)
    queries: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    return queries


def print_for_review(queries: list[dict], n: int = 10) -> None:
    """
    Imprime las primeras n consultas para la REVISION MANUAL exigida por el
    enunciado. Marca con [?] las sospechosas (vacias o muy cortas) para ayudar a
    decidir cuales descartar. Documenta tus decisiones en el MILESTONE_1.md.
    """
    print(f"=== REVISION MANUAL de {n} consultas ===\n")
    for q in queries[:n]:
        words = len((q.get("query") or "").split())
        flag = "[?]" if words < 4 else "   "
        print(f"{flag} {q['qid']}  (rel={q['relevant_ids']}, {words} palabras)")
        print(f"      query : {q.get('query')!r}")
        if "_source_preview" in q:
            print(f"      origen: {q['_source_preview']!r}")
        print()
