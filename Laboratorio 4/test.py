"""
test.py -- Pruebas del Quadtree (Laboratorio 4).

Este archivo tiene tres partes:

    1. PRUEBAS UNITARIAS (modulo unittest de Python). Cada prueba es un metodo que
       empieza por "test_" y comprueba algo con self.assertEqual, self.assertTrue, etc.
       Si una comprobacion falla, la prueba falla y unittest lo informa.

    2. VISUALIZACIONES (matplotlib). Dibujan el arbol, la busqueda por radio y el
       vecino mas cercano, y guardan las imagenes en la carpeta "figuras/".

    3. ANALISIS DE LAS PRUEBAS. Al terminar se imprime (y se guarda en
       figuras/resultados_pruebas.txt) un resumen de lo que se comprobo.

Como ejecutarlo:
    python test.py

Requisitos: Python 3 y matplotlib (pip install matplotlib).
"""

import math
import os
import random
import unittest

import matplotlib
matplotlib.use("Agg")                      # guardar imagenes sin abrir ventanas
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from Quadtreetree import Nodo, Quadtree, buscar_radio_bruta, vecino_bruto

CARPETA_FIGURAS = "figuras"

# Contadores para el resumen final (cuantas comprobaciones contra fuerza bruta se hicieron)
ESTADISTICAS = {"consultas_radio": 0, "consultas_vecino": 0, "puntos_en_arboles": 0}


# ======================================================================
# Funciones auxiliares (generar datos y recorrer el arbol)
# ======================================================================
def generar_puntos(n, lado, semilla, enteros=False):
    """n puntos al azar en [0, lado] x [0, lado]. Con enteros=True, coordenadas enteras."""
    generador = random.Random(semilla)
    puntos = []
    for _ in range(n):
        if enteros:
            x = generador.randint(0, lado)
            y = generador.randint(0, lado)
        else:
            x = generador.uniform(0, lado)
            y = generador.uniform(0, lado)
        puntos.append((x, y))
    return puntos


def construir_arbol(puntos, lado):
    """Crea un Quadtree para una ciudad de lado x lado e inserta todos los puntos."""
    arbol = Quadtree(0, 0, lado, lado)
    for p in puntos:
        arbol.insertar(p[0], p[1])
    ESTADISTICAS["puntos_en_arboles"] += len(puntos)
    return arbol


def generar_ciudad(n, semilla=1):
    """
    10.000 puntos 'tipo ciudad' para las figuras: tres zonas densas (barrios) mas
    puntos repartidos por toda la ciudad. Coordenadas en metros, ciudad de 10 km x 10 km.
    """
    generador = random.Random(semilla)
    centros_barrios = [(2500, 7000), (7500, 3000), (5000, 5000)]
    puntos = []
    # 1800 puntos por barrio, con distribucion normal alrededor del centro del barrio
    for centro in centros_barrios:
        for _ in range(1800):
            x = generador.gauss(centro[0], 500)
            y = generador.gauss(centro[1], 500)
            # dejar el punto dentro de la ciudad
            x = min(max(x, 0), 10000)
            y = min(max(y, 0), 10000)
            puntos.append((x, y))
    # el resto, uniforme en toda la ciudad
    while len(puntos) < n:
        puntos.append((generador.uniform(0, 10000), generador.uniform(0, 10000)))
    return puntos


def obtener_hojas(nodo, lista_hojas):
    """Recorre el arbol y agrega a 'lista_hojas' todas las hojas (mismo patron de contar)."""
    if nodo.es_hoja():
        lista_hojas.append(nodo)
    else:
        for hijo in nodo.hijos:
            obtener_hojas(hijo, lista_hojas)


def profundidad_del_arbol(nodo):
    """Nivel mas profundo que alcanza el arbol (la raiz es el nivel 0)."""
    if nodo.es_hoja():
        return nodo.profundidad
    mayor = 0
    for hijo in nodo.hijos:
        p = profundidad_del_arbol(hijo)
        if p > mayor:
            mayor = p
    return mayor


