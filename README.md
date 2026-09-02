# Laboratorio 1 — Matriz de 100.000 × 100.000 en disco

**Estudiante:** Juan David Puerta Palacio
**Curso:** \[NOMBRE DEL CURSO]
**Fecha:** septiembre de 2026

\---

## 1\. El problema

Escribir en disco una matriz de 100.000 × 100.000 y "mostrarla".

La matriz tiene 100.000 × 100.000 = **10¹⁰ elementos** (diez mil millones). La
solución obvia —crear la matriz en memoria y luego guardarla— falla antes de
empezar:

|Representación|Bytes por elemento|Tamaño total|
|-|-|-|
|`float64` (NumPy por defecto)|8|80 GB|
|`int32`|4|40 GB|
|Lista de listas de Python (`int`)|≈ 28 + puntero|> 300 GB|
|**1 byte por elemento (esta solución)**|**1**|**10 GB**|

Ningún computador de escritorio tiene 80 GB de RAM libres, así que
`np.zeros((100000, 100000))` o una lista de listas terminan en `MemoryError` o
congelan el sistema. La matriz solo puede existir **en disco**, y hay que
generarla, escribirla y leerla por partes.

## 2\. Decisiones de diseño

* **Contenido:** dígitos aleatorios del 1 al 9, generados con semilla fija
(reproducible).
* **Un byte por elemento:** cada dígito se guarda como su carácter ASCII
(`'1'`…`'9'`). Es el mínimo para un dígito legible y permite abrir el archivo
con cualquier editor.
* **Formato de archivo con metadatos y filas explícitas:**

```
  100000 100000\\n        <- encabezado: número de filas y de columnas
  8314594118...\\n        <- fila 0: 100.000 dígitos + salto de línea
  7583988484...\\n        <- fila 1
  ...
  ```

  * El encabezado hace que el archivo se describa a sí mismo: el lector no
necesita conocer las dimensiones de antemano.
  * Cada fila termina en `\\n`: las filas quedan separadas explícitamente.
  * Las columnas tienen ancho fijo (1 byte) y su cantidad está declarada en el
encabezado, por lo que no requieren separador. Poner una coma entre
columnas duplicaría el archivo (20 GB) sin añadir información.
* **Tamaño resultante:** `14 + 100.000 × 100.001 = 10.000.100.014 bytes`
(Windows lo muestra como ≈ 9,31 GB porque usa GiB = 1024³).
* **Sin librerías externas:** solo `random`, `os` y `time` de la biblioteca
estándar de Python.

## 3\. Cómo se resuelve cada problema

### 3.1 Consumo excesivo de RAM

La matriz **nunca existe completa en memoria**. `escribir\_matriz.py` genera una
fila (100.000 bytes), la escribe y la descarta; el consumo de RAM es constante
(\~ 100 KB de datos, unas decenas de MB contando el intérprete) sin importar el
tamaño de la matriz.

```python
for i in range(filas):
    crudo = random.randbytes(cols)      # una fila de bytes aleatorios
    digitos = crudo.translate(TABLA)    # -> caracteres '1'..'9'
    f.write(digitos + b"\\n")            # a disco y se libera
```

`leer\_matriz.py` tampoco carga el archivo: salta con `seek()` al byte exacto
que necesita y lee solo eso.

!\[RAM constante durante la escritura](capturas/ram\_administrador.png)

### 3.2 Escritura lenta a disco

Dos causas de lentitud y cómo se evitan:

1. **Bucle de Python por elemento.** Llamar a `random.randint(1, 9)` diez mil
millones de veces cuesta ≈ 1 µs por llamada → **≈ 3 horas** solo generando.
En su lugar se usa `random.randbytes(n)` (genera n bytes de una vez, en C) y
`bytes.translate(TABLA)` (convierte los 256 valores posibles a dígitos con
una tabla de búsqueda, también en C). No hay ningún bucle por elemento.
2. **Escrituras pequeñas o formato de texto con separadores.** Se escribe en
binario, secuencialmente, 100 KB por llamada a `write()`; el sistema
operativo agrupa las escrituras en su caché de disco.

