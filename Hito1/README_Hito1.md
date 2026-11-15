# Hito 1 — Baseline de recuperación dispersa (TF-IDF y BM25)

Baseline de recuperación para el Proyecto Final de PLN (Máster en IA Aplicada, UC3M).
Implementa el preprocesado con spaCy, el conjunto de consultas *known-item* y los
baselines **dispersos** (TF-IDF + coseno y BM25), evaluados con **Recall@K y MRR**.

## Estructura

```
Hito1/
├── hito1_baseline.ipynb          Notebook principal (ejecutado, con salidas)
├── src/
│   ├── preprocess.py             Preprocesado spaCy (docs y consultas, mismo tratamiento)
│   ├── corpus.py                 Carga de corpus (JSONL o carpeta de .txt) + muestreo
│   ├── baselines.py              TF-IDF+coseno y BM25 + vocabulario por frecuencia doc.
│   ├── evaluation.py             Recall@K, MRR y análisis de fallos
│   ├── generate_queries.py       Generación de queries.jsonl con un LLM (Ollama/UC3M)
│   └── foodcom.py                Adaptador del dataset Food.com -> corpus.jsonl
├── data/
│   ├── corpus_foodcom.jsonl      Corpus: 10.000 recetas (Food.com)
│   ├── queries_foodcom.jsonl     34 consultas known-item (qid, query, relevant_ids, source_chunk)
│   └── queries_foodcom_raw.jsonl Consultas con el texto de origen (para la revisión manual)
├── requirements_hito1.txt
├── MILESTONE_1.md                Entregable de una página
└── REVISION_consultas.md         Revisión manual de las consultas
```

## Instalación

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements_hito1.txt
python -m spacy download en_core_web_sm
```

## Ejecución

Abre `hito1_baseline.ipynb` en Jupyter o VS Code y ejecuta `Kernel > Restart & Run All`.
El notebook carga el corpus y las consultas de `data/`, construye los dos baselines y
muestra las métricas (Recall@5, Recall@10 y MRR) y el análisis de fallos.

## Resultados (Food.com, 10.000 recetas, 34 consultas)

| Método          | Recall@5 | Recall@10 |  MRR  |
|-----------------|:--------:|:---------:|:-----:|
| TF-IDF + coseno |  0.588   |  0.618    | 0.469 |
| BM25            |  0.559   |  0.647    | 0.431 |

Consultas generadas con `llama3.1:8b` en inglés y **parafraseadas** (el prompt prohíbe
copiar el título y los ingredientes; solape léxico medio ~46 %), tras revisión manual
(1 descartada, 5 regeneradas; ver `REVISION_consultas.md`). Varias consultas fallan en
ambos métodos por **brecha semántica** (la consulta describe el plato con otras palabras),
que un baseline léxico no puede salvar: ese es el techo que el RAG denso del Hito 2 debe superar.

## Reproducir el corpus y las consultas

**Corpus** (el dataset no se versiona; descárgalo de Kaggle, `irkaal/foodcom-recipes-and-reviews`):

```powershell
python -m src.foodcom --input C:\ruta\recipes.parquet --output data\corpus_foodcom.jsonl --n 10000
```

Cada receta es un documento (`doc_id="recipe_<id>"`, texto = título + ingredientes +
instrucciones), con muestreo estratificado por categoría y filtros de coherencia.

**Consultas**: en el notebook, pon `RUN_LLM = True` en la celda §5.b y configura el
endpoint del LLM (Ollama local o el servidor UC3M con `X-API-KEY`). Genera ~35, revisa
≥10 a mano descartando las triviales/ambiguas o que copien el texto, y documéntalo en
`MILESTONE_1.md`.

## Decisiones de diseño

- **Unidad de indexación**: receta completa (documentos cortos: mediana 109 palabras,
  99 % por debajo de 424), por lo que la evaluación es directamente a nivel de documento.
- **Preprocesado idéntico** para documentos y consultas (spaCy: lematización, filtrado
  POS, stopwords) y **filtrado por frecuencia documental** (min_df=2, max_df=0.5·N).
- **BM25**: implementación `rank_bm25.BM25Okapi`, k1=1.5, b=0.75.