def k_cercanos(arbol, qx, qy, k, radio_inicial=100.0):
    """
    Los k puntos mas cercanos a (qx, qy), usando solo buscar_radio del arbol.
    Se duplica el radio hasta encontrar al menos k puntos y se ordenan por distancia.
    Si hay k puntos o mas dentro de un radio r, los k primeros por distancia son los k
    mas cercanos (todo punto fuera del radio esta mas lejos que los de adentro).
    Devuelve una lista de tuplas (x, y, distancia), de menor a mayor distancia.
    """
    radio = radio_inicial
    ancho = max(arbol.x_max - arbol.x_min, arbol.y_max - arbol.y_min)
    while True:
        candidatos = arbol.buscar_radio(qx, qy, radio)
        if len(candidatos) >= k or radio > 2 * ancho:
            break
        radio = radio * 2

    con_distancia = []
    for p in candidatos:
        d = math.hypot(p[0] - qx, p[1] - qy)
        con_distancia.append((p[0], p[1], d))
    con_distancia.sort(key=lambda tupla: tupla[2])   # ordenar por el tercer elemento (distancia)
    return con_distancia[:k]


# ======================================================================
# 1. PRUEBAS UNITARIAS
# ======================================================================
class PruebaBase(unittest.TestCase):
    """Metodos comunes: comparar el arbol con fuerza bruta (y contar cuantas veces se hace)."""

    def comparar_radio(self, arbol, puntos, centros, radio):
        """Para cada centro, el arbol y la fuerza bruta deben devolver los MISMOS puntos."""
        for centro in centros:
            qx = centro[0]
            qy = centro[1]
            del_arbol = sorted(arbol.buscar_radio(qx, qy, radio))
            de_bruta = sorted(buscar_radio_bruta(puntos, qx, qy, radio))
            self.assertEqual(del_arbol, de_bruta, f"Difieren en el centro {centro}")
            ESTADISTICAS["consultas_radio"] += 1

    def comparar_vecino(self, arbol, puntos, centros):
        """
        Para cada centro, la DISTANCIA al vecino debe ser la misma. Se comparan
        distancias y no puntos porque, si dos puntos empatan, cualquiera de los dos es valido.
        """
        for centro in centros:
            qx = centro[0]
            qy = centro[1]
            punto_arbol, dist_arbol = arbol.buscar_vecino(qx, qy)
            punto_bruta, dist_bruta = vecino_bruto(puntos, qx, qy)
            self.assertAlmostEqual(dist_arbol, dist_bruta, places=9,
                                   msg=f"Distancias distintas en el centro {centro}")
            ESTADISTICAS["consultas_vecino"] += 1


