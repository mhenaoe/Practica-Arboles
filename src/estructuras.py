"""
estructuras.py — Nodos y listas enlazadas del motor documental.

Clases definidas aquí:
    NodoHijo        → Enlace en la lista de hijos de un nodo del árbol
    ListaHijos      → Lista enlazada de hijos (reemplaza listas de Python)
    NodoArbol       → Nodo del árbol documental (clave + valor o hijos)
    NodoColeccion   → Enlace en la lista de documentos
    ListaDocumentos → Lista enlazada de documentos (reemplaza listas de Python)

NOTA sobre el orden de definición:
    NodoArbol necesita ListaHijos en su __init__ (la instancia).
    ListaHijos necesita NodoHijo.
    NodoHijo referencia NodoArbol solo en anotaciones de tipo.
    Con 'from __future__ import annotations' todas las anotaciones son
    strings perezosos, por lo que podemos anotar NodoArbol antes de
    definirla sin errores. El orden en este archivo es:
        NodoHijo → ListaHijos → NodoArbol → NodoColeccion → ListaDocumentos
"""
from __future__ import annotations

from typing import Iterator, Optional, Union

# Tipos de valores primitivos permitidos en un nodo hoja del árbol.
# Corresponden a: string, número entero, número flotante, booleano, null de JSON.
ValorPrimitivo = Union[str, int, float, bool, None]


# ══════════════════════════════════════════════════════════════════════
#  LISTA ENLAZADA DE HIJOS
# ══════════════════════════════════════════════════════════════════════

class NodoHijo:
    """
    Eslabón de la lista enlazada de hijos de un NodoArbol.

    Atributos:
        dato      → el NodoArbol hijo que representa este eslabón
        siguiente → puntero al siguiente NodoHijo (hermano), o None si es el último
    """

    def __init__(self, dato: NodoArbol) -> None:
        self.dato: NodoArbol = dato
        self.siguiente: Optional[NodoHijo] = None

    def __repr__(self) -> str:
        return f"NodoHijo({self.dato!r})"


class ListaHijos:
    """
    Lista enlazada de hijos de un NodoArbol.

    Reemplaza por completo las listas de Python para almacenar los hijos
    de un nodo del árbol documental.

    Mantiene un puntero 'cola' al último nodo para que cada inserción
    sea O(1) en lugar de O(k).

    Atributos:
        cabeza → primer NodoHijo de la lista (o None si está vacía)
        _cola  → último NodoHijo (uso interno para inserción O(1))
    """

    def __init__(self) -> None:
        self.cabeza: Optional[NodoHijo] = None
        self._cola: Optional[NodoHijo] = None

    def agregar(self, nodo: NodoArbol) -> None:
        """Agrega un NodoArbol al final de la lista en O(1)."""
        nuevo_enlace = NodoHijo(nodo)
        if self.cabeza is None:
            self.cabeza = nuevo_enlace
            self._cola = nuevo_enlace
        else:
            # _cola nunca es None si cabeza no lo es
            self._cola.siguiente = nuevo_enlace   # type: ignore[union-attr]
            self._cola = nuevo_enlace

    def esta_vacia(self) -> bool:
        """Retorna True si la lista no tiene hijos."""
        return self.cabeza is None

    def __iter__(self) -> Iterator[NodoArbol]:
        """Permite recorrer los hijos con un for-in."""
        actual = self.cabeza
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def __bool__(self) -> bool:
        return not self.esta_vacia()

    def __repr__(self) -> str:
        nodos = [repr(n) for n in self]
        return f"ListaHijos([{', '.join(nodos)}])"


# ══════════════════════════════════════════════════════════════════════
#  ÁRBOL DOCUMENTAL — NODO
# ══════════════════════════════════════════════════════════════════════

