"""
Quadtreetree.py -- Quadtree 2D implementado desde cero (Laboratorio 4).

Contenido:
    Nodo                  nodo del arbol (region rectangular + puntos o 4 hijos)
    Quadtree              arbol: insercion, conteo, busqueda por radio, vecino mas cercano
    buscar_radio_bruta    busqueda por radio con fuerza bruta (referencia)
    vecino_bruto          vecino mas cercano con fuerza bruta (referencia)

Decisiones de diseno:
    - Es un Quadtree de 2 dimensiones.
    - Regla de bordes: una region contiene x en [x_min, x_max) e y en (y_min, y_max].
      El borde izquierdo y el superior pertenecen al nodo; el derecho y el inferior,
      al vecino. Asi cada punto pertenece a exactamente un cuadrante.
    - Los puntos se guardan solo en las hojas. Una hoja se divide cuando recibe un
      punto y ya tiene 'capacidad' puntos.
    - Profundidad maxima: una hoja en ese nivel no se divide mas y guarda el punto
      aunque supere la capacidad (si hay puntos identicos, dividir no los separa,
      y sin este limite la recursion no terminaria).
    - La raiz cubre un rectangulo un poco mayor que los datos (margen), para que los
      puntos de los bordes no queden fuera.
    - Unidades: las del usuario (en el laboratorio, metros).
"""

# Margen minimo de la region raiz, en las unidades de los datos (metros).
MARGEN_MINIMO = 1


# ----------------------------------------------------------------------
# Nodo
# ----------------------------------------------------------------------
class Nodo:
    def __init__(self, x_min, y_min, x_max, y_max, capacidad, profundidad_max):
        # Limites de la region
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max
        # Cuantos puntos aguanta una hoja antes de dividirse
        self.capacidad = capacidad
        # Nivel maximo del arbol y nivel de este nodo (la raiz es 0)
        self.profundidad_max = profundidad_max
        self.profundidad = 0
        # Puntos (tuplas (x, y)); solo se usan mientras el nodo es hoja
        self.puntos = []
        # None mientras sea hoja; luego, lista de 4 hijos
        self.hijos = None

    def es_hoja(self):
        """True si el nodo no tiene hijos."""
        return self.hijos is None

    def contiene(self, x, y):
        """True si (x, y) esta en la region: x en [x_min, x_max), y en (y_min, y_max]."""
        return (x >= self.x_min and x < self.x_max and
                y > self.y_min and y <= self.y_max)

    def indice_hijo(self, x, y):
        """
        Indice (0 a 3) del hijo donde cae (x, y), segun el centro del nodo.
        0 = abajo-izquierda, 1 = abajo-derecha, 2 = arriba-izquierda, 3 = arriba-derecha.
        Usa la misma regla de bordes que 'contiene': x == cx va a la derecha
        e y == cy va abajo.
        """
        cx = (self.x_min + self.x_max) / 2
        cy = (self.y_min + self.y_max) / 2

        if x >= cx:                 # derecha
            if y > cy:
                return 3            # arriba
            else:
                return 1            # abajo
        else:                       # izquierda
            if y > cy:
                return 2            # arriba
            else:
                return 0            # abajo

    def dividir(self):
        """Crea los 4 hijos y reparte entre ellos los puntos del nodo, que queda vacio."""
        cx = (self.x_min + self.x_max) / 2
        cy = (self.y_min + self.y_max) / 2

        # Orden: 0 = abajo-izquierda, 1 = abajo-derecha, 2 = arriba-izquierda, 3 = arriba-derecha
        hijo0 = Nodo(self.x_min, self.y_min, cx, cy, self.capacidad, self.profundidad_max)
        hijo1 = Nodo(cx, self.y_min, self.x_max, cy, self.capacidad, self.profundidad_max)
        hijo2 = Nodo(self.x_min, cy, cx, self.y_max, self.capacidad, self.profundidad_max)
        hijo3 = Nodo(cx, cy, self.x_max, self.y_max, self.capacidad, self.profundidad_max)
        for hijo in (hijo0, hijo1, hijo2, hijo3):
            hijo.profundidad = self.profundidad + 1
        self.hijos = [hijo0, hijo1, hijo2, hijo3]

        # Repartir los puntos con el mismo criterio que insertar (indice_hijo)
        puntos_viejos = self.puntos
        self.puntos = []
        for p in puntos_viejos:
            self.hijos[self.indice_hijo(p[0], p[1])].insertar(p[0], p[1])

    def insertar(self, x, y):
        """Inserta el punto: baja hasta una hoja; si esta llena, la divide."""
        # Nodo interno: bajar al hijo que corresponde
        if not self.es_hoja():
            self.hijos[self.indice_hijo(x, y)].insertar(x, y)
        # Hoja con espacio: guardar
        elif len(self.puntos) < self.capacidad:
            self.puntos.append((x, y))
        # Hoja llena y todavia se puede dividir: dividir y volver a insertar
        elif self.profundidad < self.profundidad_max:
            self.dividir()
            self.insertar(x, y)
        # Hoja llena en la profundidad maxima: guardar igual para no perder el punto
        # (la hoja puede superar la capacidad; ocurre con puntos identicos o casi identicos)
        else:
            self.puntos.append((x, y))

    def contar(self):
        """Cantidad de puntos guardados en este subarbol (suma de las hojas)."""
        if self.es_hoja():
            return len(self.puntos)
        suma = 0
        for h in self.hijos:
            suma += h.contar()
        return suma

    # ---------------- busqueda por radio ----------------
    def toca_el_nodo(self, qx, qy, r):
        """
        False si el cuadrado que encierra al circulo (centro (qx, qy), radio r) no se
        cruza con la region del nodo; True en caso contrario. Es una prueba
        conservadora: True no asegura que haya puntos dentro del circulo.
        """
        if (qy + r) < self.y_min:
            return False
        if (qy - r) > self.y_max:
            return False
        if (qx + r) < self.x_min:
            return False
        if (qx - r) > self.x_max:
            return False
        return True

    def buscar_radio(self, qx, qy, r, resultado):
        """Agrega a 'resultado' los puntos a distancia <= r de (qx, qy)."""
        # Si el circulo no toca este nodo, se descarta todo su subarbol
        if not self.toca_el_nodo(qx, qy, r):
            return
        # Hoja: revisar cada punto (distancia al cuadrado, sin raiz)
        if self.es_hoja():
            for p in self.puntos:
                if (p[0] - qx) ** 2 + (p[1] - qy) ** 2 <= r ** 2:
                    resultado.append(p)
        # Nodo interno: cada hijo se ocupa de su region
        else:
            for h in self.hijos:
                h.buscar_radio(qx, qy, r, resultado)

    # ---------------- vecino mas cercano ----------------
    def distancia_min2(self, qx, qy):
        """Distancia al cuadrado de (qx, qy) al punto de la region del nodo que le queda mas cerca."""
        if qx < self.x_min:
            dx = self.x_min - qx
        elif qx > self.x_max:
            dx = qx - self.x_max
        else:
            dx = 0

        if qy < self.y_min:
            dy = self.y_min - qy
        elif qy > self.y_max:
            dy = qy - self.y_max
        else:
            dy = 0

        return dx ** 2 + dy ** 2

    def buscar_vecino(self, qx, qy, mejor):
        """
        Actualiza 'mejor' = [distancia al cuadrado, punto] con el punto mas cercano a
        (qx, qy) de este subarbol (empieza en [infinito, None]). Devuelve 'mejor'.
        """
        # Si ni el punto mas cercano de la region mejora el candidato, se descarta
        if mejor[0] <= self.distancia_min2(qx, qy):
            return mejor

        # Hoja: revisar sus puntos
        if self.es_hoja():
            for p in self.puntos:
                d2 = (p[0] - qx) ** 2 + (p[1] - qy) ** 2
                if d2 < mejor[0]:
                    mejor[0] = d2
                    mejor[1] = p
        # Nodo interno: visitar primero los hijos mas cercanos a q, para que
        # 'mejor' baje rapido y la poda descarte mas nodos
        else:
            def distancia_a_q(hijo):
                return hijo.distancia_min2(qx, qy)

            for h in sorted(self.hijos, key=distancia_a_q):
                mejor = h.buscar_vecino(qx, qy, mejor)
        return mejor