class PruebasNodo(PruebaBase):
    """Piezas pequenas del nodo: bordes, indice del hijo, division y distancias."""

    def test_contiene_respeta_la_regla_de_bordes(self):
        # Regla: x en [x_min, x_max), y en (y_min, y_max]
        n = Nodo(0, 0, 100, 100, 4, 20)
        self.assertTrue(n.contiene(50, 50))
        self.assertTrue(n.contiene(0, 100))      # esquina superior izquierda: pertenece
        self.assertFalse(n.contiene(0, 0))       # borde inferior: no pertenece
        self.assertFalse(n.contiene(100, 50))    # borde derecho: no pertenece
        self.assertFalse(n.contiene(-1, 20))     # fuera

    def test_indice_hijo_en_los_cuatro_cuadrantes(self):
        n = Nodo(0, 0, 100, 100, 4, 20)          # centro (50, 50)
        self.assertEqual(n.indice_hijo(10, 10), 0)   # abajo-izquierda
        self.assertEqual(n.indice_hijo(90, 10), 1)   # abajo-derecha
        self.assertEqual(n.indice_hijo(10, 90), 2)   # arriba-izquierda
        self.assertEqual(n.indice_hijo(90, 90), 3)   # arriba-derecha

    def test_indice_hijo_en_las_lineas_del_medio(self):
        n = Nodo(0, 0, 100, 100, 4, 20)
        self.assertEqual(n.indice_hijo(50, 50), 1)   # x == cx va a la derecha, y == cy va abajo
        self.assertEqual(n.indice_hijo(50, 20), 1)
        self.assertEqual(n.indice_hijo(20, 50), 0)

    def test_indice_hijo_y_contiene_estan_de_acuerdo(self):
        # El hijo elegido por indice_hijo debe CONTENER al punto (misma regla de bordes)
        n = Nodo(0, 0, 100, 100, 4, 20)
        n.dividir()
        puntos = [(10, 10), (90, 10), (10, 90), (90, 90), (50, 50), (50, 20), (20, 50),
                  (50, 100), (0, 100), (99.9, 0.1)]
        for p in puntos:
            hijo = n.hijos[n.indice_hijo(p[0], p[1])]
            self.assertTrue(hijo.contiene(p[0], p[1]), f"El hijo no contiene a {p}")

    def test_dividir_reparte_los_puntos(self):
        n = Nodo(0, 0, 100, 100, 4, 20)
        n.puntos = [(10, 10), (90, 10), (20, 30), (80, 80), (60, 20)]
        n.dividir()
        self.assertEqual(n.puntos, [])                                  # el padre queda vacio
        self.assertEqual(sorted(n.hijos[0].puntos), [(10, 10), (20, 30)])
        self.assertEqual(sorted(n.hijos[1].puntos), [(60, 20), (90, 10)])
        self.assertEqual(n.hijos[2].puntos, [])
        self.assertEqual(n.hijos[3].puntos, [(80, 80)])
        self.assertEqual(n.hijos[0].profundidad, 1)                     # los hijos bajan un nivel

    def test_distancia_minima_a_un_rectangulo(self):
        n = Nodo(40, 40, 60, 60, 4, 20)
        self.assertEqual(n.distancia_min2(10, 50), 900)   # a la izquierda: dx = 30
        self.assertEqual(n.distancia_min2(45, 20), 400)   # abajo: dy = 20
        self.assertEqual(n.distancia_min2(30, 70), 200)   # en diagonal: 10^2 + 10^2
        self.assertEqual(n.distancia_min2(50, 50), 0)     # adentro

    def test_toca_el_nodo(self):
        n = Nodo(40, 40, 60, 60, 4, 20)
        self.assertFalse(n.toca_el_nodo(100, 50, 30))     # el cuadrado llega hasta x = 70 > 60
        self.assertTrue(n.toca_el_nodo(100, 50, 45))      # llega hasta x = 55: se cruza
        # La prueba es conservadora: el cuadrado se cruza pero el circulo no toca el nodo
        # (distancia del centro a la esquina (60, 60) es 14.1 > 12). Se revisa de todos modos.
        self.assertTrue(n.toca_el_nodo(70, 70, 12))


class PruebasInsercion(PruebaBase):
    """Construccion del arbol: que no se pierdan ni se dupliquen puntos."""

    def test_contar_es_igual_a_los_puntos_insertados(self):
        puntos = generar_puntos(1000, 10000, semilla=1)
        arbol = construir_arbol(puntos, 10000)
        self.assertEqual(arbol.contar(), 1000)
        self.assertEqual(arbol.cantidad_puntos, 1000)

    def test_los_5_puntos_del_ejemplo(self):
        arbol = Quadtree(0, 0, 100, 100)
        for p in [(10, 10), (90, 10), (20, 30), (80, 80), (60, 20)]:
            arbol.insertar(p[0], p[1])
        self.assertEqual(arbol.contar(), 5)
        self.assertEqual(arbol.raiz.puntos, [])           # la raiz se dividio: no guarda puntos
        self.assertFalse(arbol.raiz.es_hoja())

    def test_un_solo_punto(self):
        arbol = Quadtree(5, 5, 5, 5)                      # region de ancho 0: el margen la salva
        arbol.insertar(5, 5)
        self.assertEqual(arbol.contar(), 1)

    def test_puntos_identicos_no_causan_recursion_infinita(self):
        for cantidad in (5, 100):
            arbol = Quadtree(0, 0, 100, 100)
            for _ in range(cantidad):
                arbol.insertar(10, 10)
            self.assertEqual(arbol.contar(), cantidad)    # no se perdio ninguno

    def test_la_profundidad_no_supera_el_maximo(self):
        arbol = Quadtree(0, 0, 100, 100, capacidad=4, profundidad_max=6)
        for _ in range(50):
            arbol.insertar(10, 10)                        # puntos identicos: dividir no los separa
        self.assertEqual(profundidad_del_arbol(arbol.raiz), 6)
        self.assertEqual(arbol.contar(), 50)

    def test_las_hojas_respetan_la_capacidad_salvo_en_la_profundidad_maxima(self):
        puntos = generar_puntos(2000, 10000, semilla=2)
        arbol = construir_arbol(puntos, 10000)
        hojas = []
        obtener_hojas(arbol.raiz, hojas)
        for hoja in hojas:
            if hoja.profundidad < hoja.profundidad_max:
                self.assertLessEqual(len(hoja.puntos), hoja.capacidad)

    def test_puntos_sobre_los_bordes_de_los_cuadrantes(self):
        # Coordenadas enteras en una ciudad pequena: muchos puntos caen justo sobre
        # las lineas que dividen los cuadrantes (x == cx, y == cy) y sobre y = 0.
        puntos = generar_puntos(3000, 100, semilla=3, enteros=True)
        arbol = construir_arbol(puntos, 100)
        self.assertEqual(arbol.contar(), 3000)

    def test_las_esquinas_de_la_ciudad_se_aceptan(self):
        arbol = Quadtree(0, 0, 100, 100)
        for p in [(0, 0), (100, 0), (0, 100), (100, 100)]:
            arbol.insertar(p[0], p[1])
        self.assertEqual(arbol.contar(), 4)

    def test_un_punto_fuera_de_la_region_lanza_error(self):
        arbol = Quadtree(0, 0, 100, 100)
        with self.assertRaises(ValueError):               # se espera que se lance ValueError
            arbol.insertar(-50, 20)
        self.assertEqual(arbol.cantidad_puntos, 0)        # y que no se cuente
        self.assertEqual(arbol.contar(), 0)


