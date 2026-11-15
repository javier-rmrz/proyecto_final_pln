"""
Preprocesado de texto con spaCy para el Hito 1.

Pieza CLAVE del enunciado: "Las consultas deben preprocesarse exactamente igual
que los documentos del corpus". Por eso TODO (documentos y consultas) pasa por la
MISMA funcion `preprocess`.

Pasos (configurables):
  1. Tokenizacion + lematizacion (spaCy).
  2. Filtrado por categoria gramatical (POS): nos quedamos con contenido
     (sustantivos, nombres propios, verbos, adjetivos, adverbios) por defecto.
  3. Eliminacion de stopwords y de tokens no alfabeticos.
  4. (En baselines.py) filtrado por frecuencia documental (min_df / max_df).

Uso:
    from src.preprocess import load_nlp, preprocess
    nlp = load_nlp("en_core_web_sm")
    tokens = preprocess("The quick brown foxes were running", nlp)
"""

from __future__ import annotations

import functools

# POS que se conservan por defecto (contenido semantico).
DEFAULT_KEEP_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}


@functools.lru_cache(maxsize=4)
def load_nlp(model: str = "en_core_web_sm"):
    """
    Carga un modelo de spaCy desactivando componentes que no necesitamos
    (parser y NER) para que el preprocesado sea rapido. El lematizador y el
    tagger (POS) se mantienen.

    Idiomas habituales:
      - Ingles:  "en_core_web_sm"  (python -m spacy download en_core_web_sm)
      - Espanol: "es_core_news_sm" (python -m spacy download es_core_news_sm)
    """
    import spacy

    try:
        nlp = spacy.load(model, disable=["parser", "ner"])
    except OSError as exc:  # modelo no descargado
        raise OSError(
            f"El modelo de spaCy '{model}' no esta instalado. "
            f"Ejecuta:  python -m spacy download {model}"
        ) from exc
    return nlp


def preprocess(
    text: str,
    nlp,
    keep_pos: set[str] | None = None,
    min_len: int = 2,
) -> list[str]:
    """
    Convierte un texto en una lista de lemas normalizados.

    - keep_pos: conjunto de etiquetas POS a conservar (None -> DEFAULT_KEEP_POS).
    - min_len : longitud minima del lema (descarta tokens de 1 caracter).

    Devuelve lemas en minusculas. Mismo tratamiento para documentos y consultas.
    """
    keep = keep_pos if keep_pos is not None else DEFAULT_KEEP_POS
    doc = nlp(text)
    tokens: list[str] = []
    for tok in doc:
        if tok.is_stop or tok.is_punct or tok.is_space:
            continue
        if not tok.is_alpha:
            continue
        if tok.pos_ not in keep:
            continue
        lemma = tok.lemma_.lower().strip()
        if len(lemma) >= min_len:
            tokens.append(lemma)
    return tokens


def preprocess_many(texts: list[str], nlp, **kwargs) -> list[list[str]]:
    """
    Preprocesa una lista de textos usando nlp.pipe (mas rapido en lotes).
    Devuelve una lista de listas de lemas, en el mismo orden de entrada.
    """
    keep = kwargs.get("keep_pos") or DEFAULT_KEEP_POS
    min_len = kwargs.get("min_len", 2)
    out: list[list[str]] = []
    for doc in nlp.pipe(texts, batch_size=64):
        toks = [
            tok.lemma_.lower().strip()
            for tok in doc
            if not (tok.is_stop or tok.is_punct or tok.is_space)
            and tok.is_alpha
            and tok.pos_ in keep
            and len(tok.lemma_.strip()) >= min_len
        ]
        out.append(toks)
    return out