class NodoArbol:
    """
    Nodo de un árbol documental.

    Cada nodo representa una CLAVE del documento JSON.

    Dos tipos de nodo:
      - Nodo hoja  (es_objeto=False): tiene un valor primitivo (str, int,
                                      float, bool, None) y sin hijos.
      - Nodo objeto (es_objeto=True): representa un subobjeto JSON;
                                      su valor es None y sus hijos
                                      son los campos del subobjeto.

    La RAÍZ del árbol de un documento es un nodo especial con
    clave="" y es_objeto=True: actúa como contenedor de todos
    los campos de nivel superior.

    Atributos:
        clave     → nombre del campo JSON (vacío "" solo en la raíz)
        valor     → valor primitivo si es hoja, None si es objeto
        es_objeto → True si el nodo representa un objeto JSON anidado
        hijos     → ListaHijos con los campos hijos (vacía si es hoja)
    """

    def __init__(
        self,
        clave: str,
        valor: ValorPrimitivo = None,
        es_objeto: bool = False,
    ) -> None:
        self.clave: str = clave
        self.valor: ValorPrimitivo = valor
        self.es_objeto: bool = es_objeto
        self.hijos: ListaHijos = ListaHijos()

    def __repr__(self) -> str:
        if self.es_objeto:
            etiqueta = self.clave if self.clave else "RAIZ"
            return f"NodoArbol({etiqueta!r}, objeto)"
        return f"NodoArbol({self.clave!r}={self.valor!r})"


# ══════════════════════════════════════════════════════════════════════
#  LISTA ENLAZADA DE DOCUMENTOS
# ══════════════════════════════════════════════════════════════════════

class NodoColeccion:
    """
    Eslabón de la lista enlazada de documentos.

    Almacena la raíz del árbol de UN documento y el puntero
    al siguiente documento de la colección.

    Atributos:
        raiz      → NodoArbol raíz del árbol del documento
        siguiente → puntero al siguiente NodoColeccion, o None
    """

    def __init__(self, raiz: NodoArbol) -> None:
        self.raiz: NodoArbol = raiz
        self.siguiente: Optional[NodoColeccion] = None

    def __repr__(self) -> str:
        return f"NodoColeccion({self.raiz!r})"


class ListaDocumentos:
    """
    Lista enlazada de documentos de la colección.

    Reemplaza por completo las listas de Python para almacenar
    los documentos de la ColeccionDocumental.

    Cada elemento es un NodoColeccion que apunta a la raíz del
    árbol de un documento.

    Mantiene un puntero 'cola' al último nodo para inserción O(1).

    Atributos:
        cabeza   → primer NodoColeccion (o None si la lista está vacía)
        _cola    → último NodoColeccion (uso interno)
        _tamanio → contador de documentos
    """

    def __init__(self) -> None:
        self.cabeza: Optional[NodoColeccion] = None
        self._cola: Optional[NodoColeccion] = None
        self._tamanio: int = 0

    def agregar(self, raiz: NodoArbol) -> None:
        """Agrega la raíz de un árbol documental al final de la lista en O(1)."""
        nuevo_nodo = NodoColeccion(raiz)
        if self.cabeza is None:
            self.cabeza = nuevo_nodo
            self._cola = nuevo_nodo
        else:
            self._cola.siguiente = nuevo_nodo   # type: ignore[union-attr]
            self._cola = nuevo_nodo
        self._tamanio += 1

    def esta_vacia(self) -> bool:
        """Retorna True si la lista no contiene documentos."""
        return self.cabeza is None

    def tamanio(self) -> int:
        """Retorna la cantidad de documentos en la lista."""
        return self._tamanio

    def __iter__(self) -> Iterator[NodoArbol]:
        """Permite recorrer las raíces de los árboles con un for-in."""
        actual = self.cabeza
        while actual is not None:
            yield actual.raiz
            actual = actual.siguiente

    def __bool__(self) -> bool:
        return not self.esta_vacia()

    def __repr__(self) -> str:
        return f"ListaDocumentos({self._tamanio} documentos)"