class PruebasBusquedaPorRadio(PruebaBase):
    """Range search: el arbol debe dar exactamente lo mismo que fuerza bruta."""

    def test_ejemplo_de_5_puntos_calculado_a_mano(self):
        # Distancias^2 desde (50, 50): 3200, 3200, 1300, 1800, 1000. Con r = 45 (r^2 = 2025)
        # entran (20, 30), (80, 80) y (60, 20).
        arbol = Quadtree(0, 0, 100, 100)
        for p in [(10, 10), (90, 10), (20, 30), (80, 80), (60, 20)]:
            arbol.insertar(p[0], p[1])
        self.assertEqual(sorted(arbol.buscar_radio(50, 50, 45)),
                         [(20, 30), (60, 20), (80, 80)])

    def test_igual_a_fuerza_bruta_con_10000_puntos_aleatorios(self):
        puntos = generar_puntos(10000, 10000, semilla=4)
        arbol = construir_arbol(puntos, 10000)
        generador = random.Random(5)
        centros = []
        for _ in range(100):
            centros.append((generador.uniform(0, 10000), generador.uniform(0, 10000)))
        self.comparar_radio(arbol, puntos, centros, 500)

    def test_igual_a_fuerza_bruta_con_coordenadas_enteras(self):
        # Coordenadas enteras: aparecen puntos en los bordes y a distancia exactamente r.
        puntos = generar_puntos(3000, 100, semilla=6, enteros=True)
        arbol = construir_arbol(puntos, 100)
        generador = random.Random(7)
        centros = []
        for _ in range(200):
            centros.append((generador.randint(-10, 110), generador.randint(-10, 110)))
        self.comparar_radio(arbol, puntos, centros, 15)

    def test_un_punto_a_distancia_exactamente_r_si_entra(self):
        arbol = Quadtree(0, 0, 100, 100)
        arbol.insertar(3, 4)                              # distancia 5 al origen
        self.assertEqual(arbol.buscar_radio(0, 0, 5), [(3, 4)])
        self.assertEqual(arbol.buscar_radio(0, 0, 4.99), [])

    def test_radio_cero_devuelve_solo_los_puntos_en_ese_lugar(self):
        puntos = generar_puntos(500, 50, semilla=8, enteros=True)
        arbol = construir_arbol(puntos, 50)
        centros = [(0, 0), (25, 25), (50, 50), (10, 40)]
        self.comparar_radio(arbol, puntos, centros, 0)

    def test_centros_en_las_esquinas_y_fuera_de_la_ciudad(self):
        puntos = generar_puntos(5000, 10000, semilla=9)
        arbol = construir_arbol(puntos, 10000)
        centros = [(0, 0), (10000, 0), (0, 10000), (10000, 10000),
                   (-300, 5000), (12000, 12000), (5000, -100)]
        self.comparar_radio(arbol, puntos, centros, 500)

    def test_un_radio_enorme_devuelve_todos_los_puntos(self):
        puntos = generar_puntos(1000, 10000, semilla=10)
        arbol = construir_arbol(puntos, 10000)
        self.assertEqual(len(arbol.buscar_radio(5000, 5000, 1e9)), 1000)

    def test_arbol_vacio(self):
        arbol = Quadtree(0, 0, 100, 100)
        self.assertEqual(arbol.buscar_radio(50, 50, 10), [])


