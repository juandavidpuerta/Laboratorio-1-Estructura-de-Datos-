# Laboratorio 3 — Búsqueda por ID: Lista Ligada vs BST vs Árbol B+

## 1\. Problema y objetivo

Se tiene una colección de `n` estudiantes (id, nombre, edad, promedio). El objetivo es **medir
experimentalmente el costo de buscar un estudiante por ID** en tres estructuras y **compararlo con su
complejidad teórica**:

|Estructura|Búsqueda (teoría)|
|-|-|
|Lista ligada|O(n)|
|Árbol binario de búsqueda (BST)|O(log n) promedio con datos aleatorios (O(n) en el peor caso)|
|Árbol B+ (orden 3)|O(log n) garantizado|

## 2\. Estructuras y algoritmos

* **Lista ligada** (`ListaLigada`): búsqueda secuencial nodo a nodo.
* **BST** (`ArbolBinario`): se baja izquierda/derecha comparando el ID. Sin balanceo.
* **Árbol B+** (`BPlusTree`, orden 3): los registros están solo en las hojas; los nodos internos guardan
claves guía. Se desciende hasta la hoja y se busca la clave allí. Las hojas están enlazadas.

## 3\. Diseño del experimento

|Aspecto|Decisión|
|-|-|
|Tamaños de entrada|n = 1.000; 5.000; 10.000; 50.000; 100.000 (dos órdenes de magnitud, para ver la tendencia y no un solo punto; 10.000 es el tamaño original del enunciado)|
|Repeticiones|10 por tamaño, cada una con **datos nuevos** (semilla `42 + repetición`)|
|Generación de datos|IDs **únicos** al azar en \[2.000.000; 10.000.000]; nombre, edad (18–25) y promedio (0–5) aleatorios. Los mismos datos, en el mismo orden, se insertan en las tres estructuras|
|Generación de búsquedas|Por repetición: 300 IDs **existentes** (muestra de los datos) y 300 **no existentes** (aleatorios dentro del mismo rango, verificados que no estén). Las tres estructuras reciben exactamente las mismas búsquedas|
|Medición|`time.perf\\\\\\\_counter()` sobre el lote de 300 búsquedas, dividido entre 300 → µs por búsqueda. Se mide el lote y no cada búsqueda para evitar el error de resolución del reloj (las búsquedas en árbol duran \~1–10 µs). Antes de medir: 30 búsquedas de calentamiento, `gc.collect()` y recolector de basura desactivado durante la medición|
|Valores atípicos|Regla de Tukey (1,5·IQR) por cada combinación (estructura, n, tipo). **Se cuentan y se reportan, pero no se eliminan**; por eso se resume con la **mediana** (robusta)|
|Estadísticas|Mediana, media, desviación estándar, Q1, Q3, mínimo, máximo y número de atípicos (en `resultados/resumen.csv`). Las gráficas muestran la mediana con barras de Q1–Q3|

## 4\. Entorno



Sistema operativo: Windows-11-10.0.26200-SP0

Procesador: Intel64 Family 6 Model 186 Stepping 2, GenuineIntel

Núcleos lógicos: 12

Python: 3.13.7 (CPython)

matplotlib: 3.10.7

RAM total: 16 GB



## 5\. Cómo repetir el experimento

```
pip install -r requirements.txt
python experimento.py
```

Tarda unos minutos (la lista ligada con n = 100.000 es la parte lenta). Genera en `resultados/`:
`entorno.txt`, `mediciones.csv` (datos crudos), `resumen.csv`, `fig1\\\\\\\_tiempos.png`, `fig2\\\\\\\_complejidad.png`.
Los parámetros (tamaños, repeticiones, semilla) están al inicio de `experimento.py`.
Recomendación: cerrar otros programas durante la corrida.

## 6\. Resultados

En la carpeta resultados se encuentran también las gráficas además de las tablas de resultados.



!\[Tiempos](resultados/fig1\_tiempos.png)

!\[Complejidad](resultados/fig2\_complejidad.png)



## 7\. Interpretación y comparación con la teoría

* **Lista ligada:** es con diferencia la más lenta y crece de forma aproximadamente lineal con n, como predice O(n).
Con ID no existente tarda cerca del doble que con uno existente, porque recorre toda la lista (con uno
existente recorre en promedio la mitad).
* **BST y B+:** crecen muy despacio con n (compatible con O(log n)). Multiplicar n por 100 aumenta el tiempo
solo unas 4–5 veces, mientras que en la lista aumenta unas 400 veces.
* **BST vs B+:** aquí el BST resultó ligeramente más rápido. No contradice la teoría: ambos son O(log n), y
el B+ de orden 3 hace más trabajo por nivel (listas de claves, búsqueda dentro de la hoja). La ventaja
del B+ aparece cuando los nodos viven en disco y cada nodo es un bloque (menos accesos a disco), cosa que
este experimento, 100 % en memoria RAM, no mide.
* **Figura 2:** el cociente tiempo/complejidad teórica no es exactamente constante: sube con n. Es esperable:
la teoría cuenta operaciones, pero con n grande los nodos no caben en la caché del procesador y cada
acceso es más lento. Por eso el tiempo real crece algo más rápido que la fórmula.

## 8\. Limitaciones

* Python (intérprete) agrega sobrecosto constante; los valores absolutos no son comparables con C/Java.
* Todo corre en RAM; no se mide el efecto de disco.
* El BST no se balancea: con datos ordenados degeneraría a O(n). Aquí los datos son aleatorios.
* Solo se mide búsqueda por ID (no inserción, no rangos, no eliminación).
* Medidas hechas en un solo equipo y con otros procesos en segundo plano posibles.

## 9\. Conclusiones

1. Los resultados respaldan la teoría: la lista es O(n) y los árboles son logarítmicos; con n = 100.000 los
árboles son cientos de veces más rápidos que la lista.
2. La complejidad asintótica predice la forma de la curva, pero no las constantes: el BST ganó al B+ en RAM.
3. La estructura correcta depende del medio: en memoria, BST (balanceado) o B+ son equivalentes en orden de
magnitud; en disco, el B+ es la opción natural.

## 10\. Uso de herramientas de IA



Para este laboratorio utilicé Claude (Anthropic) como herramienta de apoyo. Las implementaciones de la lista ligada y del árbol binario de búsqueda, con sus propias clases de nodos y sin usar las listas nativas de Python, son de mi autoría, al igual que el planteamiento inicial del ejercicio y la primera comparación de tiempos que hice en Colab. En la programación del árbol B+ recibí más apoyo de Claude que en las otras estructuras.



Claude me ayudó en: (1) reorganizar el código del cuaderno de Colab para que corra en Python local, separándolo en un módulo de estructuras y un script de experimento; (2) ampliar el diseño experimental (varios tamaños de entrada, repeticiones, método de medición, tratamiento de valores atípicos y estadísticas); (3) generar el código de los experimentos y de las gráficas; y (4) redactar la primera versión del README.



Revisé el código y los resultados, ejecuté los experimentos en mi equipo y puedo explicar el funcionamiento de las estructuras, el diseño del experimento y la interpretación de los resultados.

