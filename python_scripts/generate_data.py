"""
generate_data.py — Generador de datos ficticios para DataFlow (Distribuidora Cuyo SRL)

Uso (desde la raíz del proyecto):
    python scripts/generate_data.py
    python scripts/generate_data.py --ventas 3000 --seed 7

Solo usa la librería estándar de Python (no hay que instalar nada).

Genera en data/raw/:
    clientes.csv, productos.csv, ventas.csv, compras.csv

Además genera data/ground_truth.json con la cantidad de errores inyectados
en cada archivo. Sirve como "clave de respuestas" para comprobar que tu
validador detecta todo. No lo mires hasta tener tu primera versión. :)
"""
import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

HOY = date.today()

# ----------------------------------------------------------------------------
# Datos base
# ----------------------------------------------------------------------------
UBICACIONES = {
    "Mendoza": ["Mendoza", "Godoy Cruz", "Guaymallén", "Las Heras", "Maipú",
                "Luján de Cuyo", "San Martín", "Rivadavia", "San Rafael"],
    "San Juan": ["San Juan", "Rawson", "Rivadavia", "Chimbas", "Pocito"],
    "San Luis": ["San Luis", "Villa Mercedes", "Merlo"],
    "Córdoba": ["Córdoba", "Villa María", "Río Cuarto"],
    "Buenos Aires": ["La Plata", "Mar del Plata", "Bahía Blanca"],
    "Santa Fe": ["Rosario", "Santa Fe", "Rafaela"],
}
# Pesos: la mayoría de los clientes están en Cuyo
PESOS_PROVINCIA = [40, 20, 10, 12, 10, 8]

TIPOS_COMERCIO = ["Supermercado", "Autoservicio", "Almacén", "Despensa",
                  "Minimercado", "Kiosco", "Distribuidora"]
APELLIDOS = ["García", "Rodríguez", "Fernández", "López", "Martínez", "Gómez",
             "Pérez", "Sánchez", "Romero", "Díaz", "Torres", "Ruiz", "Flores",
             "Acosta", "Benítez", "Molina", "Herrera", "Castro", "Ortiz", "Silva"]

PRODUCTOS = [
    # (nombre, categoría, precio base)
    ("Yerba Mate 1kg", "Almacén", 4200), ("Azúcar 1kg", "Almacén", 1500),
    ("Harina 000 1kg", "Almacén", 1100), ("Aceite Girasol 900ml", "Almacén", 2800),
    ("Fideos Spaghetti 500g", "Almacén", 1300), ("Arroz Largo Fino 1kg", "Almacén", 1900),
    ("Galletitas Dulces 300g", "Almacén", 1700), ("Café Molido 250g", "Almacén", 3900),
    ("Gaseosa Cola 2.25L", "Bebidas", 2600), ("Agua Mineral 2L", "Bebidas", 1000),
    ("Jugo en Polvo x10", "Bebidas", 900), ("Cerveza Lata 473ml", "Bebidas", 1800),
    ("Vino Malbec 750ml", "Bebidas", 5500), ("Vino Torrontés 750ml", "Bebidas", 4900),
    ("Detergente 750ml", "Limpieza", 2300), ("Lavandina 1L", "Limpieza", 1200),
    ("Jabón en Polvo 800g", "Limpieza", 3600), ("Papel Higiénico x4", "Limpieza", 2900),
    ("Shampoo 400ml", "Higiene", 3300), ("Jabón de Tocador x3", "Higiene", 2100),
    ("Dentífrico 90g", "Higiene", 1900), ("Leche Entera 1L", "Lácteos", 1600),
    ("Queso Cremoso kg", "Lácteos", 8200), ("Yogur Bebible 1L", "Lácteos", 2200),
    ("Dulce de Leche 400g", "Lácteos", 2700),
]

PROVEEDORES = ["Molinos del Oeste SA", "Bebidas Andinas SRL", "Lácteos La Pampa",
               "Limpieza Total SA", "Alimentos Cordilleranos", "Importadora Sur SRL"]


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def fecha_random(max_dias_atras: int) -> date:
    return HOY - timedelta(days=random.randint(1, max_dias_atras))


def redondear_50(x: float) -> int:
    return int(round(x / 50) * 50)


