"""
Laboratorio 2 - Árbol de Merkle
Autor: Juan David Puerta Palacio

Especificaciones:
- Cada hoja = SHA-256 de un bloque de datos.
- Cada nodo interno = SHA-256 de la concatenación de sus dos hijos.
- Si un nivel tiene número impar de nodos, se duplica el último (convención Bitcoin).
- La raíz (Merkle Root) representa todo el conjunto de transacciones.

Este módulo:

  1. Guarda TODOS los niveles del árbol (no solo la raíz), para poder dibujarlo.
  2. Genera pruebas de inclusión (Merkle proof) para una transacción dada.
  3. Verifica una prueba de inclusión contra una raíz esperada.
  
"""

import hashlib


def hash_data(data: str) -> str:
    """Calcula el hash SHA-256 (hex) de un string."""
    return hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Clase MerkleTree: 
# ---------------------------------------------------------------------------
class MerkleTree:
    def __init__(self, transacciones: list[str]):
        if not transacciones:
            raise ValueError("Se necesita al menos una transacción")
        self.transacciones = list(transacciones)
        self.niveles: list[list[str]] = []
        self._construir()

    def _construir(self) -> None:
        """
        Construye todos los niveles del árbol, de hojas a raíz.
        Cuando un nivel tiene longitud impar (>1), se duplica el último
        hash y esa duplicación queda registrada en el nivel almacenado,
        para que los índices de las pruebas de inclusión sean consistentes.
        """
        nivel_actual = [hash_data(tx) for tx in self.transacciones]

        while True:
            if len(nivel_actual) % 2 != 0 and len(nivel_actual) > 1:
                nivel_actual = nivel_actual + [nivel_actual[-1]]

            self.niveles.append(nivel_actual)

            if len(nivel_actual) == 1:
                break

            nivel_siguiente = []
            for i in range(0, len(nivel_actual), 2):
                combinado = nivel_actual[i] + nivel_actual[i + 1]
                nivel_siguiente.append(hash_data(combinado))
            nivel_actual = nivel_siguiente

    @property
    def raiz(self) -> str:
        return self.niveles[-1][0]

    def generar_prueba(self, indice: int) -> list[tuple[str, str]]:
        """
        Genera la prueba de inclusión (Merkle proof) para la transacción
        en la posición `indice` (0-indexado).

        Devuelve una lista de tuplas (hash_hermano, lado), donde `lado`
        indica si el hermano va a la 'izquierda' o 'derecha' al combinar
        en ese nivel.
        """
        if indice < 0 or indice >= len(self.transacciones):
            raise IndexError("Índice de transacción fuera de rango")

        prueba = []
        idx = indice
        for nivel in self.niveles[:-1]:  # excluye la raíz
            if idx % 2 == 0:
                idx_hermano = idx + 1
                lado = "derecha"
            else:
                idx_hermano = idx - 1
                lado = "izquierda"
            prueba.append((nivel[idx_hermano], lado))
            idx //= 2
        return prueba

    @staticmethod
    def verificar_prueba(
        dato: str,
        prueba: list[tuple[str, str]],
        raiz_esperada: str,
    ) -> bool:
        """
        Reconstruye el camino hacia la raíz a partir del dato original
        y la prueba de inclusión, y compara contra la raíz esperada.
        """
        hash_actual = hash_data(dato)
        for hermano, lado in prueba:
            if lado == "derecha":
                hash_actual = hash_data(hash_actual + hermano)
            else:
                hash_actual = hash_data(hermano + hash_actual)
        return hash_actual == raiz_esperada

    def imprimir_arbol(self) -> None:
        """Dibuja el árbol en ASCII, nivel por nivel (hojas -> raíz)."""
        total_niveles = len(self.niveles)
        for i, nivel in enumerate(self.niveles):
            etiqueta = "RAÍZ" if i == total_niveles - 1 else f"Nivel {i}"
            print(f"{etiqueta} ({len(nivel)} nodo(s)):")
            for j, h in enumerate(nivel):
                print(f"   [{j}] {h[:16]}...")
            if i != total_niveles - 1:
                print("      |")
        print()


# ---------------------------------------------------------------------------
# Experimento pedido en el enunciado
# ---------------------------------------------------------------------------
def main():
    separador = "=" * 70

    print(separador)
    print("1. Crear 5 transacciones y construir el árbol")
    print(separador)
    transacciones = [
        "TX1: Juan paga 100000 a Pedro",
        "TX2: Pedro paga 50000 a Maria",
        "TX3: Maria paga 75000 a Carlos",
        "TX4: Carlos paga 20000 a Juan",
        "TX5: Ana paga 30000 a Pedro",
    ]

    arbol = MerkleTree(transacciones)
    print("Transacciones:")
    for i, tx in enumerate(transacciones):
        print(f"  [{i}] {tx}")

    print(f"\nMerkle Root: {arbol.raiz}\n")
    arbol.imprimir_arbol()

    print(separador)
    print("2. Modificar una transacción y demostrar que la raíz cambia")
    print(separador)
    raiz_original = arbol.raiz
    transacciones_modificadas = transacciones.copy()
    transacciones_modificadas[1] = "TX2: Pedro paga 999999 a Maria"  # dato alterado

    arbol_modificado = MerkleTree(transacciones_modificadas)
    print(f"Raíz original:  {raiz_original}")
    print(f"Raíz modificada: {arbol_modificado.raiz}")
    print(f"¿Son iguales? {raiz_original == arbol_modificado.raiz}\n")

    print(separador)
    print("3. Prueba de inclusión para la transacción 3 (índice 2)")
    print(separador)
    indice_tx3 = 2
    prueba_tx3 = arbol.generar_prueba(indice_tx3)
    print(f"Transacción: {transacciones[indice_tx3]}")
    print("Prueba de inclusión (hash hermano, lado):")
    for hermano, lado in prueba_tx3:
        print(f"  ({hermano[:16]}..., {lado})")

    print(separador)
    print("4. Verificación con el dato correcto (debe ser válida)")
    print(separador)
    es_valida = MerkleTree.verificar_prueba(
        transacciones[indice_tx3], prueba_tx3, arbol.raiz
    )
    print(f"Dato verificado: '{transacciones[indice_tx3]}'")
    print(f"Resultado: {'VÁLIDA ✔' if es_valida else 'INVÁLIDA ✘'}\n")

    print(separador)
    print("5. Verificación con un dato incorrecto (debe fallar)")
    print(separador)
    dato_incorrecto = "TX3: Maria paga 999999999 a Carlos"  # dato falso
    es_valida_incorrecta = MerkleTree.verificar_prueba(
        dato_incorrecto, prueba_tx3, arbol.raiz
    )
    print(f"Dato verificado: '{dato_incorrecto}'")
    print(f"Resultado: {'VÁLIDA ✔' if es_valida_incorrecta else 'INVÁLIDA ✘'}")


if __name__ == "__main__":
    main()
