"""
Carga del corpus para el Hito 1.

Formato interno: una lista de documentos, cada uno un dict con al menos:
    {"doc_id": <str>, "text": <str>}

Soporta dos fuentes:
  - JSONL: un documento por linea, con claves "doc_id" y "text"
           (o personalizables con id_key / text_key).
  - Carpeta de .txt: cada fichero es un documento; el doc_id es el nombre
           del fichero sin extension.

Asi puedes apuntar el notebook a VUESTRO corpus real cambiando solo la ruta.
"""

from __future__ import annotations

import json
import pathlib


def load_jsonl(
    path: str | pathlib.Path,
    id_key: str = "doc_id",
    text_key: str = "text",
) -> list[dict]:
    """Carga un corpus desde un fichero JSONL (un documento por linea)."""
    path = pathlib.Path(path)
    docs: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            docs.append(
                {
                    "doc_id": str(obj[id_key]),
                    "text": obj[text_key],
                }
            )
    _check_unique_ids(docs)
    return docs


def load_txt_dir(path: str | pathlib.Path, pattern: str = "*.txt") -> list[dict]:
    """Carga un corpus desde una carpeta de ficheros de texto."""
    path = pathlib.Path(path)
    docs: list[dict] = []
    for fp in sorted(path.glob(pattern)):
        docs.append({"doc_id": fp.stem, "text": fp.read_text(encoding="utf-8")})
    _check_unique_ids(docs)
    return docs


def sample_corpus(docs: list[dict], n: int, seed: int = 11235) -> list[dict]:
    """
    Submuestra n documentos de forma reproducible. Util cuando el corpus es
    muy grande (cientos de miles de documentos) y quieres unos miles para
    el baseline.
    """
    import random

    if n >= len(docs):
        return list(docs)
    rng = random.Random(seed)
    return rng.sample(docs, n)


def _check_unique_ids(docs: list[dict]) -> None:
    ids = [d["doc_id"] for d in docs]
    if len(ids) != len(set(ids)):
        from collections import Counter

        dups = [i for i, c in Counter(ids).items() if c > 1]
        raise ValueError(f"doc_id duplicados en el corpus: {dups[:10]}")
