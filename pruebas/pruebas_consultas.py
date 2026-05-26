"""
pruebas_consultas.py — Pruebas del motor documental.

Ejecutar desde la RAÍZ del proyecto:
    python pruebas/pruebas_consultas.py

Campos de los documentos: id, nombre, edad, ciudad, direccion.barrio, direccion.codigo_postal

Consultas cubiertas:
    1.  Igualdad simple              {"ciudad": "Medellín"}
    2.  Ruta anidada con punto       {"direccion.barrio": "Laureles"}
    3.  Operador $gt                 {"edad": {"$gt": 30}}
    4.  Rango con $gte y $lte        {"edad": {"$gte": 18, "$lte": 30}}
    5.  AND lógico (dos condiciones) {"ciudad": "Medellín", "edad": {"$gte": 18}}
    6.  Operador $ne                 {"ciudad": {"$ne": "Bogotá"}}
    7.  Operador $lt                 {"edad": {"$lt": 20}}
    8.  AND con ruta anidada         {"ciudad": "Medellín", "direccion.barrio": "Laureles"}
    9.  Filtro vacío (todos los docs) {}
    10. Campo inexistente            {"telefono": "123"}
    11. Resultado vacío (sin match)  {"edad": {"$gt": 100}}
    12. Error de tipo (advertencia)  {"nombre": {"$gt": 10}}
    13. Visualización del árbol      find_one + ArbolDocumental.visualizar
    14. Conversión árbol → JSON      find_one + ArbolDocumental.a_json
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from src.coleccion import ColeccionDocumental
from src.arbol import ArbolDocumental


def titulo(numero: int, descripcion: str) -> None:
    print(f"\n{'═' * 60}")
    print(f"  PRUEBA {numero}: {descripcion}")
    print(f"{'═' * 60}")


def cargar_coleccion() -> ColeccionDocumental:
    ruta_datos = os.path.join(_ROOT, "datos", "documentos.json")
    col = ColeccionDocumental("personas")
    col.cargar_desde_archivo(ruta_datos)
    return col


def prueba_01_igualdad_simple(col: ColeccionDocumental) -> None:
    titulo(1, 'Igualdad simple — {"ciudad": "Medellín"}')
    resultados = col.find({"ciudad": "Medellín"})
    col.imprimir_resultados(resultados, titulo='ciudad = "Medellín"')


def prueba_02_ruta_anidada(col: ColeccionDocumental) -> None:
    titulo(2, 'Ruta anidada — {"direccion.barrio": "Laureles"}')
    resultados = col.find({"direccion.barrio": "Laureles"})
    col.imprimir_resultados(resultados, titulo='direccion.barrio = "Laureles"')


def prueba_03_operador_gt(col: ColeccionDocumental) -> None:
    titulo(3, 'Operador $gt — {"edad": {"$gt": 30}}')
    resultados = col.find({"edad": {"$gt": 30}})
    col.imprimir_resultados(resultados, titulo="edad > 30")


def prueba_04_rango_gte_lte(col: ColeccionDocumental) -> None:
    titulo(4, 'Rango — {"edad": {"$gte": 18, "$lte": 30}}')
    resultados = col.find({"edad": {"$gte": 18, "$lte": 30}})
    col.imprimir_resultados(resultados, titulo="18 ≤ edad ≤ 30")


def prueba_05_and_dos_condiciones(col: ColeccionDocumental) -> None:
    titulo(5, 'AND lógico — {"ciudad": "Medellín", "edad": {"$gte": 18}}')
    resultados = col.find({"ciudad": "Medellín", "edad": {"$gte": 18}})
    col.imprimir_resultados(resultados, titulo='ciudad="Medellín" AND edad≥18')


def prueba_06_operador_ne(col: ColeccionDocumental) -> None:
    titulo(6, 'Operador $ne — {"ciudad": {"$ne": "Bogotá"}}')
    resultados = col.find({"ciudad": {"$ne": "Bogotá"}})
    col.imprimir_resultados(resultados, titulo="ciudad ≠ Bogotá")


def prueba_07_operador_lt(col: ColeccionDocumental) -> None:
    titulo(7, 'Operador $lt — {"edad": {"$lt": 20}}')
    resultados = col.find({"edad": {"$lt": 20}})
    col.imprimir_resultados(resultados, titulo="edad < 20")


def prueba_08_and_con_ruta_anidada(col: ColeccionDocumental) -> None:
    titulo(8, 'AND con ruta anidada — ciudad="Medellín" Y barrio="Laureles"')
    resultados = col.find({"ciudad": "Medellín", "direccion.barrio": "Laureles"})
    col.imprimir_resultados(resultados, titulo='ciudad="Medellín" AND barrio="Laureles"')


def prueba_09_filtro_vacio(col: ColeccionDocumental) -> None:
    titulo(9, "Filtro vacío {} — retorna TODOS los documentos")
    resultados = col.find({})
    col.imprimir_resultados(resultados, titulo="Todos los documentos")


def prueba_10_campo_inexistente(col: ColeccionDocumental) -> None:
    titulo(10, 'Campo inexistente — {"telefono": "123"}')
    print("  (ningún documento tiene el campo 'telefono')")
    resultados = col.find({"telefono": "123"})
    col.imprimir_resultados(resultados, titulo='telefono = "123"')


def prueba_11_sin_resultados(col: ColeccionDocumental) -> None:
    titulo(11, 'Sin resultados — {"edad": {"$gt": 100}}')
    print("  (ningún documento tiene edad > 100)")
    resultados = col.find({"edad": {"$gt": 100}})
    col.imprimir_resultados(resultados, titulo="edad > 100")


def prueba_12_error_de_tipo(col: ColeccionDocumental) -> None:
    titulo(12, 'Error de tipo (advertencia) — {"nombre": {"$gt": 10}}')
    print("  ($gt sobre un campo de texto → advertencia de tipo, no excepción)")
    resultados = col.find({"nombre": {"$gt": 10}})
    col.imprimir_resultados(resultados, titulo='nombre > 10 (tipo inválido)')


def prueba_13_visualizar_arbol(col: ColeccionDocumental) -> None:
    titulo(13, "Visualización del árbol de un documento")
    raiz = col.find_one({"nombre": "Lucía Herrera"})
    if raiz:
        print("  Árbol del documento de Lucía Herrera:")
        ArbolDocumental.visualizar(raiz)
    else:
        print("  Documento no encontrado.")


def prueba_14_conversion_arbol_json(col: ColeccionDocumental) -> None:
    titulo(14, "Conversión árbol → JSON (verificación de fidelidad)")
    raiz = col.find_one({"nombre": "Pedro Soto"})
    if raiz:
        print("  JSON reconstruido desde el árbol:")
        print(ArbolDocumental.a_json(raiz))
        print("  (debe ser idéntico al documento original en documentos.json)")
    else:
        print("  Documento no encontrado.")


def main() -> None:
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         PRUEBAS — DocuTree (MongoDB-like)               ║")
    print("╚══════════════════════════════════════════════════════════╝")

    col = cargar_coleccion()

    prueba_01_igualdad_simple(col)
    prueba_02_ruta_anidada(col)
    prueba_03_operador_gt(col)
    prueba_04_rango_gte_lte(col)
    prueba_05_and_dos_condiciones(col)
    prueba_06_operador_ne(col)
    prueba_07_operador_lt(col)
    prueba_08_and_con_ruta_anidada(col)
    prueba_09_filtro_vacio(col)
    prueba_10_campo_inexistente(col)
    prueba_11_sin_resultados(col)
    prueba_12_error_de_tipo(col)
    prueba_13_visualizar_arbol(col)
    prueba_14_conversion_arbol_json(col)

    print(f"\n{'═' * 60}")
    print("  Todas las pruebas ejecutadas.")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