class PruebasVecinoMasCercano(PruebaBase):
    """Nearest neighbor: la distancia debe coincidir con la de fuerza bruta."""

    def test_ejemplo_de_5_puntos_calculado_a_mano(self):
        arbol = Quadtree(0, 0, 100, 100)
        for p in [(10, 10), (90, 10), (20, 30), (80, 80), (60, 20)]:
            arbol.insertar(p[0], p[1])
        punto, distancia = arbol.buscar_vecino(50, 50)
        self.assertEqual(punto, (60, 20))                 # distancia^2 = 1000 es la menor
        self.assertAlmostEqual(distancia, math.sqrt(1000))

    def test_igual_a_fuerza_bruta_con_10000_puntos_aleatorios(self):
        puntos = generar_puntos(10000, 10000, semilla=11)
        arbol = construir_arbol(puntos, 10000)
        generador = random.Random(12)
        centros = []
        for _ in range(100):
            centros.append((generador.uniform(-500, 10500), generador.uniform(-500, 10500)))
        self.comparar_vecino(arbol, puntos, centros)

    def test_igual_a_fuerza_bruta_con_coordenadas_enteras(self):
        puntos = generar_puntos(3000, 100, semilla=13, enteros=True)
        arbol = construir_arbol(puntos, 100)
        generador = random.Random(14)
        centros = []
        for _ in range(200):
            centros.append((generador.randint(-10, 110), generador.randint(-10, 110)))
        self.comparar_vecino(arbol, puntos, centros)

    def test_el_vecino_mas_cercano_puede_estar_en_otro_cuadrante(self):
        # q = (50.1, 50) cae en el cuadrante derecho, pero el punto mas cercano (49.9, 50)
        # esta del otro lado de la linea x = 50. Un metodo que solo mirara el cuadrante de q
        # devolveria (80, 50), que esta a 29.9 m en vez de a 0.2 m.
        arbol = Quadtree(0, 0, 100, 100)
        for p in [(10, 10), (10, 90), (90, 10), (90, 90), (5, 5), (49.9, 50), (80, 50)]:
            arbol.insertar(p[0], p[1])
        punto, distancia = arbol.buscar_vecino(50.1, 50)
        self.assertEqual(punto, (49.9, 50))
        self.assertAlmostEqual(distancia, 0.2)

    def test_un_punto_en_el_mismo_lugar_da_distancia_cero(self):
        puntos = generar_puntos(200, 100, semilla=15, enteros=True)
        arbol = construir_arbol(puntos, 100)
        punto, distancia = arbol.buscar_vecino(puntos[0][0], puntos[0][1])
        self.assertEqual(distancia, 0)

    def test_arbol_vacio(self):
        arbol = Quadtree(0, 0, 100, 100)
        punto, distancia = arbol.buscar_vecino(50, 50)
        self.assertIsNone(punto)
        self.assertEqual(distancia, float("inf"))

    def test_k_vecinos_mas_cercanos_igual_a_fuerza_bruta(self):
        puntos = generar_puntos(5000, 10000, semilla=16)
        arbol = construir_arbol(puntos, 10000)
        generador = random.Random(17)
        for _ in range(30):
            qx = generador.uniform(0, 10000)
            qy = generador.uniform(0, 10000)
            del_arbol = k_cercanos(arbol, qx, qy, 5)
            todas = []
            for p in puntos:
                todas.append(math.hypot(p[0] - qx, p[1] - qy))
            todas.sort()
            for i in range(5):
                self.assertAlmostEqual(del_arbol[i][2], todas[i], places=9)


