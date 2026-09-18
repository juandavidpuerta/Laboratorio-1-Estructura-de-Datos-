# Laboratorio 2 — Árbol de Merkle

## Descripción

Implementación de un Árbol de Merkle en Python. Cada hoja contiene el hash
SHA-256 de un bloque de datos (transacción), cada nodo interno contiene el
hash SHA-256 de la concatenación de sus dos hijos, y si un nivel tiene un
número impar de nodos, el último se duplica (convención usada por Bitcoin).
La raíz (Merkle Root) representa la integridad de todo el conjunto de datos.

## Archivos

* `merkle\_tree.py`: implementación completa

  * `hash\_data`: hash SHA-256 de un string.
  * `construir\_merkle\_general`: versión simple que devuelve solo la raíz.
  * `MerkleTree`: clase que construye y guarda todos los niveles del árbol,
permite generar pruebas de inclusión y verificarlas.
  * `main()`: ejecuta el experimento completo del enunciado.

## Cómo ejecutar

```bash
python3 merkle\_tree.py
```

## Experimento realizado

1. **Construcción del árbol** con 5 transacciones simuladas, mostrando la
Merkle Root y el árbol completo en ASCII (hojas → raíz).
2. **Modificación de una transacción** (TX2) y verificación de que la raíz
cambia por completo (efecto avalancha de SHA-256).
3. **Prueba de inclusión (Merkle proof)** para la transacción 3 (índice 2):
se generan los hashes "hermanos" necesarios en cada nivel para reconstruir
el camino hasta la raíz.
4. **Verificación válida**: se reconstruye la raíz a partir del dato original
de TX3 y la prueba generada → coincide con la raíz real (`VÁLIDA`).
5. **Verificación inválida**: se repite el proceso con un dato alterado de
TX3 → la raíz reconstruida no coincide (`INVÁLIDA`), demostrando que la
prueba detecta manipulación de datos.

## Diagrama del árbol (ejemplo con 5 transacciones)

Como 5 es impar, el último hash se duplica en cada nivel donde sea necesario:

```
Nivel 0 (hojas):   h0   h1   h2   h3   h4   h4'   <- h4 duplicado
                    \\   /     \\   /     \\   /
Nivel 1:            h01       h23       h44'
                       \\        |        /  (44' se duplica también, 3 es impar)
                        \\       |       /
Nivel 2:              h0123           h4444'
                            \\          /
Nivel 3 (RAÍZ):          MERKLE ROOT
```

(El diagrama ASCII real y con hashes concretos se genera en la salida del
script, sección `imprimir\_arbol()`).

## Capturas de pantalla

> Pendiente: agregadas al repositorio

## Uso de IA Generativa



En el desarrollo de este laboratorio utilicé Claude (Anthropic) como herramienta de apoyo. A continuación detallo explícitamente en qué partes:



Diseño e implementación de la clase MerkleTree: partí de una función propia (construir\_merkle\_general) que solo calculaba la raíz del árbol. Con ayuda de la IA extendí esa lógica para almacenar todos los niveles del árbol, y para implementar la generación y verificación de pruebas de inclusión (generar\_prueba y verificar\_prueba).

Función de impresión del árbol en ASCII (imprimir\_arbol), usada para el diagrama del entregable.

Script del experimento (main()), que organiza los 5 pasos pedidos en el enunciado (construcción, modificación de una transacción, generación de prueba, verificación válida e inválida).

Redacción del README del repositorio.



No utilicé IA para la comprensión conceptual del algoritmo (estructura de árbol de Merkle, propiedad de duplicación en niveles impares, funcionamiento de una prueba de inclusión), la cual puedo explicar y sustentar en su totalidad, incluyendo el porqué de cada decisión de diseño en el código (por ejemplo, por qué se almacena el nivel de hojas con el hash duplicado en lugar de dejarlo aparte).



Soy responsable de comprender, defender y poder modificar cada línea de este código.

## Autor

Juan David Puerta Palacio

