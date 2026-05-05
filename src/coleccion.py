"""
coleccion.py — Colección documental principal del motor.

Clase:
    ColeccionDocumental → almacena, carga y consulta documentos.

Interfaz pública:
    cargar_desde_json(datos)     → carga una lista de dicts (temporal)
    cargar_desde_archivo(ruta)   → lee un archivo JSON y carga los docs
    find(filtro)                 → retorna ListaDocumentos con coincidencias
    find_one(filtro)             → retorna el primer NodoArbol coincidente
    imprimir_resultados(lista)   → imprime documentos en formato JSON
    imprimir_coleccion()         → imprime toda la colección
    tamanio()                    → número de documentos

Regla de uso de dicts:
    Los dicts de Python solo se usan para:
      - leer el JSON de entrada (cargar_desde_json recibe list[dict])
      - reconstruir el JSON de salida (imprimir_resultados llama a a_dict)
    Internamente todo es árbol + listas enlazadas.
"""
from __future__ import annotations

import json
from typing import Optional

from src.estructuras import NodoArbol, ListaDocumentos
from src.arbol import ArbolDocumental
from src.motor_consultas import MotorConsultas


class ColeccionDocumental:
    """
    Colección de documentos almacenados como árboles en una lista enlazada.

    Inspirada en las colecciones de MongoDB. Internamente usa ListaDocumentos
    (lista enlazada propia) para almacenar las raíces de los árboles.

    Uso típico:
        col = ColeccionDocumental("personas")
        col.cargar_desde_archivo("datos/documentos.json")

        resultados = col.find({"ciudad": "Medellín", "edad": {"$gte": 18}})
        col.imprimir_resultados(resultados)
    """

    def __init__(self, nombre: str = "coleccion") -> None:
        self.nombre: str = nombre
        self.documentos: ListaDocumentos = ListaDocumentos()

    # ══════════════════════════════════════════════════════════════
    #  CARGA
    # ══════════════════════════════════════════════════════════════

    def cargar_desde_json(self, datos: list[dict]) -> None:
        """
        Carga una lista de diccionarios y construye los árboles internos.

        El argumento 'datos' (list[dict]) se usa solo durante la conversión;
        tras llamar a ArbolDocumental.desde_dict, el dict se descarta y
        el documento vive únicamente como árbol en la ListaDocumentos.

        Complejidad: O(N × M)
            N = número de documentos
            M = número promedio de campos por documento (contando anidados)

        Lanza:
            ValueError si la lista está vacía.
        """
        if not datos:
            raise ValueError(
                f"[{self.nombre}] La lista de documentos no puede estar vacía."
            )

        for doc_dict in datos:
            raiz = ArbolDocumental.desde_dict(doc_dict)   # dict → árbol
            self.documentos.agregar(raiz)                 # raíz → lista enlazada

        print(
            f"[{self.nombre}] {self.documentos.tamanio()} "
            f"documento(s) cargado(s) correctamente."
        )

    def cargar_desde_archivo(self, ruta_archivo: str) -> None:
        """
        Lee un archivo JSON y carga los documentos en la colección.

        El archivo debe contener una lista de objetos JSON ([ {...}, {...}, ... ]).

        Lanza:
            FileNotFoundError si el archivo no existe.
            ValueError        si el JSON no es una lista.
        """
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            datos_raw = json.load(archivo)           # dict/list temporal, permitido

        if not isinstance(datos_raw, list):
            raise ValueError(
                f"[{self.nombre}] El archivo debe contener una lista JSON "
                f"de documentos, pero se encontró: {type(datos_raw).__name__}."
            )

        self.cargar_desde_json(datos_raw)

    # ══════════════════════════════════════════════════════════════
    #  CONSULTAS
    # ══════════════════════════════════════════════════════════════

    def find(self, filtro: dict) -> ListaDocumentos:
        """
        Retorna todos los documentos que cumplen el filtro (AND lógico).

        El filtro puede contener:
            Igualdad simple:    {"ciudad": "Medellín"}
            Ruta anidada:       {"direccion.barrio": "Laureles"}
            Operadores:         {"edad": {"$gt": 25}}
            Múltiples conds:    {"ciudad": "Medellín", "edad": {"$gte": 18}}
            Filtro vacío:       {}  →  retorna todos los documentos

        Complejidad: O(N × C × k × b)
            N = número de documentos en la colección
            C = número de condiciones en el filtro
            k = profundidad de la ruta más larga
            b = número máximo de hijos por nodo (ancho del árbol)

        Retorna:
            ListaDocumentos con los NodoArbol raíz de los docs coincidentes.
            Lista vacía si no hay coincidencias.
        """
        if self.documentos.esta_vacia():
            print(
                f"[{self.nombre}] La colección está vacía. "
                f"Carga documentos antes de consultar."
            )
            return ListaDocumentos()

        resultados = ListaDocumentos()
        for raiz in self.documentos:
            if MotorConsultas.cumple_filtro(raiz, filtro):
                resultados.agregar(raiz)

        return resultados

    def find_one(self, filtro: dict) -> Optional[NodoArbol]:
        """
        Retorna el primer documento que cumpla el filtro, o None.

        Útil para buscar un documento específico sin recorrer toda la colección.
        find_one({}) retorna el primer documento de la colección.
        """
        if self.documentos.esta_vacia():
            return None

        for raiz in self.documentos:
            if MotorConsultas.cumple_filtro(raiz, filtro):
                return raiz

        return None

    # ══════════════════════════════════════════════════════════════
    #  SALIDA / IMPRESIÓN
    # ══════════════════════════════════════════════════════════════

    def imprimir_resultados(
        self,
        resultados: ListaDocumentos,
        titulo: str = "",
    ) -> None:
        """
        Imprime los documentos de 'resultados' en formato JSON legible.

        Cada árbol se reconstruye a dict (temporal) solo para imprimirlo.
        Si 'resultados' está vacío, imprime un mensaje informativo.
        """
        cabecera = f"[{titulo}] " if titulo else ""

        if resultados.esta_vacia():
            print(f"{cabecera}Sin resultados encontrados.")
            return

        print(f"\n{cabecera}{resultados.tamanio()} resultado(s):")
        print("─" * 52)
        for i, raiz in enumerate(resultados, start=1):
            doc_dict = ArbolDocumental.a_dict(raiz)   # árbol → dict temporal para JSON
            print(f"[{i}] {json.dumps(doc_dict, ensure_ascii=False, indent=4)}")
        print("─" * 52)

    def imprimir_coleccion(self) -> None:
        """Imprime todos los documentos de la colección."""
        print(f"\n=== Colección: '{self.nombre}' ({self.documentos.tamanio()} docs) ===")
        self.imprimir_resultados(self.documentos, titulo=self.nombre)

    def tamanio(self) -> int:
        """Retorna el número de documentos almacenados en la colección."""
        return self.documentos.tamanio()
