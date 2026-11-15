"""
Evaluacion de recuperacion para el Hito 1: Recall@K y MRR.

Evaluacion *known-item*: cada consulta tiene uno (o varios) documentos
relevantes (`relevant_ids`). Se mide si aparecen entre los primeros K resultados.

  - Recall@K: fraccion de documentos relevantes recuperados en el top-K.
             (En known-item con 1 relevante equivale a "esta en el top-K": 0/1.)
  - MRR    : media del inverso de la posicion del primer relevante
             (0 si no aparece en los resultados devueltos).

`recall_at_k` usa la definicion estandar de Recall@K.
`mrr` calcula el Mean Reciprocal Rank.
"""

from __future__ import annotations

from dataclasses import dataclass


def relevance_flags(ranked_ids: list[str], relevant_ids: set[str]) -> list[bool]:
    """Convierte un ranking de doc_ids en una lista de booleanos de relevancia."""
    return [doc_id in relevant_ids for doc_id in ranked_ids]


def recall_at_k(flags: list[bool], total_relevant: int, k: int) -> float:
    """Recall@K: relevantes en top-K sobre el total de relevantes de la consulta."""
    if total_relevant <= 0:
        return 0.0
    return sum(flags[:k]) / total_relevant


def reciprocal_rank(flags: list[bool]) -> float:
    """1 / posicion del primer relevante; 0 si no hay ninguno en la lista."""
    for i, is_rel in enumerate(flags, start=1):
        if is_rel:
            return 1.0 / i
    return 0.0


@dataclass
class QueryResult:
    qid: str
    query: str
    relevant_ids: list[str]
    ranked_ids: list[str]
    first_relevant_rank: int | None  # posicion (1-based) del primer relevante, o None
    rr: float
    recall: dict[int, float]         # {k: recall@k}


def evaluate(
    retriever,
    queries: list[dict],
    preprocess_fn,
    ks: tuple[int, ...] = (5, 10),
    retrieve_k: int | None = None,
) -> tuple[dict, list[QueryResult]]:
    """
    Ejecuta un retriever sobre un conjunto de consultas y agrega las metricas.

    - retriever   : objeto con .search(query_tokens, top_k) -> [(doc_id, score)]
    - queries     : lista de dicts {"qid","query","relevant_ids"}
    - preprocess_fn: funcion texto -> lista de lemas (la MISMA que para los docs)
    - ks          : valores de K para Recall@K
    - retrieve_k  : cuantos resultados pedir (por defecto, max(ks))

    Devuelve (resumen_agregado, lista_de_QueryResult).
    """
    top_k = retrieve_k or max(ks)
    per_query: list[QueryResult] = []

    for q in queries:
        rel = set(q["relevant_ids"])
        q_tokens = preprocess_fn(q["query"])
        ranked = [doc_id for doc_id, _ in retriever.search(q_tokens, top_k)]
        flags = relevance_flags(ranked, rel)

        first_rank = next((i for i, f in enumerate(flags, start=1) if f), None)
        per_query.append(
            QueryResult(
                qid=q["qid"],
                query=q["query"],
                relevant_ids=list(rel),
                ranked_ids=ranked,
                first_relevant_rank=first_rank,
                rr=reciprocal_rank(flags),
                recall={k: recall_at_k(flags, len(rel), k) for k in ks},
            )
        )

    n = len(per_query) or 1
    summary = {
        "n_queries": len(per_query),
        "MRR": round(sum(r.rr for r in per_query) / n, 4),
        **{
            f"Recall@{k}": round(sum(r.recall[k] for r in per_query) / n, 4)
            for k in ks
        },
    }
    return summary, per_query


def failure_analysis(
    results_by_method: dict[str, list[QueryResult]],
    k: int = 10,
) -> list[dict]:
    """
    Consultas en las que TODOS los metodos fallan (el relevante no entra en top-K).
    Devuelve una lista de dicts para inspeccion cualitativa (enunciado: "Analizad
    las consultas en las que fallan ambos metodos").
    """
    methods = list(results_by_method.keys())
    by_qid = {m: {r.qid: r for r in res} for m, res in results_by_method.items()}
    qids = [r.qid for r in next(iter(results_by_method.values()))]

    failures = []
    for qid in qids:
        ranks = {m: by_qid[m][qid].first_relevant_rank for m in methods}
        all_fail = all(rank is None or rank > k for rank in ranks.values())
        if all_fail:
            sample = by_qid[methods[0]][qid]
            failures.append(
                {
                    "qid": qid,
                    "query": sample.query,
                    "relevant_ids": sample.relevant_ids,
                    "first_relevant_rank": ranks,
                }
            )
    return failures
