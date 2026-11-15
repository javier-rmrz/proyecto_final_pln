"""
Baselines de recuperacion DISPERSA (lexica) para el Hito 1:

  1. TF-IDF + similitud coseno   (scikit-learn)
  2. BM25 (Okapi)                (rank_bm25)

Ambos reciben documentos y consultas YA preprocesados (listas de lemas) por
`src.preprocess`, garantizando que consulta y documento se tratan igual.

Filtrado por frecuencia documental: se construye un vocabulario filtrado con
min_df / max_df sobre el corpus, y tanto documentos como consultas se restringen
a ese vocabulario (las palabras fuera de vocabulario -OOV- se descartan). Esto
cubre el requisito "filtrado por frecuencia documental" del enunciado y mantiene
coherentes los dos baselines.
"""

from __future__ import annotations

from collections import Counter


# --------------------------------------------------------------------------
# Vocabulario por frecuencia documental
# --------------------------------------------------------------------------

def document_frequencies(corpus_tokens: list[list[str]]) -> Counter:
    """Numero de documentos en los que aparece cada termino (document frequency)."""
    df: Counter = Counter()
    for toks in corpus_tokens:
        for term in set(toks):
            df[term] += 1
    return df


def build_vocabulary(
    corpus_tokens: list[list[str]],
    min_df: int = 2,
    max_df_ratio: float = 0.5,
) -> set[str]:
    """
    Vocabulario que descarta terminos demasiado raros (df < min_df) y demasiado
    comunes (df > max_df_ratio * n_docs). Devuelve el conjunto de terminos validos.
    """
    n_docs = len(corpus_tokens)
    max_df = max_df_ratio * n_docs
    df = document_frequencies(corpus_tokens)
    return {t for t, c in df.items() if c >= min_df and c <= max_df}


def apply_vocabulary(tokens: list[str], vocab: set[str]) -> list[str]:
    """Filtra una lista de lemas dejando solo los que estan en el vocabulario."""
    return [t for t in tokens if t in vocab]


# --------------------------------------------------------------------------
# Baseline 1: TF-IDF + coseno
# --------------------------------------------------------------------------

class TfidfRetriever:
    """
    TF-IDF con similitud coseno. Internamente usa TfidfVectorizer de scikit-learn
    sobre tokens ya preprocesados (se unen con espacios; el vectorizador no vuelve
    a tokenizar de forma destructiva porque ya son lemas limpios).
    """

    def __init__(self, doc_ids: list[str]):
        self.doc_ids = doc_ids
        self.vectorizer = None
        self.doc_matrix = None

    def fit(self, corpus_tokens: list[list[str]]) -> "TfidfRetriever":
        from sklearn.feature_extraction.text import TfidfVectorizer

        joined = [" ".join(toks) for toks in corpus_tokens]
        # token_pattern simple: cualquier secuencia de caracteres no-espacio.
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"[^\s]+",
            lowercase=False,  # ya vienen en minuscula
            norm="l2",
            sublinear_tf=True,
        )
        self.doc_matrix = self.vectorizer.fit_transform(joined)
        return self

    def search(self, query_tokens: list[str], top_k: int) -> list[tuple[str, float]]:
        from sklearn.metrics.pairwise import cosine_similarity

        q_vec = self.vectorizer.transform([" ".join(query_tokens)])
        sims = cosine_similarity(q_vec, self.doc_matrix)[0]
        order = sims.argsort()[::-1][:top_k]
        return [(self.doc_ids[i], float(sims[i])) for i in order]


# --------------------------------------------------------------------------
# Baseline 2: BM25 (Okapi)
# --------------------------------------------------------------------------

class BM25Retriever:
    """
    BM25 Okapi (implementacion: paquete `rank_bm25`, clase BM25Okapi).
    Parametros por defecto de la libreria: k1=1.5, b=0.75 (reportalos en el
    MILESTONE). Se pueden ajustar al construir.
    """

    def __init__(self, doc_ids: list[str], k1: float = 1.5, b: float = 0.75):
        self.doc_ids = doc_ids
        self.k1 = k1
        self.b = b
        self.bm25 = None

    def fit(self, corpus_tokens: list[list[str]]) -> "BM25Retriever":
        from rank_bm25 import BM25Okapi

        self.bm25 = BM25Okapi(corpus_tokens, k1=self.k1, b=self.b)
        return self

    def search(self, query_tokens: list[str], top_k: int) -> list[tuple[str, float]]:
        scores = self.bm25.get_scores(query_tokens)
        order = scores.argsort()[::-1][:top_k]
        return [(self.doc_ids[i], float(scores[i])) for i in order]
