# MILESTONE 1 — Baseline de recuperación

**Grupo:** Samuel Ruiz Valera, Javier Ramírez Zarzoso, Jorge Sabariego Martos, Alejandro Martín Martínez · **Aplicación:** A. Chatbot sobre base de datos documental
**Repositorio:** https://github.com/javier-rmrz/proyecto_final_pln · **Commit del hito:** ⟨hash del commit entregado, tras fusionar en `main`⟩

## Qué se ha hecho
- **Corpus**: Food.com (Kaggle `irkaal/foodcom-recipes-and-reviews`), **10.000** recetas muestreadas
  de forma **estratificada por categoría** (291 categorías) con filtros de coherencia (≥2 pasos,
  instrucciones de longitud mínima, 2–20 ingredientes).
- **Unidad de indexación**: la **receta completa** (título + ingredientes + instrucciones), sin fragmentar,
  y se mantendrá en todo el proyecto. Las recetas son **cortas**: mediana de 109 palabras, p95 de 279 y
  p99 de 424; solo el 1,3 % pasa de 400. Casi todas caben ya en un fragmento de 200–400 palabras, que es
  el tamaño que propone la guía. Partirlas no aportaría nada y separaría ingredientes de instrucciones,
  cuando una consulta *known-item* describe el plato entero. Cada receta es, por tanto, **un único
  fragmento**: la evaluación por fragmentos y por documento coinciden (no hay fragmentos que agrupar ni
  documentos repetidos en el top-K).
- **Preprocesado (spaCy `en_core_web_sm`)**: lematización, filtrado por categoría gramatical
  (NOUN/PROPN/VERB/ADJ/ADV), eliminación de stopwords y de tokens no alfabéticos, y filtrado por
  frecuencia documental (**min_df = 2**, **max_df = 0,5·N**; vocabulario final de 5.842 términos).
  Documentos y consultas pasan por la misma función y el mismo vocabulario.
- **Consultas**: **34** consultas *known-item* en inglés generadas con **`llama3.1:8b`** (Ollama) a partir
  de 35 recetas al azar. El prompt prohíbe copiar el título y la lista de ingredientes.
  **Revisión** (`REVISION_consultas.md`): un cribado automático mide el solape de cada consulta con su
  receta y con su título (`src/review_queries.py`); se descartó 1 consulta y se regeneraron 5. En la
  revisión manual (14 consultas leídas junto a su receta) se **reescribieron a mano 7**: 3 que repetían
  el título, 2 con relleno vago del LLM (*"a specific type of rice"*) y 2 ambiguas (una casi idéntica a
  otra consulta y un *fried rice* que valía para 29 recetas del corpus). Se guardan en `data/queries.jsonl`
  con el formato pedido, incluido el fragmento de origen: `{"qid", "query", "relevant_ids":
  ["recipe_<id>"], "source_chunk": "recipe_<id>_c00"}`. Como cada receta es un único fragmento,
  `source_chunk` siempre es el `c00` de su receta. Lo guardamos para respetar el formato
  `<documento>_<fragmento>` (identificador del documento más uno propio del fragmento) y que los ids
  encajen con la base vectorial del Hito 2. Las métricas se calculan con `relevant_ids`.
- **Baselines**: TF-IDF + coseno (scikit-learn, `sublinear_tf`, norma L2) y BM25
  (`rank_bm25.BM25Okapi`, **k1 = 1,5**, **b = 0,75**).

## Resultados (10.000 recetas, 34 consultas)
| Método          | Recall@5 | Recall@10 | MRR@10 |
|-----------------|:--------:|:---------:|:------:|
| TF-IDF + coseno |  0.529   |  0.529    | 0.417  |
| BM25            |  0.529   |  0.588    | 0.393  |

Con 34 consultas cada acierto vale ~0,03: la diferencia entre ambos métodos (1–2 consultas) no es
concluyente. El MRR se calcula sobre el top-10 recuperado.

## Problemas encontrados y decisiones de diseño
- **Consultas que copiaban el título**: inflaban las métricas (con ellas, Recall@10 era 0,62/0,65).
  Se midió el solape con el título y se reescribieron; los resultados de arriba son los honestos.
- **Vocabulario ubicuo y plantilla**: términos como *add*, *minute*, *salt* y las etiquetas
  *Ingredients/Instructions* aparecen en más de la mitad de las recetas y los elimina `max_df`.
- **Análisis de fallos** (14/34 fallan en ambos métodos; notebook §8): (1) **sinónimos e hiperónimos**,
  la causa principal (*pasta* frente a *fettuccine*, *seafood* frente a *shrimp, clams*, *deviled eggs*
  frente a *stuffed egg halves*); (2) consultas correctas pero **genéricas**, superadas por recetas más
  típicas (*Greek pasta salad*); (3) **lematización inconsistente** de participios en spaCy
  (*grilled* frente a *grill*); (4) términos útiles eliminados por `max_df` (*pepper*). Las causas 1 y 2
  exigen comparar significados y motivan la recuperación densa del Hito 2.

## Siguiente paso (Hito 2)
Recuperación **densa** (sentence embeddings + base de datos vectorial, por decidir entre FAISS, Chroma
o pgvector) con la receta completa como unidad, evaluada con **el mismo `queries.jsonl`**, y primera
evaluación de la **generación** con un LLM de pesos abiertos.

## Uso de herramientas de IA generativa
- **Generación de consultas**: `llama3.1:8b` vía Ollama local (`/api/generate`, temperatura 0,7).
- **Asistente de código**: hemos usado Claude Code como **apoyo en corrección del
  código**, así como en los scripts de generación. También preparó una propuesta razonada de la tercera
  ronda de revisión manual, que el grupo comprobó frente a cada receta antes de firmarla.
