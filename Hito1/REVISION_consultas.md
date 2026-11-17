# Revisión de las consultas de evaluación (Hito 1)

Registro de cómo se generaron, criban y revisan las consultas *known-item* de `data/queries_foodcom.jsonl`. El enunciado pide revisar **a mano al menos 10** consultas, descartando las triviales o ambiguas, y documentarlo.

## Proceso

1. **Generación.** 35 recetas elegidas al azar (`seed=11235`); para cada una, `llama3.1:8b` (Ollama) escribe una consulta en inglés con el prompt de `src/generate_queries.py`, que prohíbe copiar el título y la lista de ingredientes. Originales: `data/queries_foodcom_raw.jsonl`.
2. **Cribado automático** (`python -m src.review_queries`). Para cada consulta mide el **solape** (% de sus palabras, sin stopwords ni *recipe*, que aparecen en la receta) y el **título** (% de las palabras del título que repite) y sugiere un veredicto. Es solo una ayuda: la decisión es de la persona que revisa.
3. **Primera ronda.** Se descartó la q20 original (*Roasted winter squash…*, casi copia del título) y se regeneraron 5 (q06, q09, q12, q13 y la q21 original). Al quitar la q20, las consultas siguientes se **renumeraron** (la q21 original es ahora la q20, etc.; ver historial).
4. **Segunda ronda (17/11/2026).** Al medir también el solape con el título aparecieron 3 consultas que repetían el título entero y el primer cribado no detectaba (q15, q24, q25): se **reescribieron a mano**. La q20 (*turkey meatloaf*) se mantiene de forma justificada. Además, el motivo con el que se marcó la q12 (*"una sopa no se cuece al vapor"*) era erróneo: la receta sí cuece al vapor.

**Resultado:** 34 consultas válidas (≥30).

## Cómo completar la revisión manual

Cada revisor lee la consulta **junto a su receta** (búscala por `doc_id` en `data/corpus_foodcom.jsonl`) y escribe en **Revisión manual** su decisión (*OK*, *Reescribir* o *Descartar*), su nombre y, si no es OK, el motivo. Se exige revisar **al menos 10**; las marcadas *REVISAR* tienen prioridad. Si se reescribe o descarta alguna, hay que actualizar `data/queries_foodcom.jsonl` y re-ejecutar el notebook.

## Consultas finales (34)

