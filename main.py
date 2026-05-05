"""
main.py — Punto de entrada principal del motor documental.

Ejecutar desde la raíz del proyecto:
    python main.py

Para las pruebas completas (14 consultas):
    python pruebas/pruebas_consultas.py
"""
import os

from src.coleccion import ColeccionDocumental
from src.arbol import ArbolDocumental


def main() -> None:
    print("╔══════════════════════════════════════════════════════╗")
    print("║   Mini Motor Documental — Inspirado en MongoDB      ║")
    print("║   Estructuras: Árboles + Listas Enlazadas           ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    # ── 1. Cargar documentos desde archivo ─────────────────────────
    ruta_datos = os.path.join("datos", "documentos.json")
    col = ColeccionDocumental("personas")
    col.cargar_desde_archivo(ruta_datos)

    # ── 2. Ver toda la colección ────────────────────────────────────
    print("\n[1] Colección completa:")
    col.imprimir_coleccion()

    # ── 3. Igualdad simple ──────────────────────────────────────────
    print("\n[2] Personas de Medellín:")
    r = col.find({"ciudad": "Medellín"})
    col.imprimir_resultados(r)

    # ── 4. Rango numérico ───────────────────────────────────────────
    print("\n[3] Personas con edad entre 18 y 30 años:")
    r = col.find({"edad": {"$gte": 18, "$lte": 30}})
    col.imprimir_resultados(r)

    # ── 5. Ruta anidada ─────────────────────────────────────────────
    print("\n[4] Personas del barrio Laureles:")
    r = col.find({"direccion.barrio": "Laureles"})
    col.imprimir_resultados(r)

    # ── 6. AND lógico ───────────────────────────────────────────────
    print("\n[5] Personas de Medellín mayores de 20 años:")
    r = col.find({"ciudad": "Medellín", "edad": {"$gt": 20}})
    col.imprimir_resultados(r)

    # ── 7. Visualización del árbol ──────────────────────────────────
    print("\n[6] Árbol del documento de Ana García:")
    raiz = col.find_one({"nombre": "Ana García"})
    if raiz:
        ArbolDocumental.visualizar(raiz)

    # ── 8. Conversión árbol → JSON ──────────────────────────────────
    print("\n[7] JSON reconstruido desde el árbol de Carlos Ruiz:")
    raiz = col.find_one({"nombre": "Carlos Ruiz"})
    if raiz:
        print(ArbolDocumental.a_json(raiz))

    print("\nPara ver las 14 pruebas completas, ejecuta:")
    print("    python pruebas/pruebas_consultas.py\n")


if __name__ == "__main__":
    main()
