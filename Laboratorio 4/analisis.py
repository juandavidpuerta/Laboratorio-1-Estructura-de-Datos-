"""
analisis.py -- Metricas de rendimiento del Laboratorio 4: Quadtree vs fuerza bruta.

Pregunta: ¿desde que tamano de datos el Quadtree es mas rapido que fuerza bruta?

Diseno del experimento:
    - Ciudad de 10 km x 10 km (unidades en metros); puntos uniformes al azar.
    - Para cada n se generan los mismos puntos y los mismos centros de consulta
      para ambos metodos (semilla fija); radio fijo de 500 m.
    - Se cronometra cada consulta por separado (time.perf_counter) y se reporta
      la MEDIANA, menos sensible a valores atipicos que el promedio.
    - La construccion del arbol se mide aparte y se repite varias veces (mediana).
    - En cada consulta se verifica, fuera del cronometro, que ambos metodos devuelven
      exactamente los mismos puntos.
    - Ademas del tiempo se cuenta cuantos puntos revisa cada metodo (el arbol revisa
      solo los de las hojas que toca el circulo; fuerza bruta revisa los n).

Uso:
    python analisis.py                   mide, guarda resultados.csv y genera las graficas
    python analisis.py --solo-graficas   no mide: regenera las graficas desde resultados.csv

Salidas: resultados.csv, entorno.txt, discusion.txt y las graficas en figuras/.
"""

import csv
import os
import platform
import random
import statistics
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from Quadtreetree import Quadtree, buscar_radio_bruta


def contar_revisados(nodo, qx, qy, r):
    """
    Cuantos puntos revisa buscar_radio en este subarbol: sigue la misma poda
    (toca_el_nodo) y suma los puntos de las hojas que no descarta.
    """
    if not nodo.toca_el_nodo(qx, qy, r):
        return 0
    if nodo.es_hoja():
        return len(nodo.puntos)
    total = 0
    for hijo in nodo.hijos:
        total += contar_revisados(hijo, qx, qy, r)
    return total


def medir(n, n_consultas, r=500, semilla=1, repeticiones_construccion=5):
    """
    Mide un tamano n. Devuelve (t_construccion, tiempos_arbol, tiempos_bruta, revisados),
    con tiempos en segundos: la construccion es la mediana de varias repeticiones, los
    dos siguientes son listas con un tiempo por consulta, y 'revisados' es el promedio
    de puntos que el arbol revisa por consulta.
    """
    # Dos generadores independientes: los puntos y los centros NO comparten secuencia
    gen_puntos = random.Random(semilla)
    gen_centros = random.Random(semilla + 1)

    # 1. generar n puntos aleatorios (metros, ciudad de 10 km x 10 km)
    puntos = [(gen_puntos.uniform(0, 10000), gen_puntos.uniform(0, 10000)) for _ in range(n)]

    # 2. construir el arbol varias veces y quedarse con la mediana del tiempo
    tiempos_construccion = []
    for _ in range(repeticiones_construccion):
        t0 = time.perf_counter()
        t = Quadtree(0, 0, 10000, 10000)
        for p in puntos:
            t.insertar(p[0], p[1])
        tiempos_construccion.append(time.perf_counter() - t0)
    t_construccion = statistics.median(tiempos_construccion)

    # 3. generar los centros de consulta
    centros = [(gen_centros.uniform(0, 10000), gen_centros.uniform(0, 10000))
               for _ in range(n_consultas)]

    # 4. un tiempo por consulta, para cada metodo
    tiempos_arbol = []
    tiempos_bruta = []
    lista_revisados = []
    for c in centros:
        qx, qy = c

        t0 = time.perf_counter()
        res_arbol = t.buscar_radio(qx, qy, r)
        tiempos_arbol.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        res_bruta = buscar_radio_bruta(puntos, qx, qy, r)
        tiempos_bruta.append(time.perf_counter() - t0)

        # Verificacion y conteo (fuera del cronometro)
        assert sorted(res_arbol) == sorted(res_bruta), f"Difieren en el centro {c}"
        lista_revisados.append(contar_revisados(t.raiz, qx, qy, r))

    revisados = statistics.mean(lista_revisados)
    return t_construccion, tiempos_arbol, tiempos_bruta, revisados


def barrido(tamanos, n_consultas=300, r=500, archivo_csv=None):
    """
    Repite medir() para cada n. Devuelve dos listas:
        resultados_arbol = [(n, mediana_consulta_us, construccion_ms, revisados), ...]
        resultados_bruta = [(n, mediana_consulta_us), ...]
    Si se da archivo_csv, escribe ahi una fila por n.
    """
    resultados_arbol = []
    resultados_bruta = []
    for n in tamanos:
        t_construccion, tiempos_arbol, tiempos_bruta, revisados = medir(n, n_consultas, r)
        # Medianas en microsegundos; construccion en milisegundos
        mediana_arbol = statistics.median(tiempos_arbol) * 1e6
        mediana_bruta = statistics.median(tiempos_bruta) * 1e6
        resultados_arbol.append((n, mediana_arbol, t_construccion * 1e3, revisados))
        resultados_bruta.append((n, mediana_bruta))
        print(f"n={n:>7,}  arbol={mediana_arbol:9.2f} us  bruta={mediana_bruta:9.2f} us  "
              f"construccion={t_construccion * 1e3:9.2f} ms  revisados={revisados:9.1f}")

    if archivo_csv is not None:
        with open(archivo_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["n", "mediana_arbol_us", "mediana_bruta_us", "construccion_arbol_ms",
                        "puntos_revisados_arbol"])
            for (n, ma, cons, rev), (_, mb) in zip(resultados_arbol, resultados_bruta):
                w.writerow([n, ma, mb, cons, rev])

    return resultados_arbol, resultados_bruta