# ----------------------------------------------------------------------
# Quadtree
# ----------------------------------------------------------------------
class Quadtree:
    def __init__(self, x_min, y_min, x_max, y_max, capacidad=4, profundidad_max=20):
        """
        Arbol para puntos en el rectangulo [x_min, x_max] x [y_min, y_max].
        La region de la raiz se agranda con un margen (1 % del tamano en cada eje,
        y nunca menos que MARGEN_MINIMO) para que los puntos de los bordes queden dentro.
        """
        margenx = max(0.01 * (x_max - x_min), MARGEN_MINIMO)
        margeny = max(0.01 * (y_max - y_min), MARGEN_MINIMO)
        self.x_min = x_min - margenx
        self.x_max = x_max + margenx
        self.y_min = y_min - margeny
        self.y_max = y_max + margeny
        self.capacidad = capacidad
        self.profundidad_max = profundidad_max
        self.cantidad_puntos = 0    # puntos entregados al arbol (para comparar con contar())
        self.raiz = Nodo(self.x_min, self.y_min, self.x_max, self.y_max,
                         self.capacidad, self.profundidad_max)

    def insertar(self, x, y):
        """Inserta (x, y). Lanza ValueError si el punto queda fuera de la region del arbol."""
        if not self.raiz.contiene(x, y):
            raise ValueError(f"El punto ({x}, {y}) esta fuera de la region del arbol")
        self.cantidad_puntos += 1
        self.raiz.insertar(x, y)

    def contar(self):
        """Total de puntos guardados, recorriendo las hojas (verificacion)."""
        return self.raiz.contar()

    def buscar_radio(self, qx, qy, r):
        """Lista de puntos a distancia <= r de (qx, qy)."""
        resultado = []
        self.raiz.buscar_radio(qx, qy, r, resultado)
        return resultado

    def buscar_vecino(self, qx, qy):
        """
        Devuelve (punto mas cercano, distancia) a (qx, qy).
        Si el arbol esta vacio devuelve (None, inf).
        """
        mejor = [float('inf'), None]
        mejor = self.raiz.buscar_vecino(qx, qy, mejor)
        return mejor[1], mejor[0] ** 0.5


# ----------------------------------------------------------------------
# Fuerza bruta (referencia para verificar y comparar)
# ----------------------------------------------------------------------
def buscar_radio_bruta(puntos, qx, qy, r):
    """Puntos de la lista a distancia <= r de (qx, qy), recorriendolos todos."""
    resultado = []
    for p in puntos:
        if (p[0] - qx) ** 2 + (p[1] - qy) ** 2 <= r ** 2:
            resultado.append(p)
    return resultado


def vecino_bruto(puntos, qx, qy):
    """Devuelve (punto mas cercano, distancia) a (qx, qy), recorriendo todos los puntos."""
    mejor_d2 = float('inf')
    mejor_punto = None
    for p in puntos:
        d2 = (p[0] - qx) ** 2 + (p[1] - qy) ** 2
        if d2 < mejor_d2:
            mejor_d2 = d2
            mejor_punto = p
    return mejor_punto, mejor_d2 ** 0.5
