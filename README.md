# Mini Motor Documental — Inspirado en MongoDB

Implementación de un motor documental usando **árboles** y **listas enlazadas** propias.
No se usan listas de Python para la colección ni para los hijos de los nodos.

---

## Estructura del proyecto

```
Practica_Arboles/
├── src/
│   ├── __init__.py            # Descripción del paquete
│   ├── estructuras.py         # Nodos y listas enlazadas (clases base)
│   ├── arbol.py               # Conversión JSON ↔ árbol documental
│   ├── motor_consultas.py     # Operadores y lógica de filtrado
│   └── coleccion.py           # ColeccionDocumental con find()
├── datos/
│   └── documentos.json        # 8 documentos de prueba
├── pruebas/
│   └── pruebas_consultas.py   # 14 consultas de prueba
├── main.py                    # Punto de entrada rápido
└── README.md                  # Este archivo
```

---

## Cómo ejecutar

```bash
# Desde la carpeta raíz del proyecto:
python main.py

# Para las 14 pruebas completas:
python pruebas/pruebas_consultas.py
```

---

## Modelo de clases

### `estructuras.py` — Clases base (nodos y listas)

```
NodoHijo
    dato: NodoArbol          → el hijo que representa este eslabón
    siguiente: NodoHijo|None → puntero al hermano siguiente

ListaHijos
    cabeza: NodoHijo|None    → primer hijo
    _cola:  NodoHijo|None    → último hijo (para inserción O(1))
    agregar(nodo)            → O(1), agrega al final
    __iter__()               → itera todos los hijos

NodoArbol
    clave: str               → nombre del campo JSON
    valor: str|int|float|bool|None  → valor si es hoja
    es_objeto: bool          → True si el nodo tiene hijos (subobjeto)
    hijos: ListaHijos        → hijos del nodo (vacía si es hoja)

    La RAÍZ de cada árbol tiene clave="" y es_objeto=True.

NodoColeccion
    raiz: NodoArbol          → raíz del árbol de un documento
    siguiente: NodoColeccion|None  → puntero al siguiente documento

ListaDocumentos
    cabeza: NodoColeccion|None
    _cola:  NodoColeccion|None  → inserción O(1)
    _tamanio: int
    agregar(raiz)            → O(1)
    tamanio()                → O(1)
    __iter__()               → itera todas las raíces
```

### `arbol.py` — Conversión JSON ↔ árbol

```
ArbolDocumental (métodos estáticos)
    desde_dict(datos: dict) → NodoArbol
        Construye el árbol desde un dict. El dict es temporal.

    a_dict(raiz: NodoArbol) → dict
        Reconstruye el dict desde el árbol. El dict es solo para salida.

    a_json(raiz: NodoArbol) → str
        Serializa el árbol a string JSON.

    visualizar(raiz, nivel) → None
        Imprime el árbol con indentación (útil para debug).
```

### `motor_consultas.py` — Filtrado

```
MotorConsultas (métodos estáticos)
    buscar_por_ruta(raiz, ruta) → (bool, Any)
        Navega el árbol siguiendo la ruta "campo.subcampo".
        Retorna (encontrado, valor).

    aplicar_operador(valor, operador, operando) → bool
        Evalúa: valor $gt operando, valor $eq operando, etc.
        Lanza TypeError para operadores numéricos sobre no-números.

    evaluar_condicion(raiz, ruta, condicion) → bool
        Combina buscar_por_ruta + aplicar_operador.
        condicion puede ser un valor directo o un dict de operadores.

    cumple_filtro(raiz, filtro) → bool
        AND lógico de todas las condiciones del filtro.
```

### `coleccion.py` — Colección principal

```
ColeccionDocumental
    nombre: str
    documentos: ListaDocumentos

    cargar_desde_json(datos: list[dict])
    cargar_desde_archivo(ruta: str)
    find(filtro: dict) → ListaDocumentos
    find_one(filtro: dict) → NodoArbol | None
    imprimir_resultados(resultados, titulo)
    imprimir_coleccion()
    tamanio() → int
```

---

## Decisiones de diseño

### 1. Por qué todas las clases base en un solo archivo (`estructuras.py`)
`NodoArbol` necesita instanciar `ListaHijos` en su `__init__`.
`ListaHijos` necesita `NodoHijo`. `NodoHijo` anota `NodoArbol`.
Esta dependencia circular se resuelve con `from __future__ import annotations`
(anotaciones como strings) y definiendo las clases en el orden:
`NodoHijo → ListaHijos → NodoArbol → NodoColeccion → ListaDocumentos`.