| qid | Consulta | Receta de origen (título) | Solape | Título | Sugerido | Nota | Revisión manual |
|-----|----------|---------------------------|:------:|:------:|----------|------|-----------------|
| q01 | Coconut based no bake energy bars with flax seed and dark chocolate topping | Power Bars | 60% | 50% | MANTENER |  |  |
| q02 | Fried Jewish fish patties made with ground fish and matzo meal, served on a bed of greens. | fried gefilte fish | 64% | 67% | MANTENER |  |  |
| q03 | Grilled Middle Eastern style chicken kebabs with vegetables marinating in a spicy citrus sauce | Shish Taouk - Chicken Kebabs | 27% | 50% | MANTENER |  |  |
| q04 | Creamy sauce with pasta and sautéed vegetables baked with extra cheese topping | Cream Cheese Sauce | 30% | 67% | MANTENER |  |  |
| q05 | Greek-inspired pasta salad with a tangy cheese and olive twist | Spaghetti With Tomatoes, Black Olives, Garlic, and Feta Cheese | 38% | 14% | MANTENER |  |  |
| q06 | Roasted garlic potato recipe with rosemary that's perfect for a weeknight dinner | Roasted Red Potatoes | 38% | 33% | MANTENER |  |  |
| q07 | Beef and mushroom dish with creamy sauce served over a specific type of rice. | My Dad's Beef Stroganoff | 22% | 25% | MANTENER |  |  |
| q08 | Boiled egg salad sandwich recipe with creamy dressing and fresh dill | Egg Sandwich | 50% | 100% | MANTENER |  |  |
| q09 | Blackened fish recipe with Creole seasoning and compound butter for a Cajun-style dinner. | Blackened Catfish - Claire Robinson | 67% | 25% | MANTENER |  |  |
| q10 | baked puff pastry cups filled with creamy asparagus and chicken mixture | Chicken and Asparagus Vol-Au-Vents | 22% | 40% | MANTENER |  |  |
| q11 | bundt pan macaroni and cheese with crispy breadcrumb topping and cheesy sauce | Mac & Cheese Ring | 56% | 33% | MANTENER |  |  |
| q12 | Steamed vegetable puree soup with saffron and minimal dairy for a light meal option | Healthy Carrot Soup | 40% | 33% | MANTENER | *Steamed* es correcto: la receta cuece las zanahorias al vapor. |  |
| q13 | Smooth blended tropical drink with banana and fruit juices for summer. | Paradise Freeze | 25% | 0% | MANTENER |  |  |
| q14 | Greek pasta salad with tangy dressing and crumbled white cheese. | Greek Orzo Salad | 50% | 67% | MANTENER |  |  |
| q15 | Island-style stuffed egg halves with a creamy, peppery yolk mix | Caribbean Deviled Eggs | 22% | 0% | MANTENER |  | **Reescrita** (Alejandro). Original: *Caribbean deviled eggs with a thick spicy filling recipe* (copiaba el título). |
| q16 | Warm dessert with bananas and pineapple topped with coconut and chocolate sauce | Banana Split Dump Cake | 62% | 0% | MANTENER |  |  |
| q17 | New Orleans style cheesy potato casserole with crispy bacon and sour cream topping | New Orleans Potatoes | 55% | 67% | MANTENER |  |  |
| q18 | Homemade spice blend recipe for traditional East African red pepper sauce mix. | Eritrean Berbere (Red Pepper Spice Mixture) | 40% | 50% | MANTENER |  |  |
| q19 | baked fish with lemon and herbs in a light margarine sauce | Lemon Basil Orange Roughy | 43% | 25% | MANTENER |  |  |
| q20 | Ground turkey meatloaf with Mediterranean herbs and pine nuts recipe | Tempting Turkey Meatloaf | 71% | 67% | REVISAR | Solape alto con el texto de la receta. | **Mantener** (Alejandro): la receta se llama por su ingrediente principal; nombrar *turkey meatloaf* es inevitable y el resto sí parafrasea. |
| q21 | smoked salmon salad with citrus and herbs for a light winter dinner | Smoked Salmon With Grapefruit Salad | 38% | 75% | REVISAR | Repite casi todo el título. Parafrasea *grapefruit* → *citrus*. |  |
| q22 | Low-calorie Italian pasta dish with creamy sauce and fresh herbs. | Skinny Fettuccine Alfredo | 33% | 0% | MANTENER |  |  |
| q23 | Baked ham glazed with sweet and spicy mixture over an open flame | Bavarian Christmas Ham in the Fireplace | 25% | 25% | MANTENER |  |  |
| q24 | Southern Louisiana style fried organ meat simmered in a sweet tomato and pepper sauce | Beef Liver Creole | 18% | 0% | MANTENER |  | **Reescrita** (Alejandro). Original: *beef liver stew with Creole spices and sweetened tomatoes recipe* (copiaba el título). |
| q25 | White fish fillets baked in a foil parcel with ginger, chili and a soy-citrus dressing | Sea Bass Thai Style | 55% | 0% | MANTENER |  | **Reescrita** (Alejandro). Original: *Thai style baked sea bass in foil with spicy Asian marinade recipe* (copiaba el título). |
| q26 | Coconut and pineapple sweet bread recipe with coffee flavors and warm spices | Coconut Pineapple Coffee Batter Bread/Cake | 62% | 67% | MANTENER |  |  |
| q27 | Sweet breakfast muffins with warm spices and crunchy cinnamon topping baked in individual cups | Cinnamon Muffins | 45% | 100% | MANTENER |  |  |
| q28 | Jamaican-style spice rub for grilled pork or chicken, includes sweet and smoky flavors | Bryan's Jerk Rub: Jamiacan Style | 36% | 33% | MANTENER |  |  |
| q29 | Meatball soup recipe for a crowd, slow cooker method, freezer-friendly, comforting. | OAMC Crockpot Meatball Vegetable Soup | 33% | 40% | MANTENER |  |  |
| q30 | Cheesy beef casserole recipe with taco flavors and crunchy topping. | Nacho Casserole | 29% | 50% | MANTENER |  |  |
| q31 | Stuffed winter squash recipe with quinoa and sweet flavors, vegetarian option. | Quinoa Stuffed Kabocha Squash | 38% | 75% | REVISAR | Repite casi todo el título. Parafrasea *kabocha* → *winter squash*. |  |
| q32 | chewy chocolate chip cookies with coffee flavor baked in a specific way | The Real Neiman Marcus Chocolate Chip Cookie Recipe | 56% | 33% | MANTENER |  |  |
| q33 | Chinese-style fried rice dish with vegetables and egg, using a wok and stir-fry method. | Fried Rice W/ Vegetables | 55% | 75% | REVISAR | Repite casi todo el título. Título corto y genérico (*Fried Rice W/ Vegetables*). |  |
| q34 | Paella inspired pasta dish with seafood and cheese casserole method | Pantry Paella Style Shells and Cheese | 25% | 40% | MANTENER |  |  |

## Historial de cambios respecto a las 35 originales

| Original | Final | Cambio | Consulta original | Solape orig. | Consulta final |
|----------|-------|--------|-------------------|:------------:|----------------|
| q06 | q06 | Regenerada (1ª ronda) | Roasted garlic potatoes with rosemary recipe for side dish | 80% | Roasted garlic potato recipe with rosemary that's perfect for a weeknight dinner |
| q09 | q09 | Regenerada (1ª ronda) | Blackened catfish recipe with spicy butter and lemons, oven-baked with Creole seasoning. | 78% | Blackened fish recipe with Creole seasoning and compound butter for a Cajun-style dinner. |
| q12 | q12 | Regenerada (1ª ronda) | Light and creamy steamed vegetable soup with saffron and milk. | 57% | Steamed vegetable puree soup with saffron and minimal dairy for a light meal option |
| q13 | q13 | Regenerada (1ª ronda) | Smooth tropical cocktail recipe made with frozen fruit and a hint of citrus | 14% | Smooth blended tropical drink with banana and fruit juices for summer. |
| q15 | q15 | Reescrita a mano (2ª ronda) | Caribbean deviled eggs with a thick spicy filling recipe | 67% | Island-style stuffed egg halves with a creamy, peppery yolk mix |
| q20 | — | Descartada | Roasted winter squash recipe with toasted pumpkin seeds and fresh mint | 88% | — |
| q21 | q20 | Regenerada (1ª ronda) | ground turkey meatloaf recipe with Mediterranean flavors and pine nuts | 71% | Ground turkey meatloaf with Mediterranean herbs and pine nuts recipe |
| q25 | q24 | Reescrita a mano (2ª ronda) | beef liver stew with Creole spices and sweetened tomatoes recipe | 57% | Southern Louisiana style fried organ meat simmered in a sweet tomato and pepper sauce |
| q26 | q25 | Reescrita a mano (2ª ronda) | Thai style baked sea bass in foil with spicy Asian marinade recipe | 56% | White fish fillets baked in a foil parcel with ginger, chili and a soy-citrus dressing |

Las consultas no listadas no han cambiado. Numeración: q01–q19 conservan su número; de la q21 a la q35 originales pasan a ser q20–q34.
