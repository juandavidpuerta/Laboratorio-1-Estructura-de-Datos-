# -*- coding: utf-8 -*-
"""
Laboratorio 3 - Estructura de Datos
Implementaciones: Lista Ligada, Árbol Binario de Búsqueda (BST) y Árbol B+.
Este módulo NO mide tiempos; los mide experimento.py.
"""

import random

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
class EstudianteDatosGenerador:
    nombres = ["Juan", "María", "Pedro", "Ana", "Luis", "Sofía", "Carlos", "Laura"]
    apellidos = ["García", "Rodríguez", "Martínez", "Hernández",
                 "López", "González", "Pérez", "Sánchez"]

    @classmethod
    def generar_lote(cls, cantidad, id_min=2_000_000, id_max=10_000_000):
        """Genera `cantidad` estudiantes con IDs únicos (id, nombre, edad, promedio)."""
        ids = random.sample(range(id_min, id_max + 1), cantidad)
        return [
            (
                id_est,
                random.choice(cls.nombres) + " " + random.choice(cls.apellidos),
                random.randint(18, 25),
                round(random.uniform(0.0, 5.0), 2),
            )
            for id_est in ids
        ]


def imprimir_estudiante(id_, nombre, edad, promedio):
    print(f"ID: {id_}, Nombre: {nombre}, Edad: {edad}, Promedio: {promedio}")


# ---------------------------------------------------------------------------
# 1. Lista ligada
# ---------------------------------------------------------------------------
class Nodo:
    def __init__(self, id, nombre, edad, promedio):
        self.id = id
        self.nombre = nombre
        self.edad = edad
        self.promedio = promedio
        self.siguiente = None


class ListaLigada:
    def __init__(self):
        self.primero = None
        self.ultimo = None  # evita recorrer toda la lista en cada inserción

    def insertar_estudiante(self, id, nombre, edad, promedio):
        nuevo = Nodo(id, nombre, edad, promedio)
        if self.primero is None:
            self.primero = nuevo
        else:
            self.ultimo.siguiente = nuevo
        self.ultimo = nuevo

    def buscar_por_id(self, id):
        """Devuelve (id, nombre, edad, promedio) o None. Recorrido secuencial: O(n)."""
        actual = self.primero
        while actual is not None:
            if actual.id == id:
                return actual.id, actual.nombre, actual.edad, actual.promedio
            actual = actual.siguiente
        return None

    def listar_estudiantes(self, limite=None):
        """Lista en orden de inserción (la lista NO ordena por ID)."""
        actual = self.primero
        contador = 0
        while actual is not None and (limite is None or contador < limite):
            imprimir_estudiante(actual.id, actual.nombre, actual.edad, actual.promedio)
            actual = actual.siguiente
            contador += 1


# ---------------------------------------------------------------------------
# 2. Árbol binario de búsqueda
# ---------------------------------------------------------------------------
class NodoArbolBinario:
    def __init__(self, id, nombre, edad, promedio):
        self.id = id
        self.nombre = nombre
        self.edad = edad
        self.promedio = promedio
        self.izquierda = None
        self.derecha = None


class ArbolBinario:
    def __init__(self):
        self.raiz = None

    def insertar(self, id, nombre, edad, promedio):
        nuevo = NodoArbolBinario(id, nombre, edad, promedio)
        if self.raiz is None:
            self.raiz = nuevo
            return
        actual = self.raiz
        while True:
            if id < actual.id:
                if actual.izquierda is None:
                    actual.izquierda = nuevo
                    return
                actual = actual.izquierda
            else:
                if actual.derecha is None:
                    actual.derecha = nuevo
                    return
                actual = actual.derecha

    def buscar_por_id(self, id):
        """Devuelve (id, nombre, edad, promedio) o None. O(h): h ~ log n en promedio."""
        actual = self.raiz
        while actual is not None:
            if actual.id == id:
                return actual.id, actual.nombre, actual.edad, actual.promedio
            actual = actual.izquierda if id < actual.id else actual.derecha
        return None

    def _inorden(self, nodo, limite, contador):
        if nodo is None or (limite is not None and contador[0] >= limite):
            return
        self._inorden(nodo.izquierda, limite, contador)
        if limite is None or contador[0] < limite:
            imprimir_estudiante(nodo.id, nodo.nombre, nodo.edad, nodo.promedio)
            contador[0] += 1
        self._inorden(nodo.derecha, limite, contador)

    def listar_estudiantes(self, limite=None):
        print("Listado de estudiantes (ordenado por ID):")
        self._inorden(self.raiz, limite, [0])