**Resultado medido:** escritura completa en **26.5 segundos** en SSD


### 3.3 Optimización en la manipulación, almacenamiento y lectura

* **Almacenamiento:** 1 byte por elemento; 10 GB frente a 80 GB de la
representación ingenua.
* **Acceso directo en O(1):** como todas las filas miden lo mismo
(`STRIDE = columnas + 1`), la posición en bytes del elemento (i, j) es

```
  posición(i, j) = H + i · STRIDE + j        (H = bytes del encabezado)
  ```

  y `f.seek(posición)` llega a cualquier elemento sin leer lo anterior. Es la
misma organización *row-major* que usan C, NumPy y la memoria RAM, pero
sobre el disco.

* **Patrones de acceso:**

  * elemento: 1 `seek` + 1 `read` de 1 byte;
  * tramo de fila: 1 `seek` + 1 `read` de k bytes (la fila es contigua);
  * tramo de columna: k `seek` + k `read` (los elementos de una columna están
separados `STRIDE` bytes). Si se necesitaran columnas con frecuencia, se
guardaría también la traspuesta.

## 4\. Cómo verificar el contenido del archivo

Ejecutar `leer\_matriz.py` (con `matriz.txt` en la misma carpeta). No es
posible imprimir 10¹⁰ dígitos (a 10.000 caracteres por segundo tardaría 11
días), así que "mostrar" la matriz significa **evidenciar** que está completa
y es accesible:

|Verificación|Qué demuestra|
|-|-|
|Lee `filas` y `cols` del encabezado|El archivo se describe a sí mismo|
|Tamaño real = `H + filas·STRIDE`|Contiene exactamente filas × columnas elementos|
|Esquinas superior izquierda e inferior derecha, y centro|Está lleno de principio a fin|
|Elemento arbitrario `\[73842, 15]`|Acceso directo a cualquier posición|
|Tramo de fila y tramo de columna|Los dos patrones de acceso funcionan|
|Byte tras la fila 12345 es `\\n`|La estructura de filas es real|
|`fila(0)` y `columna(0)` coinciden con la esquina|La fórmula de posición es consistente|



## 5\. Cómo ejecutar

Requisitos: Python 3.9 o superior (por `random.randbytes`), \~10 GB libres en
disco. Sin dependencias externas.

```
python escribir\_matriz.py     # genera matriz.txt  (\~\[XX] s en SSD)
python leer\_matriz.py         # verifica y muestra la matriz  (< 1 s)
```

Para probar en pequeño antes de la corrida completa, cambiar `FILAS` y `COLS`
al inicio de `escribir\_matriz.py` (por ejemplo 1000 × 1000 → 1 MB). El lector
no necesita cambios: toma las dimensiones del encabezado.

## 6\. Archivos del repositorio

|Archivo|Descripción|
|-|-|
|`README.md`|Este documento|
|`escribir\_matriz.py`|Genera `matriz.txt` fila por fila, con encabezado de metadatos|
|`leer\_matriz.py`|Lee los metadatos, verifica el tamaño y muestra elementos, filas, columnas y bloques|
|`.gitignore`|Excluye `matriz.txt` (10 GB) del repositorio|
|`capturas/`|Evidencias de ejecución: tiempos, uso de RAM y salida de la verificación|

`matriz.txt` no se incluye en el repositorio por su tamaño; se regenera con
`escribir\_matriz.py` en menos de un minuto y, gracias a la semilla fija, con
exactamente el mismo contenido.

## 7\. Nota sobre la evolución de la solución

Una primera versión escribía los 10¹⁰ bytes seguidos, sin encabezado ni
separadores. Funcionaba, pero era un **arreglo**, no una matriz: su forma
existía solo en la cabeza del programador. La versión entregada agrega el
encabezado con las dimensiones y el salto de línea al final de cada fila, con
lo que el archivo pasa a ser un formato de matriz autodescriptivo, al estilo
de `.npy` (NumPy) o `.pgm` (imágenes), manteniendo el acceso directo O(1).

