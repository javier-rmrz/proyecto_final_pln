# Hito 1 — Baseline de recuperación dispersa (TF-IDF y BM25)

Baseline de recuperación para el Proyecto Final de PLN (Máster en IA Aplicada, UC3M).
Implementa el preprocesado con spaCy, el conjunto de consultas *known-item* y los
baselines **dispersos** (TF-IDF + coseno y BM25), evaluados con **Recall@K y MRR@10**.

## Estructura

```
Hito1/
├── hito1_baseline.ipynb          Notebook principal (ejecutado, con salidas)
├── src/
│   ├── preprocess.py             Preprocesado spaCy (docs y consultas, mismo tratamiento)
│   ├── corpus.py                 Carga de corpus (JSONL o carpeta de .txt) + muestreo
│   ├── baselines.py              TF-IDF+coseno y BM25 + vocabulario por frecuencia doc.
│   ├── evaluation.py             Recall@K, MRR@10 y análisis de fallos por consulta
│   ├── generate_queries.py       Generación de queries.jsonl con un LLM (Ollama/UC3M)
│   ├── review_queries.py         Cribado de apoyo a la revisión (solape con receta y título)
│   └── foodcom.py                Adaptador del dataset Food.com -> corpus.jsonl
├── data/
│   ├── corpus_foodcom.jsonl      Corpus: 10.000 recetas (Food.com)
│   ├── queries.jsonl             34 consultas known-item (qid, query, relevant_ids)
│   └── queries_raw.jsonl         Las 35 consultas originales del LLM, con el texto de origen
├── requirements_hito1.txt
├── MILESTONE_1.md                Entregable de una página
└── REVISION_consultas.md         Revisión manual de las consultas e historial de cambios
```

## Instalación

Usad Python 3.12 o 3.13: spaCy aún no funciona bien con Python 3.14.

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements_hito1.txt
python -m spacy download en_core_web_sm
```

## Ejecución

Abre `hito1_baseline.ipynb` en Jupyter o VS Code y ejecuta `Kernel > Restart & Run All`.
El notebook carga el corpus y las consultas de `data/`, construye los dos baselines y
muestra las métricas (Recall@5, Recall@10 y MRR@10) y el análisis de fallos.

## Resultados (Food.com, 10.000 recetas, 34 consultas)

| Método          | Recall@5 | Recall@10 | MRR@10 |
|-----------------|:--------:|:---------:|:------:|
| TF-IDF + coseno |  0.529   |  0.529    | 0.417  |
| BM25            |  0.529   |  0.588    | 0.393  |

Consultas generadas con `llama3.1:8b` en inglés y **parafraseadas** (el prompt prohíbe
copiar el título y los ingredientes; solape léxico medio con la receta ~42 %). Revisión en
`REVISION_consultas.md`: 1 descartada, 5 regeneradas y 7 reescritas a mano (3 repetían el
título, 2 tenían relleno vago y 2 eran ambiguas); 14 consultas revisadas a mano en total. 14 de 34 consultas fallan en ambos métodos, sobre todo por **sinónimos** (la
consulta describe el plato con otras palabras), que un baseline léxico no puede salvar:
ese es el techo que el RAG denso del Hito 2 debe superar.

## Reproducir el corpus y las consultas

**Corpus** (el dataset no se versiona; descárgalo de Kaggle, `irkaal/foodcom-recipes-and-reviews`):

```powershell
python -m src.foodcom --input C:\ruta\recipes.parquet --output data\corpus_foodcom.jsonl --n 10000
```

Cada receta es un documento (`doc_id="recipe_<id>"`, texto = título + ingredientes +
instrucciones), con muestreo estratificado por categoría y filtros de coherencia.

**Consultas**: en el notebook, pon `RUN_LLM = True` en la celda §5.b y configura el
endpoint del LLM (Ollama local o el servidor UC3M con `X-API-KEY`). Genera ~35, pasa el
cribado de apoyo (`python -m src.review_queries`), revisa ≥10 a mano descartando las
triviales/ambiguas o que copien el texto, y documéntalo en `REVISION_consultas.md`.

## Decisiones de diseño

- **Unidad de indexación**: receta completa (documentos cortos: mediana 109 palabras,
  99 % por debajo de 424), por lo que la evaluación es directamente a nivel de documento.
- **Preprocesado idéntico** para documentos y consultas (spaCy: lematización, filtrado
  POS, stopwords) y **filtrado por frecuencia documental** (min_df=2, max_df=0.5·N).
- **BM25**: implementación `rank_bm25.BM25Okapi`, k1=1.5, b=0.75.