# ======================================================================
# 2. VISUALIZACIONES
# ======================================================================
def separar_coordenadas(puntos):
    """De una lista de tuplas (x, y) devuelve dos listas: todas las x y todas las y."""
    xs = []
    ys = []
    for p in puntos:
        xs.append(p[0])
        ys.append(p[1])
    return xs, ys


def dibujar_hojas(ax, arbol, transparencia=0.6, grosor=0.5):
    """Dibuja el rectangulo de cada hoja del arbol. Devuelve cuantas hojas hay."""
    hojas = []
    obtener_hojas(arbol.raiz, hojas)
    for hoja in hojas:
        rectangulo = Rectangle((hoja.x_min, hoja.y_min),
                               hoja.x_max - hoja.x_min, hoja.y_max - hoja.y_min,
                               fill=False, edgecolor="#6e7781",
                               linewidth=grosor, alpha=transparencia)
        ax.add_patch(rectangulo)
    return len(hojas)


def preparar_ejes(ax, xlim, ylim, titulo):
    ax.set_xlim(xlim[0], xlim[1])
    ax.set_ylim(ylim[0], ylim[1])
    ax.set_aspect("equal", adjustable="box")   # misma escala en x e y: el circulo se ve circular
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(titulo)


def guardar_figura(fig, nombre_archivo):
    os.makedirs(CARPETA_FIGURAS, exist_ok=True)
    ruta = os.path.join(CARPETA_FIGURAS, nombre_archivo)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    print("  figura guardada:", ruta)


def graficar_arbol(arbol, puntos, nombre_archivo):
    """Puntos y rectangulos de las hojas: hay mas subdivision donde hay mas puntos."""
    fig, ax = plt.subplots(figsize=(8, 8))
    xs, ys = separar_coordenadas(puntos)
    ax.scatter(xs, ys, s=2, c="#b8bcc4", zorder=2)
    cantidad_hojas = dibujar_hojas(ax, arbol)
    limites_x = (arbol.x_min, arbol.x_max)
    limites_y = (arbol.y_min, arbol.y_max)
    preparar_ejes(ax, limites_x, limites_y,
                  f"Quadtree: {len(puntos):,} puntos y {cantidad_hojas:,} hojas")
    guardar_figura(fig, nombre_archivo)


def graficar_radio(arbol, puntos, qx, qy, radio, nombre_archivo):
    """
    Verificacion visual del range search.
      gris  = puntos que NO se encontraron      azul = puntos dentro del radio
      circulo naranja = radio de busqueda       X roja = centro de la consulta
    Izquierda: toda la ciudad. Derecha: zoom alrededor del centro.
    El titulo dice si el resultado coincide con el de fuerza bruta.
    """
    encontrados = arbol.buscar_radio(qx, qy, radio)
    esperados = buscar_radio_bruta(puntos, qx, qy, radio)
    coincide = sorted(encontrados) == sorted(esperados)

    # Un set permite preguntar rapido si un punto esta entre los encontrados
    set_encontrados = set(encontrados)
    no_encontrados = []
    for p in puntos:
        if p not in set_encontrados:
            no_encontrados.append(p)
    xs_no, ys_no = separar_coordenadas(no_encontrados)
    xs_si, ys_si = separar_coordenadas(encontrados)

    fig, (ax_general, ax_zoom) = plt.subplots(1, 2, figsize=(14, 7))
    for ax, es_zoom in ((ax_general, False), (ax_zoom, True)):
        ax.scatter(xs_no, ys_no, s=12 if es_zoom else 3, c="#b8bcc4", zorder=2,
                   label="no encontrados")
        ax.scatter(xs_si, ys_si, s=28 if es_zoom else 10, c="#1f6feb", zorder=4,
                   label=f"dentro del radio ({len(encontrados)})")
        dibujar_hojas(ax, arbol, transparencia=0.6 if es_zoom else 0.35,
                      grosor=0.6 if es_zoom else 0.3)
        ax.add_patch(Circle((qx, qy), radio, fill=False, edgecolor="#bf8700",
                            linewidth=1.8, zorder=5))
        ax.scatter([qx], [qy], s=60, c="#d1242f", marker="x", zorder=6, label="centro q")

    preparar_ejes(ax_general, (arbol.x_min, arbol.x_max), (arbol.y_min, arbol.y_max),
                  "Vista general")
    ventana = 2.2 * radio
    preparar_ejes(ax_zoom, (qx - ventana, qx + ventana), (qy - ventana, qy + ventana),
                  f"Zoom alrededor de q (r = {radio:g} m)")
    ax_zoom.legend(loc="upper right", fontsize=8)

    estado = "coincide con fuerza bruta" if coincide else "NO COINCIDE con fuerza bruta"
    fig.suptitle(f"Busqueda por radio desde q = ({qx:.0f}, {qy:.0f}): "
                 f"{len(encontrados)} puntos, {estado}")
    guardar_figura(fig, nombre_archivo)


