"""
arbol.py — Conversión entre diccionario Python y árbol documental.

Clase:
    ArbolDocumental → métodos estáticos para construir y reconstruir árboles.

Regla de uso de dicts:
    Los diccionarios de Python SOLO se usan de forma temporal en:
      - desde_dict(datos: dict)  → entrada: el dict se lee y se descarta
      - a_dict(raiz)             → salida: el dict se construye solo al final
    La estructura interna siempre es árbol + listas enlazadas.

Estructura del árbol resultante:
    Raíz (clave="", es_objeto=True)
    ├── NodoArbol(clave="nombre",    valor="Ana")
    ├── NodoArbol(clave="edad",      valor=28)
    └── NodoArbol(clave="direccion", es_objeto=True)
        ├── NodoArbol(clave="barrio", valor="Laureles")
        └── NodoArbol(clave="calle",  valor="45B")
"""
from __future__ import annotations

import json

from src.estructuras import NodoArbol, ValorPrimitivo


class ArbolDocumental:
    """
    Gestiona la conversión entre diccionario Python y árbol documental.

    Todos los métodos son estáticos porque la clase no necesita estado
    propio: es una colección de funciones de transformación.
    """

    # ── Construcción: dict → árbol ─────────────────────────────────

    @staticmethod
    def desde_dict(datos: dict) -> NodoArbol:
        """
        Convierte un diccionario Python en un árbol documental.

        El diccionario 'datos' se usa solo para leer los pares clave-valor;
        a partir de ahí se construyen NodoArbol enlazados con ListaHijos.

        Retorna:
            NodoArbol raíz con clave="" y es_objeto=True.
            Todos los campos de 'datos' son hijos directos de la raíz.
        """
        raiz = NodoArbol(clave="", es_objeto=True)
        ArbolDocumental._poblar_nodo(raiz, datos)
        return raiz

    @staticmethod
    def _poblar_nodo(nodo_padre: NodoArbol, datos: dict) -> None:
        """
        Agrega recursivamente los campos de 'datos' como hijos de 'nodo_padre'.

        Casos:
            valor es dict  → crea un nodo con es_objeto=True y recursión
            valor es primitivo → crea un nodo hoja con el valor directo
        """
        for clave, valor in datos.items():
            if isinstance(valor, dict):
                # Objeto anidado: nodo contenedor, los valores van como hijos
                hijo = NodoArbol(clave=clave, es_objeto=True)
                ArbolDocumental._poblar_nodo(hijo, valor)
            else:
                # Valor primitivo: nodo hoja (str, int, float, bool, None)
                hijo = NodoArbol(clave=clave, valor=valor, es_objeto=False)
            nodo_padre.hijos.agregar(hijo)

    # ── Reconstrucción: árbol → dict ───────────────────────────────

    @staticmethod
    def a_dict(raiz: NodoArbol) -> dict:
        """
        Reconstruye el diccionario Python equivalente a partir del árbol.

        Itera los hijos del nodo:
            - Si el hijo es objeto → recursión (subobjeto)
            - Si el hijo es hoja   → agrega clave: valor al dict de salida

        El dict resultado es temporal y se usa solo para serializar a JSON.

        Complejidad: O(M) donde M = número total de nodos en el árbol.
        """
        resultado: dict = {}
        for hijo in raiz.hijos:
            if hijo.es_objeto:
                resultado[hijo.clave] = ArbolDocumental.a_dict(hijo)
            else:
                resultado[hijo.clave] = hijo.valor
        return resultado

    @staticmethod
    def a_json(raiz: NodoArbol, indent: int = 2) -> str:
        """Serializa el árbol directamente a string JSON con formato legible."""
        return json.dumps(
            ArbolDocumental.a_dict(raiz),
            ensure_ascii=False,
            indent=indent,
        )

    # ── Visualización del árbol (debug) ────────────────────────────

    @staticmethod
    def visualizar(raiz: NodoArbol, nivel: int = 0) -> None:
        """
        Imprime el árbol con indentación para mostrar su estructura.

        Ejemplo de salida:
            [RAIZ]
              nombre: 'Ana'
              edad: 28
              [direccion]
                barrio: 'Laureles'
                calle: '45B'
        """
        sangria = "  " * nivel
        if raiz.es_objeto:
            etiqueta = raiz.clave if raiz.clave else "RAIZ"
            print(f"{sangria}[{etiqueta}]")
        else:
            print(f"{sangria}{raiz.clave}: {raiz.valor!r}")

        for hijo in raiz.hijos:
            ArbolDocumental.visualizar(hijo, nivel + 1)