# ---------------------------------------------------------------------------
# 3. Árbol B+
# ---------------------------------------------------------------------------
class NodoBPlus:
    def __init__(self, orden, es_hoja=False):
        self.orden = orden
        self.claves = []
        self.hijos = []             # nodos hijos (internos) o registros (hojas)
        self.es_hoja = es_hoja
        self.siguiente_hoja = None  # enlace entre hojas (recorridos por rango)
        self.padre = None


class BPlusTree:
    def __init__(self, orden):
        self.orden = orden
        self.raiz = NodoBPlus(orden, es_hoja=True)

    def _buscar_hoja(self, key):
        nodo = self.raiz
        while not nodo.es_hoja:
            i = 0
            while i < len(nodo.claves) and key >= nodo.claves[i]:
                i += 1
            nodo = nodo.hijos[i]
        return nodo

    def insertar(self, id_estudiante, nombre, edad, promedio):
        registro = {'id': id_estudiante, 'nombre': nombre,
                    'edad': edad, 'promedio': promedio}
        hoja = self._buscar_hoja(id_estudiante)

        i = 0
        while i < len(hoja.claves) and id_estudiante > hoja.claves[i]:
            i += 1
        hoja.claves.insert(i, id_estudiante)
        hoja.hijos.insert(i, registro)

        if len(hoja.claves) > self.orden - 1:
            self._dividir_hoja(hoja)

    def _dividir_hoja(self, nodo_viejo):
        nuevo = NodoBPlus(self.orden, es_hoja=True)
        medio = len(nodo_viejo.claves) // 2

        nuevo.claves = nodo_viejo.claves[medio:]
        nuevo.hijos = nodo_viejo.hijos[medio:]
        nodo_viejo.claves = nodo_viejo.claves[:medio]
        nodo_viejo.hijos = nodo_viejo.hijos[:medio]

        nuevo.siguiente_hoja = nodo_viejo.siguiente_hoja
        nodo_viejo.siguiente_hoja = nuevo

        self._promover(nodo_viejo, nuevo.claves[0], nuevo)

    def _dividir_interno(self, nodo_viejo):
        nuevo = NodoBPlus(self.orden)
        medio = len(nodo_viejo.claves) // 2
        clave_promovida = nodo_viejo.claves[medio]

        nuevo.claves = nodo_viejo.claves[medio + 1:]
        nuevo.hijos = nodo_viejo.hijos[medio + 1:]
        nodo_viejo.claves = nodo_viejo.claves[:medio]
        nodo_viejo.hijos = nodo_viejo.hijos[:medio + 1]

        for hijo in nuevo.hijos:
            hijo.padre = nuevo

        self._promover(nodo_viejo, clave_promovida, nuevo)

    def _promover(self, nodo_viejo, clave, nodo_nuevo):
        """Sube `clave` al padre de `nodo_viejo`; crea nueva raíz si hace falta."""
        if nodo_viejo is self.raiz:
            nueva_raiz = NodoBPlus(self.orden)
            nueva_raiz.claves = [clave]
            nueva_raiz.hijos = [nodo_viejo, nodo_nuevo]
            nodo_viejo.padre = nueva_raiz
            nodo_nuevo.padre = nueva_raiz
            self.raiz = nueva_raiz
        else:
            self._insertar_en_padre(nodo_viejo.padre, clave, nodo_nuevo)

    def _insertar_en_padre(self, padre, clave, hijo_derecho):
        i = 0
        while i < len(padre.claves) and clave > padre.claves[i]:
            i += 1
        padre.claves.insert(i, clave)
        padre.hijos.insert(i + 1, hijo_derecho)
        hijo_derecho.padre = padre

        if len(padre.claves) > self.orden - 1:
            self._dividir_interno(padre)

    def buscar_por_id(self, id_estudiante):
        """Devuelve (id, nombre, edad, promedio) o None. Desciende por la altura del árbol: O(log n)."""
        hoja = self._buscar_hoja(id_estudiante)
        for i, clave in enumerate(hoja.claves):
            if clave == id_estudiante:
                r = hoja.hijos[i]
                return r['id'], r['nombre'], r['edad'], r['promedio']
        return None

    def listar_estudiantes(self, limite=None):
        print("Listado de estudiantes (ordenado por ID):")
        nodo = self.raiz
        while not nodo.es_hoja:
            nodo = nodo.hijos[0]
        contador = 0
        while nodo is not None:
            for r in nodo.hijos:
                if limite is not None and contador >= limite:
                    return
                imprimir_estudiante(r['id'], r['nombre'], r['edad'], r['promedio'])
                contador += 1
            nodo = nodo.siguiente_hoja
