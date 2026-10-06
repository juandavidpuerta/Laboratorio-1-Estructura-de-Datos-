# -*- coding: utf-8 -*-
"""
Laboratorio 3 - Experimento: búsqueda por ID en Lista Ligada, BST y Árbol B+.

Uso:  python experimento.py
Salida (carpeta resultados/): entorno.txt, mediciones.csv, resumen.csv,
                              fig1_tiempos.png, fig2_complejidad.png
"""

import csv
import gc
import math
import os
import platform
import random
import statistics
import sys
import time

import matplotlib.pyplot as plt

from estructuras import ArbolBinario, BPlusTree, EstudianteDatosGenerador, ListaLigada

# ---------------------------------------------------------------------------
# Parámetros del experimento (todo lo que hay que reportar en el informe)
# ---------------------------------------------------------------------------
TAMANOS = [1_000, 5_000, 10_000, 50_000, 100_000]   # n = número de estudiantes
REPETICIONES = 10          # repeticiones independientes por tamaño (datos nuevos cada vez)
N_BUSQUEDAS = 300          # búsquedas por tipo y por repetición
ORDEN_BPLUS = 3
ID_MIN, ID_MAX = 2_000_000, 10_000_000
SEMILLA = 42
CARPETA = "resultados"

ESTRUCTURAS = ["Lista Ligada", "Árbol Binario (BST)", "Árbol B+"]
TIPOS = ["existente", "no_existente"]


# ---------------------------------------------------------------------------
# Entorno (hardware y software)
# ---------------------------------------------------------------------------
def describir_entorno():
    lineas = [
        f"Sistema operativo: {platform.platform()}",
        f"Procesador: {platform.processor() or platform.machine()}",
        f"Núcleos lógicos: {os.cpu_count()}",
        f"Python: {sys.version.split()[0]} ({platform.python_implementation()})",
        f"matplotlib: {plt.matplotlib.__version__}",
    ]
    try:  # RAM total (Linux/macOS); en Windows se completa a mano en el README
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
        lineas.append(f"RAM total: {ram:.1f} GB")
    except (ValueError, OSError, AttributeError):
        lineas.append("RAM total: (completar a mano)")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Medición
# ---------------------------------------------------------------------------
def generar_busquedas(estudiantes, n_busquedas):
    """IDs existentes (muestra de los datos) y no existentes (dentro del mismo rango)."""
    existentes = [e[0] for e in random.sample(estudiantes, n_busquedas)]
    presentes = {e[0] for e in estudiantes}
    no_existentes = []
    while len(no_existentes) < n_busquedas:
        candidato = random.randint(ID_MIN, ID_MAX)
        if candidato not in presentes:
            no_existentes.append(candidato)
    return {"existente": existentes, "no_existente": no_existentes}


def medir(estructura, ids):
    """Tiempo promedio por búsqueda (microsegundos) midiendo el lote completo."""
    for id_ in ids[:30]:           # calentamiento (cachés, intérprete)
        estructura.buscar_por_id(id_)
    gc.collect()
    gc.disable()                   # que el recolector de basura no contamine la medición
    inicio = time.perf_counter()
    for id_ in ids:
        estructura.buscar_por_id(id_)
    fin = time.perf_counter()
    gc.enable()
    return (fin - inicio) / len(ids) * 1e6


def correr_experimento():
    filas = []  # (estructura, n, tipo, repeticion, us_por_busqueda)
    for n in TAMANOS:
        for rep in range(REPETICIONES):
            random.seed(SEMILLA + rep)
            estudiantes = EstudianteDatosGenerador.generar_lote(n, ID_MIN, ID_MAX)
            busquedas = generar_busquedas(estudiantes, N_BUSQUEDAS)

            lista, bst, bplus = ListaLigada(), ArbolBinario(), BPlusTree(ORDEN_BPLUS)
            for est in estudiantes:  # mismos datos, mismo orden, en las tres
                lista.insertar_estudiante(*est)
                bst.insertar(*est)
                bplus.insertar(*est)
            estructuras = dict(zip(ESTRUCTURAS, [lista, bst, bplus]))

            for tipo in TIPOS:
                for nombre in ESTRUCTURAS:   # mismas búsquedas para las tres
                    filas.append((nombre, n, tipo, rep, medir(estructuras[nombre], busquedas[tipo])))
        print(f"  n = {n:>7,} listo")
    return filas


# ---------------------------------------------------------------------------
# Estadísticas
# ---------------------------------------------------------------------------
def cuartiles(valores):
    q = statistics.quantiles(valores, n=4, method="inclusive")
    return q[0], q[1], q[2]