### 2. Puntero `_cola` para inserción O(1)
Sin `_cola`, cada `agregar()` recorre toda la lista: O(k).
Con `_cola`, se inserta directo al final: O(1).
Esto es importante cuando se cargan muchos documentos o un documento tiene muchos campos.

### 3. Nodo raíz con `clave=""`
La raíz es un nodo centinela (clave vacía, es_objeto=True).
Los campos de nivel superior son sus hijos directos.
Esto simplifica `buscar_por_ruta`: siempre se empieza desde la raíz
y se busca el primer segmento entre sus hijos.

### 4. `ValorPrimitivo = Union[str, int, float, bool, None]`
Mapea directamente los tipos JSON primitivos a Python.
`bool` es subclase de `int` en Python, pero se excluye explícitamente
de los operadores numéricos (`$gt`, `$gte`, `$lt`, `$lte`) para evitar
comparaciones inesperadas como `True > 0`.

### 5. Uso permitido de dicts
Los dicts de Python solo se usan en:
- **Entrada**: `json.load()` en `cargar_desde_archivo` y el argumento de `find(filtro)`.
- **Salida**: `a_dict()` y `json.dumps()` en `imprimir_resultados`.
Toda la lógica interna (construcción, búsqueda, comparación) opera sobre árboles y listas enlazadas.

---

## Análisis de complejidad

### Variables
- `N` = número de documentos en la colección
- `M` = número total de nodos por documento (campos + subcampos)
- `C` = número de condiciones en el filtro
- `k` = profundidad de la ruta (segmentos separados por punto)
- `b` = número máximo de hijos por nodo (ancho del árbol)

### Carga de documentos — `cargar_desde_json`

| Operación                        | Complejidad  |
|----------------------------------|-------------|
| Construir árbol de 1 documento   | O(M)        |
| Cargar N documentos              | O(N × M)    |
| Agregar cada raíz a la lista     | O(1) por doc (con puntero _cola) |
| **Total carga**                  | **O(N × M)** |

### Búsqueda por ruta — `buscar_por_ruta`

En cada nivel se recorre la ListaHijos linealmente hasta encontrar la clave.

| Caso             | Complejidad  |
|------------------|-------------|
| Mejor caso       | O(k)        | (la clave buscada siempre es la primera hija)
| Peor caso        | O(k × b)    | (la clave siempre está al final de cada nivel)
| **Caso promedio**| **O(k × b/2) ≈ O(k × b)** |

> Para documentos típicos con pocos campos, `b` es pequeño (3-10) y la búsqueda es muy rápida.

### Consulta sobre la colección — `find`

Se evalúa cada documento contra el filtro:

| Operación               | Complejidad          |
|-------------------------|---------------------|
| Evaluar 1 condición     | O(k × b)            |
| Evaluar filtro completo | O(C × k × b)        |
| Consultar N documentos  | O(N × C × k × b)    |
| **Total find()**        | **O(N × C × k × b)**|

> En la práctica `C`, `k`, y `b` son pequeños y constantes, por lo que `find()` es efectivamente **O(N)**.

### Conversión árbol → JSON — `a_dict`

Se visita cada nodo exactamente una vez:

| Operación       | Complejidad |
|-----------------|------------|
| 1 documento     | O(M)       |
| N documentos    | O(N × M)   |
| **Total**       | **O(M)**   |

---

## Operadores soportados

| Operador | Descripción        | Ejemplo                          |
|----------|--------------------|----------------------------------|
| `$eq`    | igual (implícito)  | `{"ciudad": "Medellín"}`         |
| `$ne`    | diferente          | `{"ciudad": {"$ne": "Bogotá"}}`  |
| `$gt`    | mayor que          | `{"edad": {"$gt": 30}}`          |
| `$gte`   | mayor o igual      | `{"edad": {"$gte": 18}}`         |
| `$lt`    | menor que          | `{"puntuacion": {"$lt": 80}}`    |
| `$lte`   | menor o igual      | `{"edad": {"$lte": 65}}`         |

---

## Ejemplos de consultas

```python
from src.coleccion import ColeccionDocumental

col = ColeccionDocumental("personas")
col.cargar_desde_archivo("datos/documentos.json")

# Igualdad simple
col.find({"ciudad": "Medellín"})

# Ruta anidada
col.find({"direccion.barrio": "Laureles"})

# Rango numérico
col.find({"edad": {"$gte": 18, "$lte": 30}})

# AND lógico (múltiples condiciones)
col.find({"ciudad": "Medellín", "activo": True, "puntuacion": {"$gte": 90}})

# Diferente
col.find({"ciudad": {"$ne": "Bogotá"}})
```