def graficar_vecino(arbol, puntos, qx, qy, nombre_archivo):
    """
    Verificacion visual del vecino mas cercano (verde). Se dibuja el circulo con centro en q
    y radio = distancia al vecino: si el resultado es correcto, el interior queda vacio.
    """
    vecino, distancia = arbol.buscar_vecino(qx, qy)
    punto_bruta, distancia_bruta = vecino_bruto(puntos, qx, qy)
    coincide = abs(distancia - distancia_bruta) < 1e-9

    xs, ys = separar_coordenadas(puntos)
    fig, (ax_general, ax_zoom) = plt.subplots(1, 2, figsize=(14, 7))
    for ax, es_zoom in ((ax_general, False), (ax_zoom, True)):
        ax.scatter(xs, ys, s=14 if es_zoom else 3, c="#b8bcc4", zorder=2, label="puntos")
        dibujar_hojas(ax, arbol, transparencia=0.6 if es_zoom else 0.35,
                      grosor=0.6 if es_zoom else 0.3)
        ax.add_patch(Circle((qx, qy), distancia, fill=False, edgecolor="#bf8700",
                            linewidth=1.8, linestyle="--", zorder=5))
        ax.plot([qx, vecino[0]], [qy, vecino[1]], c="#2da44e", linewidth=1.5, zorder=5)
        ax.scatter([vecino[0]], [vecino[1]], s=90 if es_zoom else 60, c="#2da44e", zorder=6,
                   label=f"vecino mas cercano ({distancia:.1f} m)")
        ax.scatter([qx], [qy], s=60, c="#d1242f", marker="x", zorder=7, label="centro q")

    preparar_ejes(ax_general, (arbol.x_min, arbol.x_max), (arbol.y_min, arbol.y_max),
                  "Vista general")
    ventana = max(2.0 * distancia, 1.0)
    preparar_ejes(ax_zoom, (qx - ventana, qx + ventana), (qy - ventana, qy + ventana),
                  "Zoom: el circulo punteado debe estar vacio")
    ax_zoom.legend(loc="upper right", fontsize=8)

    estado = "coincide con fuerza bruta" if coincide else "NO COINCIDE con fuerza bruta"
    fig.suptitle(f"Vecino mas cercano de q = ({qx:.0f}, {qy:.0f}): {estado}")
    guardar_figura(fig, nombre_archivo)


def graficar_k_vecinos(arbol, puntos, qx, qy, k, nombre_archivo):
    """Los k vecinos mas cercanos, numerados de 1 (el mas cercano) a k."""
    vecinos = k_cercanos(arbol, qx, qy, k)
    distancia_k = vecinos[-1][2]

    # Comprobacion con fuerza bruta: las k menores distancias de toda la lista
    todas = []
    for p in puntos:
        todas.append(math.hypot(p[0] - qx, p[1] - qy))
    todas.sort()
    coincide = True
    for i in range(k):
        if abs(vecinos[i][2] - todas[i]) > 1e-9:
            coincide = False

    xs, ys = separar_coordenadas(puntos)
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(xs, ys, s=14, c="#b8bcc4", zorder=2)
    dibujar_hojas(ax, arbol, transparencia=0.6, grosor=0.6)
    ax.add_patch(Circle((qx, qy), distancia_k, fill=False, edgecolor="#bf8700",
                        linewidth=1.8, linestyle="--", zorder=5))
    numero = 1
    for vecino in vecinos:
        x, y, d = vecino
        ax.plot([qx, x], [qy, y], c="#1f6feb", linewidth=1.0, alpha=0.7, zorder=5)
        ax.scatter([x], [y], s=70, c="#1f6feb", zorder=6)
        ax.annotate(f"{numero}  ({d:.0f} m)", (x, y), textcoords="offset points",
                    xytext=(6, 6), fontsize=9, zorder=7)
        numero += 1
    ax.scatter([qx], [qy], s=70, c="#d1242f", marker="x", zorder=7)

    ventana = 1.6 * distancia_k
    estado = "coincide con fuerza bruta" if coincide else "NO COINCIDE con fuerza bruta"
    preparar_ejes(ax, (qx - ventana, qx + ventana), (qy - ventana, qy + ventana),
                  f"{k} vecinos mas cercanos de q = ({qx:.0f}, {qy:.0f}): {estado}")
    guardar_figura(fig, nombre_archivo)