def resumir(filas):
    grupos = {}
    for nombre, n, tipo, rep, us in filas:
        grupos.setdefault((nombre, n, tipo), []).append(us)

    resumen = []
    for (nombre, n, tipo), vals in grupos.items():
        q1, mediana, q3 = cuartiles(vals)
        iqr = q3 - q1
        atipicos = [v for v in vals if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr]
        resumen.append({
            "estructura": nombre, "n": n, "tipo": tipo, "repeticiones": len(vals),
            "mediana_us": mediana, "media_us": statistics.mean(vals),
            "desv_est_us": statistics.stdev(vals), "q1_us": q1, "q3_us": q3,
            "min_us": min(vals), "max_us": max(vals), "atipicos": len(atipicos),
        })
    return resumen


# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------
def guardar_csv(ruta, filas, columnas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        w.writerows(filas)


def imprimir_tabla(resumen):
    for tipo in TIPOS:
        print(f"\nBúsqueda de ID {tipo.replace('_', ' ')} - mediana [Q1, Q3] en µs/búsqueda "
              f"(atípicos entre paréntesis)")
        print(f"{'n':>8} | " + " | ".join(f"{e:^36}" for e in ESTRUCTURAS))
        for n in TAMANOS:
            celdas = []
            for e in ESTRUCTURAS:
                r = next(x for x in resumen if x["estructura"] == e and x["n"] == n and x["tipo"] == tipo)
                celdas.append(f"{r['mediana_us']:>9.3f} [{r['q1_us']:.3f}, {r['q3_us']:.3f}] ({r['atipicos']})".center(36))
            print(f"{n:>8,} | " + " | ".join(celdas))


def serie(resumen, estructura, tipo, campo):
    return [next(r for r in resumen if r["estructura"] == estructura and r["n"] == n and r["tipo"] == tipo)[campo]
            for n in TAMANOS]


def graficar(resumen):
    # Figura 1: tiempo vs n (log-log), mediana con barras = rango intercuartílico
    fig, ejes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, tipo in zip(ejes, TIPOS):
        for nombre in ESTRUCTURAS:
            med = serie(resumen, nombre, tipo, "mediana_us")
            q1 = serie(resumen, nombre, tipo, "q1_us")
            q3 = serie(resumen, nombre, tipo, "q3_us")
            ax.errorbar(TAMANOS, med, yerr=[[m - a for m, a in zip(med, q1)],
                                            [b - m for m, b in zip(med, q3)]],
                        marker="o", capsize=3, label=nombre)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("n (número de estudiantes)")
        ax.set_title(f"ID {tipo.replace('_', ' ')}")
        ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ejes[0].set_ylabel("Tiempo por búsqueda (µs)")
    ejes[0].legend()
    fig.suptitle(f"Tiempo de búsqueda vs tamaño (mediana e IQR de {REPETICIONES} repeticiones)")
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "fig1_tiempos.png"), dpi=150)

    # Figura 2: tiempo / función teórica (debería ser ~constante si se cumple la complejidad)
    fig, ax = plt.subplots(figsize=(8, 5))
    teoria = {"Lista Ligada": lambda n: n,
              "Árbol Binario (BST)": lambda n: math.log2(n),
              "Árbol B+": lambda n: math.log2(n)}
    etiqueta = {"Lista Ligada": "t / n", "Árbol Binario (BST)": "t / log2(n)", "Árbol B+": "t / log2(n)"}
    for nombre in ESTRUCTURAS:
        med = serie(resumen, nombre, "existente", "mediana_us")
        norm = [m / teoria[nombre](n) for m, n in zip(med, TAMANOS)]
        norm = [v / norm[0] for v in norm]   # normalizado al primer tamaño
        ax.plot(TAMANOS, norm, marker="o", label=f"{nombre} ({etiqueta[nombre]})")
    ax.axhline(1, color="gray", linestyle=":")
    ax.set_xscale("log")
    ax.set_xlabel("n (número de estudiantes)")
    ax.set_ylabel("Cociente normalizado (1 = crece como la teoría)")
    ax.set_title("Verificación de la complejidad teórica (ID existente)")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "fig2_complejidad.png"), dpi=150)
    plt.show()


def main():
    os.makedirs(CARPETA, exist_ok=True)
    entorno = describir_entorno()
    print(entorno)
    with open(os.path.join(CARPETA, "entorno.txt"), "w", encoding="utf-8") as f:
        f.write(entorno + "\n")

    print(f"\nEjecutando: tamaños={TAMANOS}, repeticiones={REPETICIONES}, "
          f"búsquedas/tipo/rep={N_BUSQUEDAS}")
    filas = correr_experimento()
    guardar_csv(os.path.join(CARPETA, "mediciones.csv"), filas,
                ["estructura", "n", "tipo", "repeticion", "us_por_busqueda"])

    resumen = resumir(filas)
    cols = list(resumen[0].keys())
    guardar_csv(os.path.join(CARPETA, "resumen.csv"), [[r[c] for c in cols] for r in resumen], cols)
    imprimir_tabla(resumen)
    graficar(resumen)


if __name__ == "__main__":
    main()
