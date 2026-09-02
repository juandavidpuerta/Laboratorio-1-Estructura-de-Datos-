"""
leer_matriz.py
==============
Lee y verifica la matriz generada por escribir_matriz.py SIN cargarla en RAM.

Idea central
------------
El archivo tiene un encabezado seguido de FILAS líneas de exactamente
COLS + 1 bytes (COLS dígitos + '\n'). Como todas las filas miden lo mismo,
la posición en bytes del elemento (i, j) se calcula con una fórmula:

    posicion(i, j) = H + i * STRIDE + j

    H      = longitud del encabezado en bytes
    STRIDE = COLS + 1   (una fila completa, incluido su '\n')

Con f.seek(posicion) el cursor salta directamente a ese byte sin leer nada
de lo anterior. El acceso a cualquier elemento cuesta lo mismo, esté al
inicio o al final de los 10 GB: acceso aleatorio en O(1).

Patrones de acceso
------------------
- Elemento (i, j):  1 seek + 1 read de 1 byte.
- Tramo de fila:    1 seek + 1 read de k bytes (la fila es contigua en disco).
- Tramo de columna: k seeks + k reads (los elementos de una columna están
                    separados STRIDE bytes entre sí; no son contiguos).

Verificaciones que realiza este script
--------------------------------------
1. Lee los metadatos del encabezado (no usa ninguna dimensión escrita a mano).
2. Comprueba que el tamaño real del archivo coincide con H + FILAS*STRIDE.
3. Muestra las esquinas y el centro (prueba que el archivo está lleno).
4. Lee un elemento arbitrario, un tramo de fila y un tramo de columna.
5. Comprueba que el byte que sigue a una fila es '\n' (estructura de filas).
6. Verificaciones cruzadas: la fila 0 y la columna 0 leídas con las
   funciones fila() y columna() deben coincidir con la esquina superior
   izquierda leída con submatriz().

Ejecución
---------
    python leer_matriz.py       (con matriz.txt en la misma carpeta)
"""

import os

RUTA = "matriz.txt"


# ----------------------------------------------------------------------------
# Apertura y lectura de metadatos
# ----------------------------------------------------------------------------
def abrir(ruta: str):
    """
    Abre el archivo, lee el encabezado y devuelve (f, filas, cols, H, stride).

    - f      : archivo abierto en modo binario, con el cursor tras el encabezado
    - filas  : número de filas (leído del encabezado)
    - cols   : número de columnas (leído del encabezado)
    - H      : bytes que ocupa el encabezado
    - stride : bytes que ocupa una fila completa (cols + 1 por el '\\n')
    """
    f = open(ruta, "rb")
    encabezado = f.readline()                    # lee hasta el primer '\n'
    filas, cols = map(int, encabezado.split())   # b"100000 100000\n" -> 100000, 100000
    return f, filas, cols, len(encabezado), cols + 1


# ----------------------------------------------------------------------------
# Funciones de acceso
# ----------------------------------------------------------------------------
def elemento(f, H, stride, i, j):
    """Devuelve el dígito en la fila i, columna j."""
    f.seek(H + i * stride + j)           # salto directo al byte
    return f.read(1).decode()            # b'3' -> '3'


def fila(f, H, stride, cols, i, desde=0, cuantos=20):
    """Devuelve `cuantos` dígitos de la fila i a partir de la columna `desde`."""
    cuantos = min(cuantos, cols - desde)         # no pasarse del final de la fila
    f.seek(H + i * stride + desde)               # inicio del tramo
    return " ".join(f.read(cuantos).decode())    # una sola lectura: la fila es contigua


def columna(f, H, stride, filas, j, desde=0, cuantos=20):
    """Devuelve `cuantos` dígitos de la columna j a partir de la fila `desde`."""
    cuantos = min(cuantos, filas - desde)
    valores = []
    for i in range(desde, desde + cuantos):
        f.seek(H + i * stride + j)               # un salto por cada fila
        valores.append(f.read(1).decode())
    return " ".join(valores)


def submatriz(f, H, stride, i0, j0, alto, ancho):
    """Devuelve como texto el bloque de `alto` x `ancho` que empieza en (i0, j0)."""
    lineas = []
    for i in range(i0, i0 + alto):
        f.seek(H + i * stride + j0)
        lineas.append(" ".join(f.read(ancho).decode()))
    return "\n".join(lineas)


# ----------------------------------------------------------------------------
# Programa principal: verificación
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    f, FILAS, COLS, H, STRIDE = abrir(RUTA)

    print("=== 1. Metadatos leídos del encabezado ===")
    print(f"filas = {FILAS}, columnas = {COLS}")
    print(f"encabezado = {H} bytes, cada fila = {STRIDE} bytes (columnas + '\\n')")

    print("\n=== 2. Tamaño del archivo ===")
    real = os.path.getsize(RUTA)
    esperado = H + FILAS * STRIDE
    print(f"real:     {real:,} bytes")
    print(f"esperado: {esperado:,} bytes  ->", "OK" if real == esperado else "ERROR")

    print("\n=== 3. Esquinas y centro ===")
    print("Esquina superior izquierda (10x10):")
    esquina = submatriz(f, H, STRIDE, 0, 0, 10, 10)
    print(esquina)
    print("\nEsquina inferior derecha (10x10):")
    print(submatriz(f, H, STRIDE, FILAS - 10, COLS - 10, 10, 10))
    print("\nCentro (5x5):")
    print(submatriz(f, H, STRIDE, FILAS // 2, COLS // 2, 5, 5))

    print("\n=== 4. Accesos puntuales ===")
    i, j = 73842, 15
    print(f"elemento [{i}, {j}] = {elemento(f, H, STRIDE, i, j)}"
          f"   (byte {H + i * STRIDE + j:,})")
    print(f"fila 50000, columnas 300..309:  {fila(f, H, STRIDE, COLS, 50_000, 300, 10)}")
    print(f"columna 15, filas 73840..73844: {columna(f, H, STRIDE, FILAS, 15, 73_840, 5)}")
    print("  (el tercer valor de esa columna debe ser el elemento [73842, 15])")

    print("\n=== 5. Estructura de filas ===")
    f.seek(H + 12345 * STRIDE + COLS)            # byte justo después de la fila 12345
    byte_final = f.read(1)
    print(f"byte al final de la fila 12345: {byte_final}  ->",
          "OK (salto de línea)" if byte_final == b"\n" else "ERROR")

    print("\n=== 6. Verificaciones cruzadas ===")
    primera_linea = esquina.split("\n")[0]
    primera_col = " ".join(l.split()[0] for l in esquina.split("\n"))
    ok_fila = fila(f, H, STRIDE, COLS, 0, 0, 10) == primera_linea
    ok_col = columna(f, H, STRIDE, FILAS, 0, 0, 10) == primera_col
    print("fila(0)    coincide con la 1ª línea de la esquina:  ", "OK" if ok_fila else "ERROR")
    print("columna(0) coincide con la 1ª columna de la esquina:", "OK" if ok_col else "ERROR")

    f.close()