def escribir_csv(path: Path, campos: list, filas: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print(f"  ✔ {path}  ({len(filas)} filas)")


def repartir_indices(n_filas: int, cantidades: dict) -> dict:
    """Elige índices SIN solaparse para que cada fila tenga como mucho un error."""
    total = sum(cantidades.values())
    elegidos = random.sample(range(n_filas), total)
    out, i = {}, 0
    for nombre, c in cantidades.items():
        out[nombre] = elegidos[i:i + c]
        i += c
    return out


def fecha_mala(d: date) -> str:
    return random.choice([
        d.strftime("%d/%m/%Y"),       # formato distinto
        d.strftime("%d-%m-%y"),       # año de 2 dígitos
        "2026-13-45",                 # fecha imposible
        "ayer",                       # texto
        "",                           # vacía
    ])


# ----------------------------------------------------------------------------
# Generadores
# ----------------------------------------------------------------------------
def generar_clientes(n: int):
    filas = []
    for i in range(1, n + 1):
        prov = random.choices(list(UBICACIONES), weights=PESOS_PROVINCIA)[0]
        loc = random.choice(UBICACIONES[prov])
        ape = random.choice(APELLIDOS)
        nombre = f"{random.choice(TIPOS_COMERCIO)} {ape}"
        email = f"contacto{i}@{ape.lower().replace('í','i').replace('é','e').replace('á','a').replace('ó','o').replace('ñ','n')}.com.ar"
        filas.append({"id_cliente": i, "nombre": nombre, "provincia": prov,
                      "localidad": loc, "email": email})

    errores = {}
    idx = repartir_indices(len(filas), {"email_vacio": 3, "email_invalido": 3,
                                        "provincia_vacia": 2})
    for i in idx["email_vacio"]:
        filas[i]["email"] = ""
    for i in idx["email_invalido"]:
        filas[i]["email"] = filas[i]["email"].replace("@", "")
    for i in idx["provincia_vacia"]:
        filas[i]["provincia"] = ""
    errores.update({k: len(v) for k, v in idx.items()})

    # Duplicados exactos y duplicados con datos distintos (mismo id)
    dup_exactos = random.sample(filas, 3)
    dup_conflicto = random.sample(filas, 2)
    filas.extend(dict(f) for f in dup_exactos)
    for f in dup_conflicto:
        c = dict(f)
        c["nombre"] = c["nombre"] + " SRL"
        filas.append(c)
    errores["duplicados_exactos"] = 3
    errores["duplicados_con_conflicto"] = 2
    return filas, errores


def generar_productos():
    filas = [{"id_producto": i, "producto": n, "categoria": c, "precio": p}
             for i, (n, c, p) in enumerate(PRODUCTOS, start=1)]
    errores = {}
    idx = repartir_indices(len(filas), {"categoria_vacia": 1, "precio_negativo": 1,
                                        "precio_cero": 1})
    filas[idx["categoria_vacia"][0]]["categoria"] = ""
    filas[idx["precio_negativo"][0]]["precio"] = -abs(filas[idx["precio_negativo"][0]]["precio"])
    filas[idx["precio_cero"][0]]["precio"] = 0
    errores.update({k: len(v) for k, v in idx.items()})
    filas.append(dict(random.choice(filas)))  # 1 duplicado
    errores["duplicados_exactos"] = 1
    return filas, errores


def generar_ventas(n: int, n_clientes: int, productos_precio: dict):
    ids_prod = list(productos_precio)
    filas = []
    for k in range(n):
        id_prod = random.choice(ids_prod)
        base = productos_precio[id_prod]
        # Si el precio base del producto es inválido (error inyectado), usamos 1000
        base = base if base > 0 else 1000
        filas.append({
            "id_venta": 1001 + k,
            "fecha": fecha_random(60).isoformat(),
            "id_cliente": random.randint(1, n_clientes),
            "id_producto": id_prod,
            "cantidad": random.choice([1, 2, 5, 5, 10, 10, 12, 20, 24, 50]),
            "precio_unitario": redondear_50(base * random.uniform(0.95, 1.10)),
        })

    cantidades = {
        "fecha_invalida": 15, "producto_inexistente": 12, "cliente_inexistente": 10,
        "cantidad_negativa": 12, "cantidad_cero": 6, "campo_vacio": 12,
        "precio_invalido": 8,
    }
    idx = repartir_indices(len(filas), cantidades)
    errores = {k: len(v) for k, v in idx.items()}

    for i in idx["fecha_invalida"]:
        filas[i]["fecha"] = fecha_mala(date.fromisoformat(filas[i]["fecha"]))
    for i in idx["producto_inexistente"]:
        filas[i]["id_producto"] = random.choice([999, 0, 500])
    for i in idx["cliente_inexistente"]:
        filas[i]["id_cliente"] = random.choice([9999, 0, 777])
    for i in idx["cantidad_negativa"]:
        filas[i]["cantidad"] = -random.randint(1, 20)
    for i in idx["cantidad_cero"]:
        filas[i]["cantidad"] = 0
    for i in idx["campo_vacio"]:
        filas[i][random.choice(["id_cliente", "id_producto", "cantidad", "precio_unitario"])] = ""
    for i in idx["precio_invalido"]:
        filas[i]["precio_unitario"] = random.choice([-1500, 0])

    # IDs de venta repetidos: mitad copias exactas, mitad con datos distintos
    copias = random.sample(filas, 20)
    for j, f in enumerate(copias):
        c = dict(f)
        if j >= 10:  # conflicto: mismo id_venta, otra cantidad
            c["cantidad"] = random.randint(1, 30)
        filas.append(c)
    errores["id_venta_repetido_exacto"] = 10
    errores["id_venta_repetido_con_conflicto"] = 10

    random.shuffle(filas)  # los repetidos no aparecen todos al final
    return filas, errores


def generar_compras(n: int, productos_precio: dict):
    ids_prod = list(productos_precio)
    filas = []
    for k in range(n):
        id_prod = random.choice(ids_prod)
        base = productos_precio[id_prod]
        base = base if base > 0 else 1000
        filas.append({
            "id_compra": 5001 + k,
            "fecha": fecha_random(90).isoformat(),
            "proveedor": random.choice(PROVEEDORES),
            "id_producto": id_prod,
            "cantidad": random.choice([50, 100, 100, 200, 300, 500]),
            "costo_unitario": redondear_50(base * random.uniform(0.55, 0.75)),
        })
    idx = repartir_indices(len(filas), {"fecha_invalida": 6, "producto_inexistente": 5,
                                        "cantidad_negativa": 5, "proveedor_vacio": 4,
                                        "costo_invalido": 4})
    errores = {k: len(v) for k, v in idx.items()}
    for i in idx["fecha_invalida"]:
        filas[i]["fecha"] = fecha_mala(date.fromisoformat(filas[i]["fecha"]))
    for i in idx["producto_inexistente"]:
        filas[i]["id_producto"] = 888
    for i in idx["cantidad_negativa"]:
        filas[i]["cantidad"] = -random.randint(10, 100)
    for i in idx["proveedor_vacio"]:
        filas[i]["proveedor"] = ""
    for i in idx["costo_invalido"]:
        filas[i]["costo_unitario"] = random.choice([0, -800])
    copias = random.sample(filas, 5)
    filas.extend(dict(c) for c in copias)
    errores["id_compra_repetido_exacto"] = 5
    random.shuffle(filas)
    return filas, errores


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Genera CSV ficticios para DataFlow")
    ap.add_argument("--clientes", type=int, default=60)
    ap.add_argument("--ventas", type=int, default=1500)
    ap.add_argument("--compras", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42, help="misma semilla = mismos datos")
    ap.add_argument("--out", type=Path, default=Path("data/raw"))
    args = ap.parse_args()

    random.seed(args.seed)
    print(f"Generando datos (seed={args.seed}) en {args.out}/ ...")

    clientes, e_cli = generar_clientes(args.clientes)
    productos, e_prod = generar_productos()
    # Precios base para generar ventas/compras coherentes
    precios = {p["id_producto"]: p["precio"] for p in productos}

    ventas, e_ven = generar_ventas(args.ventas, args.clientes, precios)
    compras, e_com = generar_compras(args.compras, precios)

    escribir_csv(args.out / "clientes.csv",
                 ["id_cliente", "nombre", "provincia", "localidad", "email"], clientes)
    escribir_csv(args.out / "productos.csv",
                 ["id_producto", "producto", "categoria", "precio"], productos)
    escribir_csv(args.out / "ventas.csv",
                 ["id_venta", "fecha", "id_cliente", "id_producto", "cantidad",
                  "precio_unitario"], ventas)
    escribir_csv(args.out / "compras.csv",
                 ["id_compra", "fecha", "proveedor", "id_producto", "cantidad",
                  "costo_unitario"], compras)

    truth = {"seed": args.seed, "clientes": e_cli, "productos": e_prod,
             "ventas": e_ven, "compras": e_com}
    gt_path = args.out.parent / "ground_truth.json"
    gt_path.write_text(json.dumps(truth, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✔ {gt_path}  (clave de respuestas, no mirar todavía)")
    print("Listo.")


if __name__ == "__main__":
    main()
