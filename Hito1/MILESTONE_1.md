# MILESTONE 1 — Baseline de recuperación

> Plantilla de **una página** (entregable del Hito 1). Rellena los campos marcados
> con ⟨…⟩ con los datos de **vuestro corpus real** y borra estas notas antes de entregar.
> Entrega: Aula Global (un miembro del grupo) + indicar el **commit** correspondiente.

**Grupo:** Samuel Ruiz Valera, Javier Ramírez Zarzoso, Jorge Sabariego Martos, Alejandro Martín Martínez · **Aplicación:** A. Chatbot sobre base de datos documental
**Repositorio:** https://github.com/javier-rmrz/proyecto_final_pln · **Commit del hito:** ⟨hash⟩

## Qué se ha hecho
- **Corpus**: Food.com (dataset `irkaal/foodcom-recipes-and-reviews`), **10.000** recetas
  muestreadas de forma **estratificada por categoría** para asegurar variedad
  (291 categorías, sin dominio de postres), con filtros de coherencia (≥2 pasos,
  longitud mínima de instrucciones, 2–20 ingredientes).
- **Unidad de indexación**: **receta completa** (título + ingredientes + instrucciones).
  Justificación: son documentos **cortos** (mediana 109 palabras, p95 279, 99 % por
  debajo de 424; solo el 1,3 % supera 400 palabras), por lo que —según la guía— se
  indexan completos en lugar de fragmentar. La evaluación es, por tanto, directamente
  a nivel de documento (un documento = una unidad; sin agrupación de fragmentos).
- **Preprocesado (spaCy)**: lematización, filtrado por categoría gramatical
  (⟨NOUN/PROPN/VERB/ADJ/ADV⟩), eliminación de stopwords y filtrado por frecuencia
  documental (min_df=⟨…⟩, max_df=⟨…⟩). Mismo tratamiento para documentos y consultas.
- **Consultas de evaluación**: **34** consultas *known-item* generadas con el LLM
  **`llama3.1:8b`** (Ollama local; mismo modelo desplegado en la UC3M), en inglés
  (idioma del corpus), guardadas en `queries.jsonl`. El prompt fuerza **paráfrasis**
  (prohíbe copiar el título y los ingredientes exactos); el solape léxico medio
  consulta–documento es ~46 %, no una copia. **Revisión manual** de las 35 generadas
  (ver `REVISION_consultas.md`): 1 descartada por copiar el título y 5 regeneradas por
  rozar la copia; quedan **34 válidas** (≥30). El solape residual se da en recetas
  nombradas por su ingrediente principal (p. ej. *Turkey Meatloaf*), donde nombrar el
  alimento es inevitable para una consulta *known-item*.
- **Baselines**: TF-IDF + similitud coseno (scikit-learn, `sublinear_tf`, norma L2) y
  BM25 (implementación `rank_bm25.BM25Okapi`, **k1=1.5, b=0.75**). Documentos y
  consultas se preprocesan igual (spaCy) y se restringen al mismo vocabulario
  (frecuencia documental: min_df=2, max_df=0.5·N).

## Resultados (corpus real: 10.000 recetas, 34 consultas parafraseadas)
| Método          | Recall@5 | Recall@10 |  MRR  |
|-----------------|:--------:|:---------:|:-----:|
| TF-IDF + coseno |  0.588   |  0.618    | 0.469 |
| BM25            |  0.559   |  0.647    | 0.431 |

## Problemas encontrados y decisiones de diseño
- **Unidad de indexación**: receta completa (documentos cortos; ver arriba).
- **Boilerplate y vocabulario común**: términos ubicuos del dominio culinario
  (`add`, `minute`, `salt`, `heat`…) y las etiquetas de plantilla se neutralizan con el
  filtrado por frecuencia documental (max_df), evitando que dominen la puntuación.
- **Análisis de fallos**: con consultas parafraseadas fallan en ambos métodos 12/34.
  La causa es la **brecha semántica**: la consulta describe el plato con otras palabras
  (p. ej. *"Greek-inspired pasta salad"* para una receta que dice *spaghetti / feta /
  kalamata olives*), y un baseline **léxico** solo puntúa por solape de términos, no por
  significado. Esto fija el techo del baseline y motiva directamente la recuperación
  **densa** (embeddings) del Hito 2, que sí captura sinónimos y paráfrasis.

## Siguiente paso (Hito 2)
Recuperación **densa** (sentence embeddings + base de datos vectorial
⟨pgvector/FAISS/Chroma⟩) evaluada con **el mismo `queries.jsonl`** para comparar con
este baseline, y primera evaluación de la **generación** con un LLM de pesos abiertos.

## Uso de herramientas de IA generativa
- ⟨LLM usado para generar las consultas: modelo y endpoint⟩.
- ⟨Asistentes de código usados y para qué (p. ej. andamiaje del baseline y del notebook)⟩.
