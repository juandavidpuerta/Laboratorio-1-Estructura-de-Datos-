"""
escribir_matriz.py
==================
Genera en disco una matriz de FILAS x COLS con dígitos aleatorios del 1 al 9,
sin cargar nunca la matriz completa en memoria RAM.

Formato del archivo generado (matriz.txt)
-----------------------------------------
    100000 100000\n          <- encabezado: metadatos (filas y columnas)
    8314594118...\n          <- fila 0: COLS dígitos + salto de línea
    7583988484...\n          <- fila 1
    ...

- Cada elemento ocupa exactamente 1 byte (el carácter ASCII del dígito).
- Cada fila termina en '\n', lo que separa explícitamente una fila de otra.
- Las columnas tienen ancho fijo (1 byte) y su cantidad está declarada en el
  encabezado, por lo que no se necesita separador entre ellas.

Tamaño resultante: len(encabezado) + FILAS * (COLS + 1) bytes
                   = 14 + 100.000 * 100.001 = 10.000.100.014 bytes (~9,3 GiB)

Cómo resuelve los tres problemas del laboratorio
------------------------------------------------
1. Consumo excesivo de RAM: se genera y escribe UNA fila a la vez (100 KB).
   La matriz nunca existe completa en memoria; solo existe en disco.
2. Escritura lenta a disco: los dígitos se generan con random.randbytes()
   (implementado en C) y se convierten a caracteres '1'..'9' con
   bytes.translate() (también en C). No hay bucle de Python por elemento.
   Un bucle con random.randint() por elemento tardaría ~3 horas; esta
   versión tarda menos de un minuto en SSD.
3. Optimización de almacenamiento: 1 byte por elemento (el mínimo para un
   dígito legible). Guardarlo como texto con comas duplicaría el tamaño.

Ejecución
---------
    python escribir_matriz.py

Requiere Python 3.9+ (por random.randbytes) y ~10 GB libres en disco.
Para probar en pequeño, cambiar FILAS y COLS (p. ej. 1000 x 1000 = 1 MB).
"""

import os
import random
import time

# ----------------------------------------------------------------------------
# Parámetros
# ----------------------------------------------------------------------------
FILAS = 100_000          # número de filas de la matriz
COLS = 100_000           # número de columnas de la matriz
RUTA = "matriz.txt"      # archivo de salida (se crea junto a este script)
SEMILLA = 2026           # semilla para que el resultado sea reproducible

# ----------------------------------------------------------------------------
# Tabla de traducción byte -> dígito ASCII
# ----------------------------------------------------------------------------
# random.randbytes() entrega bytes con valores 0..255. Queremos convertir cada
# uno en un carácter '1'..'9'. bytes.translate() necesita una tabla de 256
# posiciones donde la posición b contiene el byte de salida para la entrada b:
#
#     salida(b) = (b mod 9) + 1  -> un número entre 1 y 9
#     + ord('0')                 -> lo convierte en el código ASCII del dígito
#
# Ejemplo: b = 200 -> 200 mod 9 = 2 -> 2 + 1 = 3 -> '3' (ASCII 51)
TABLA = bytes((b % 9) + 1 + ord('0') for b in range(256))


def escribir_matriz(ruta: str, filas: int, cols: int) -> int:
    """
    Escribe la matriz en `ruta` y devuelve el tamaño esperado en bytes.

    La escritura es secuencial y por filas: en cada iteración se genera una
    fila de `cols` dígitos, se le agrega '\\n' y se escribe. El uso de RAM es
    constante (~ cols bytes) sin importar el tamaño de la matriz.
    """
    random.seed(SEMILLA)
    inicio = time.time()

    with open(ruta, "wb") as f:
        # --- Encabezado con los metadatos ---------------------------------
        # Ejemplo: b"100000 100000\n". Es la primera línea del archivo y es
        # lo que permite a cualquier lector conocer la forma de la matriz.
        encabezado = f"{filas} {cols}\n".encode()
        f.write(encabezado)

        # --- Cuerpo: una fila por iteración -------------------------------
        for i in range(filas):
            crudo = random.randbytes(cols)          # cols bytes aleatorios 0..255
            digitos = crudo.translate(TABLA)        # -> cols caracteres '1'..'9'
            f.write(digitos + b"\n")                # fila + separador de fila

            if i % 10_000 == 0:
                print(f"fila {i:>7} / {filas}   ({time.time() - inicio:.0f} s)")

    print(f"Escritura terminada en {time.time() - inicio:.1f} s")
    return len(encabezado) + filas * (cols + 1)


if __name__ == "__main__":
    esperado = escribir_matriz(RUTA, FILAS, COLS)
    real = os.path.getsize(RUTA)

    print()
    print(f"Archivo:          {os.path.abspath(RUTA)}")
    print(f"Tamaño real:      {real:,} bytes")
    print(f"Tamaño esperado:  {esperado:,} bytes")
    print("Verificación:    ", "OK" if real == esperado else "ERROR: tamaños no coinciden")