def generar_figuras():
    print("\nGenerando figuras en la carpeta", CARPETA_FIGURAS, "...")
    puntos = generar_ciudad(10000)
    arbol = construir_arbol(puntos, 10000)
    graficar_arbol(arbol, puntos, "fig_arbol.png")
    graficar_radio(arbol, puntos, 5000, 5000, 500, "fig_radio_centro.png")     # zona densa
    graficar_radio(arbol, puntos, 300, 400, 500, "fig_radio_esquina.png")      # cerca de una esquina
    graficar_vecino(arbol, puntos, 2500, 7000, "fig_vecino_zona_densa.png")
    graficar_vecino(arbol, puntos, 9000, 9000, "fig_vecino_zona_vacia.png")
    graficar_k_vecinos(arbol, puntos, 7400, 3100, 5, "fig_k_vecinos.png")


# ======================================================================
# 3. ANALISIS DE LAS PRUEBAS
# ======================================================================
def resumen_de_pruebas(programa):
    """Texto con lo que se comprobo (se imprime y se guarda en figuras/resultados_pruebas.txt)."""
    resultado = programa.result
    ejecutadas = resultado.testsRun
    fallidas = len(resultado.failures) + len(resultado.errors)
    lineas = [
        "RESUMEN DE LAS PRUEBAS",
        "----------------------",
        f"Pruebas unitarias ejecutadas : {ejecutadas}",
        f"Pruebas que pasaron          : {ejecutadas - fallidas}",
        f"Pruebas que fallaron         : {fallidas}",
        f"Consultas de radio comparadas con fuerza bruta    : {ESTADISTICAS['consultas_radio']:,}",
        f"Consultas de vecino comparadas con fuerza bruta   : {ESTADISTICAS['consultas_vecino']:,}",
        f"Puntos insertados en los arboles de prueba        : {ESTADISTICAS['puntos_en_arboles']:,}",
        "",
        "Que se comprobo:",
        "  - Regla de bordes: contiene() e indice_hijo() usan el mismo criterio.",
        "  - Insercion: no se pierden ni se duplican puntos (contar() == puntos insertados),",
        "    tambien con puntos identicos, un solo punto y puntos sobre los bordes.",
        "  - La profundidad maxima corta la recursion con puntos identicos.",
        "  - Un punto fuera de la region se rechaza con ValueError.",
        "  - Busqueda por radio y vecino mas cercano dan EXACTAMENTE lo mismo que fuerza",
        "    bruta con coordenadas continuas, coordenadas enteras (bordes y empates),",
        "    centros en esquinas y fuera de la ciudad, radio 0 y radio enorme.",
        "  - El vecino mas cercano puede estar en otro cuadrante que el de q.",
    ]
    return "\n".join(lineas)


if __name__ == "__main__":
    programa = unittest.main(exit=False, verbosity=2)      # corre todas las pruebas de arriba
    texto = resumen_de_pruebas(programa)
    print("\n" + texto)
    os.makedirs(CARPETA_FIGURAS, exist_ok=True)
    with open(os.path.join(CARPETA_FIGURAS, "resultados_pruebas.txt"), "w", encoding="utf-8") as f:
        f.write(texto + "\n")
    if programa.result.wasSuccessful():
        generar_figuras()
    else:
        print("\nHay pruebas que fallaron: no se generan las figuras.")