def encontrar_cruce(resultados_arbol, resultados_bruta):
    """
    Primer n a partir del cual el arbol es mas rapido que fuerza bruta en todos los
    tamanos siguientes. Devuelve None si la bruta gana incluso con el n mas grande; si
    el arbol gana desde el primer tamano, devuelve ese primer tamano (el cruce esta ahi
    o por debajo).
    """
    # Recorrer de mayor a menor y parar en el primero donde la bruta es estrictamente mas rapida
    for i in range(len(resultados_arbol) - 1, -1, -1):
        if resultados_bruta[i][1] < resultados_arbol[i][1]:
            if i == len(resultados_arbol) - 1:
                return None
            return resultados_arbol[i + 1][0]
    return resultados_arbol[0][0]


def leer_csv(archivo_csv):
    """Lee resultados.csv y devuelve (resultados_arbol, resultados_bruta) como barrido()."""
    resultados_arbol = []
    resultados_bruta = []
    with open(archivo_csv, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            n = int(fila["n"])
            resultados_arbol.append((n, float(fila["mediana_arbol_us"]),
                                     float(fila["construccion_arbol_ms"]),
                                     float(fila["puntos_revisados_arbol"])))
            resultados_bruta.append((n, float(fila["mediana_bruta_us"])))
    return resultados_arbol, resultados_bruta


# ----------------------------------------------------------------------
# Graficas
# ----------------------------------------------------------------------
def guardar(fig, nombre):
    os.makedirs("figuras", exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join("figuras", nombre), dpi=150)
    plt.close(fig)
    print("  figura guardada: figuras/" + nombre)


def graficar_todo(res_arbol, res_bruta, cruce):
    ns = [fila[0] for fila in res_arbol]
    t_arbol = [fila[1] for fila in res_arbol]
    t_bruta = [fila[1] for fila in res_bruta]
    construccion = [fila[2] for fila in res_arbol]
    revisados = [fila[3] for fila in res_arbol]
    aceleracion = [b / a for a, b in zip(t_arbol, t_bruta)]   # cuantas veces mas rapido es el arbol

    # 1. Tiempo por consulta, ejes logaritmicos (el rango de n es muy amplio)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(ns, t_bruta, "o-", color="#d1242f", label="fuerza bruta")
    ax.plot(ns, t_arbol, "s-", color="#1f6feb", label="Quadtree")
    if cruce is not None:
        ax.axvline(cruce, color="gray", linestyle=":", label=f"el arbol gana desde n = {cruce}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n (cantidad de puntos)")
    ax.set_ylabel("mediana por consulta (microsegundos)")
    ax.set_title("Busqueda por radio (500 m): tiempo por consulta")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    guardar(fig, "an_tiempos.png")

    # 2. Aceleracion (bruta / arbol); 1 = empate
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(ns, aceleracion, "o-", color="#2da44e")
    ax.axhline(1, color="gray", linestyle="--", label="empate (1x)")
    ax.set_xscale("log")
    ax.set_xlabel("n (cantidad de puntos)")
    ax.set_ylabel("tiempo bruta / tiempo arbol (veces)")
    ax.set_title("Cuantas veces mas rapido es el Quadtree (por encima de 1 gana el arbol)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    guardar(fig, "an_aceleracion.png")

    # 3. Puntos revisados por consulta
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(ns, ns, "o-", color="#d1242f", label="fuerza bruta (revisa los n)")
    ax.plot(ns, revisados, "s-", color="#1f6feb", label="Quadtree")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n (cantidad de puntos)")
    ax.set_ylabel("puntos revisados por consulta")
    ax.set_title("Trabajo hecho por consulta (independiente de la maquina)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    guardar(fig, "an_revisados.png")

    # 4. Costo de construir el arbol
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(ns, construccion, "o-", color="#8250df")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n (cantidad de puntos)")
    ax.set_ylabel("construccion del arbol (milisegundos)")
    ax.set_title("Tiempo de construccion del Quadtree")
    ax.grid(True, which="both", alpha=0.3)
    guardar(fig, "an_construccion.png")

    # 5. Zoom a los n pequenos (escala lineal) para ver el cruce
    chicos = [i for i, n in enumerate(ns) if n <= 50]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot([ns[i] for i in chicos], [t_bruta[i] for i in chicos], "o-", color="#d1242f",
            label="fuerza bruta")
    ax.plot([ns[i] for i in chicos], [t_arbol[i] for i in chicos], "s-", color="#1f6feb",
            label="Quadtree")
    ax.set_xlabel("n (cantidad de puntos)")
    ax.set_ylabel("mediana por consulta (microsegundos)")
    ax.set_title("Zoom a n pequenos: donde se cruzan las curvas")
    ax.grid(True, alpha=0.3)
    ax.legend()
    guardar(fig, "an_zoom_cruce.png")


# ----------------------------------------------------------------------
# Discusion y entorno
# ----------------------------------------------------------------------
def escribir_discusion(res_arbol, res_bruta, cruce, archivo="discusion.txt"):
    """Arma un texto con los numeros de ESTA corrida, lo imprime y lo guarda."""
    lineas = ["DISCUSION DE RESULTADOS (generada con los datos de esta corrida)", ""]
    ns = [f[0] for f in res_arbol]

    if cruce is None:
        lineas.append("Pregunta: en este experimento la fuerza bruta fue mas rapida incluso con "
                      f"n = {ns[-1]:,}; no se observo cruce.")
    else:
        lineas.append(f"Pregunta: el Quadtree empieza a ser mas rapido que fuerza bruta desde "
                      f"n = {cruce} puntos (primer tamano medido desde el cual gana en todos "
                      "los tamanos siguientes).")
        if cruce == ns[0]:
            lineas.append("  (Gana desde el primer tamano medido: el cruce esta ahi o por debajo.)")
        else:
            anterior = ns[ns.index(cruce) - 1]
            lineas.append(f"  El cruce esta entre n = {anterior} y n = {cruce}; los tamanos "
                          "intermedios no se midieron.")

    lineas.append("")
    lineas.append("Aceleracion (tiempo bruta / tiempo arbol) y puntos revisados por consulta:")
    for (n, ta, cons, rev), (_, tb) in zip(res_arbol, res_bruta):
        if n in (10, 100, 1000, 10000, ns[-1]) or n == ns[0]:
            lineas.append(f"  n = {n:>7,}: {tb / ta:6.1f}x   (arbol revisa {rev:8.1f} puntos, "
                          f"bruta revisa {n:,})")

    # Amortizacion de la construccion en el n mas grande
    n, ta, cons, rev = res_arbol[-1]
    tb = res_bruta[-1][1]
    if tb > ta:
        consultas = cons * 1e3 / (tb - ta)          # ms -> us, dividido entre lo que ahorra cada consulta
        lineas.append("")
        lineas.append(f"Construccion: con n = {n:,} el arbol tarda {cons:.1f} ms en construirse; "
                      f"se paga solo despues de unas {consultas:.0f} consultas (construccion / "
                      "ahorro por consulta).")

    lineas += [
        "",
        "Como interpretar:",
        "  - Con n <= capacidad (4) el arbol es una sola hoja: hace lo mismo que fuerza bruta "
        "mas el costo de las llamadas y de la poda, por eso pierde con n muy pequeno.",
        "  - Al crecer n el arbol descarta casi todas las hojas: revisa muchos menos puntos "
        "(grafica an_revisados.png) y el tiempo por consulta crece mucho mas despacio que en bruta.",
        "  - La ciudad es fija (10 km x 10 km) y el radio es fijo (500 m): al aumentar n sube la "
        "densidad, asi que el numero de puntos dentro del circulo tambien crece y el tiempo del "
        "arbol sigue creciendo (de forma lineal pero con pendiente mucho menor). Con densidad "
        "constante el arbol crece como O(log n + k), con k = resultados.",
        "  - El cruce depende del lenguaje, la maquina, la capacidad de hoja y la distribucion; "
        "el valor exacto no es universal, la tendencia si.",
        "  - Las barras de error no se muestran; se uso la mediana de 300 consultas por tamano. "
        "Una sola corrida: los tiempos varian algo entre ejecuciones.",
    ]
    texto = "\n".join(lineas)
    print("\n" + texto)
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(texto + "\n")


def escribir_entorno(archivo="entorno.txt"):
    lineas = [
        "Entorno de la medicion",
        f"Python    : {sys.version.split()[0]}",
        f"Sistema   : {platform.platform()}",
        f"Procesador: {platform.processor() or 'no informado'}",
        "Reloj     : time.perf_counter",
    ]
    with open(archivo, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


if __name__ == "__main__":
    if "--solo-graficas" in sys.argv:
        res_arbol, res_bruta = leer_csv("resultados.csv")
    else:
        tamanos = [2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 50, 100, 200, 500,
                   1000, 2000, 5000, 10000, 20000, 50000]
        res_arbol, res_bruta = barrido(tamanos, n_consultas=300, archivo_csv="resultados.csv")
        escribir_entorno()
    cruce = encontrar_cruce(res_arbol, res_bruta)
    print("Cruce en n =", cruce)
    graficar_todo(res_arbol, res_bruta, cruce)
    escribir_discusion(res_arbol, res_bruta, cruce)
