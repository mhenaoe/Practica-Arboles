"""
motor_consultas.py — Lógica de filtrado y operadores de comparación.

Clase:
    MotorConsultas → métodos estáticos para navegar el árbol y evaluar filtros.

Operadores soportados:
    $eq   igual
    $ne   diferente
    $gt   mayor que
    $gte  mayor o igual que
    $lt   menor que
    $lte  menor o igual que

Notación de ruta:
    Las claves del filtro pueden ser simples ("ciudad") o rutas con punto
    ("direccion.barrio") para acceder a campos de objetos anidados.

Lógica AND:
    Todas las condiciones de un filtro deben cumplirse simultáneamente
    (AND lógico), igual que en MongoDB.
"""
from __future__ import annotations

from typing import Any, Tuple

from src.estructuras import NodoArbol

# Conjunto inmutable de operadores válidos (frozenset para O(1) de búsqueda)
OPERADORES_VALIDOS: frozenset[str] = frozenset({"$eq", "$ne", "$gt", "$gte", "$lt", "$lte"})


class MotorConsultas:
    """
    Motor de consultas del sistema documental.

    Responsabilidades:
      1. Navegar el árbol por ruta con notación de punto.
      2. Aplicar operadores de comparación sobre valores primitivos.
      3. Evaluar si un documento cumple un filtro completo (AND lógico).
    """

    # ── 1. Navegación por ruta ─────────────────────────────────────

    @staticmethod
    def buscar_por_ruta(raiz: NodoArbol, ruta: str) -> Tuple[bool, Any]:
        """
        Navega el árbol siguiendo los segmentos de 'ruta' separados por punto.

        Ejemplo: ruta="direccion.barrio"
            raiz → buscar hijo "direccion" → buscar hijo "barrio" → valor

        Complejidad: O(k × b)
            k = número de segmentos en la ruta
            b = número máximo de hijos por nodo (ancho del árbol)

        Retorna:
            (True,  valor)          si la ruta existe y el nodo final es hoja
            (True,  "[objeto]")     si la ruta existe pero el nodo es objeto
            (False, None)           si algún segmento de la ruta no existe
        """
        segmentos = ruta.split(".")
        nodo_actual = raiz

        for segmento in segmentos:
            encontrado = False
            for hijo in nodo_actual.hijos:
                if hijo.clave == segmento:
                    nodo_actual = hijo
                    encontrado = True
                    break
            if not encontrado:
                return False, None

        # La ruta existe. ¿Es un nodo hoja o un objeto?
        if nodo_actual.es_objeto and nodo_actual.clave != "":
            return True, "[objeto]"

        return True, nodo_actual.valor

    # ── 2. Operadores de comparación ──────────────────────────────

    @staticmethod
    def aplicar_operador(valor: Any, operador: str, operando: Any) -> bool:
        """
        Aplica 'operador' entre el valor del documento y el operando del filtro.

        Restricciones de tipo:
            $gt, $gte, $lt, $lte → solo sobre valores numéricos (int o float).
            Aplica a None, str, bool con operadores numéricos → TypeError.

        Lanza:
            TypeError  si los tipos no son compatibles con el operador
            ValueError si el operador no es reconocido
        """
        if operador not in OPERADORES_VALIDOS:
            raise ValueError(
                f"Operador {operador!r} no reconocido. "
                f"Operadores válidos: {sorted(OPERADORES_VALIDOS)}"
            )

        # Los operadores de orden requieren números. bool hereda de int
        # (True==1, False==0) así que se permite intencionalmente.
        if operador in {"$gt", "$gte", "$lt", "$lte"}:
            valor_numerico = isinstance(valor, (int, float)) and not isinstance(valor, bool)
            operando_numerico = isinstance(operando, (int, float)) and not isinstance(operando, bool)
            if not valor_numerico or not operando_numerico:
                raise TypeError(
                    f"El operador {operador!r} solo acepta números. "
                    f"Valor del documento: {type(valor).__name__} = {valor!r}. "
                    f"Operando del filtro: {type(operando).__name__} = {operando!r}."
                )

        if operador == "$eq":
            return valor == operando
        elif operador == "$ne":
            return valor != operando
        elif operador == "$gt":
            return valor > operando       # type: ignore[operator]
        elif operador == "$gte":
            return valor >= operando      # type: ignore[operator]
        elif operador == "$lt":
            return valor < operando       # type: ignore[operator]
        else:  # "$lte"
            return valor <= operando      # type: ignore[operator]

    # ── 3. Evaluación de condiciones y filtros ────────────────────

    @staticmethod
    def evaluar_condicion(raiz: NodoArbol, ruta: str, condicion: Any) -> bool:
        """
        Evalúa una condición sobre el campo indicado por 'ruta'.

        Dos formas de condición:
            Valor directo  → {"ciudad": "Medellín"}       (equivale a $eq)
            Dict operadores→ {"edad": {"$gt": 25, "$lte": 40}}  (AND entre operadores)

        Si la ruta no existe en el documento → retorna False.
        Si hay error de tipo en el operador  → advertencia + retorna False.
        """
        encontrado, valor = MotorConsultas.buscar_por_ruta(raiz, ruta)

        if not encontrado:
            return False

        # Condición directa: igualdad implícita ($eq)
        if not isinstance(condicion, dict):
            return valor == condicion

        # Condición con operadores: todos deben cumplirse (AND entre operadores)
        for operador, operando in condicion.items():
            try:
                if not MotorConsultas.aplicar_operador(valor, operador, operando):
                    return False
            except TypeError as exc:
                print(f"  [Advertencia de tipo] {exc}")
                return False
            except ValueError as exc:
                print(f"  [Operador inválido] {exc}")
                return False

        return True

    @staticmethod
    def cumple_filtro(raiz: NodoArbol, filtro: dict) -> bool:
        """
        Verifica si un documento cumple TODAS las condiciones del filtro.

        Lógica AND: si alguna condición falla, retorna False inmediatamente.
        Filtro vacío {} → coincide con todos los documentos (como en MongoDB).

        Complejidad: O(C × k × b)
            C = número de condiciones en el filtro
            k = profundidad de la ruta más larga
            b = número máximo de hijos por nodo
        """
        for ruta, condicion in filtro.items():
            if not MotorConsultas.evaluar_condicion(raiz, ruta, condicion):
                return False
        return True
