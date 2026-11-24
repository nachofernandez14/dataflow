# DataFlow — Sistema de procesamiento de ventas empresariales

> Proyecto práctico de Data Engineering · Nivel intermedio · Modo mixto (explicación + desafío + revisión)
> Stack: Docker · Docker Compose · Python · Pandas · SQLAlchemy · PostgreSQL

---

## 1. Contexto

**Distribuidora Cuyo SRL** vende productos a supermercados y comercios chicos. Cada área exporta sus datos en CSV, sin ningún control de calidad. La gerencia necesita todo centralizado en PostgreSQL para analizar el negocio.

**Tu rol:** Data Engineer. Tenés que construir un pipeline ETL que reciba los archivos, los valide, separe lo bueno de lo malo y cargue los datos limpios en la base, sin duplicarlos si el proceso se corre dos veces.

```
CSV (ventas, clientes, productos, compras)
        │
        ▼
Python + Pandas  →  extraer · limpiar · validar · transformar
        │                         │
        ▼                         ▼
PostgreSQL (datos válidos)   data/rejected/ (registros rechazados + motivo)
        │
        ▼
Consultas SQL (reportes y métricas)
```

---

## 2. Objetivos de aprendizaje

- Orquestar servicios con Docker Compose.
- Diseñar un modelo relacional con claves y restricciones.
- Escribir un ETL modular, testeable y con logs.
- Validar datos "sucios" y justificar decisiones sobre cada tipo de error.
- Cargar de forma **idempotente** (correr el pipeline N veces = mismo resultado).
- Documentar el proyecto como para mostrarlo en una entrevista.

---

## 3. Funcionalidades obligatorias

Marcá cada una cuando la tengas funcionando.

### Etapa 1 · Infraestructura
- [ ] Estructura de carpetas del repositorio.
- [ ] `docker-compose.yml` con servicio `db` (PostgreSQL) y servicio `etl` (Python).
- [ ] `Dockerfile` para el servicio de Python.
- [ ] Credenciales en `.env` (y `.env.example` versionado, **sin** secretos).
- [ ] Volumen persistente para PostgreSQL.
- [ ] `healthcheck` en la base: el ETL no arranca hasta que Postgres esté listo.
- [ ] Poder conectarte a la base (`psql` o DBeaver) y ejecutar SQL.
- [ ] `.gitignore` correcto (`.env`, `logs/`, `data/raw/*.csv`, `__pycache__/`, etc.).

### Etapa 2 · Extracción
- [ ] Generar los CSV (ver sección 6).
- [ ] `extract.py`: función que lee cada CSV a un DataFrame.
- [ ] Leer todo como texto (`dtype=str`) y convertir recién en la transformación, para no perder información de los errores.
- [ ] Inspección inicial: `shape`, `dtypes`, nulos por columna, duplicados.
- [ ] Manejo de archivo inexistente, vacío o con columnas faltantes.

### Etapa 3 · Transformación y validación
- [ ] Normalizar texto (espacios, mayúsculas/minúsculas, nombres de provincia).
- [ ] Convertir tipos (fechas, enteros, decimales).
- [ ] Aplicar las reglas de validación de la sección 4.
- [ ] Separar en **válidos** y **rechazados**.
- [ ] Cada registro rechazado guarda el **motivo** (`motivo_rechazo`).
- [ ] Guardar rechazados en `data/rejected/<entidad>_rechazados.csv`.
- [ ] Guardar válidos transformados en `data/processed/`.
- [ ] Resumen por archivo: total leído, válidos, rechazados, rechazados por motivo.

### Etapa 4 · Carga en PostgreSQL
- [ ] `sql/schema.sql` con tablas: `clientes`, `productos`, `ventas`, `compras`.
- [ ] Claves primarias y foráneas.
- [ ] Restricciones: `NOT NULL`, `CHECK (cantidad > 0)`, `CHECK (precio > 0)`, `UNIQUE` donde corresponda.
- [ ] Índices en columnas de consulta frecuente (`fecha`, `id_cliente`, `id_producto`).
- [ ] Orden de carga que respete las dependencias (primero dimensiones, después hechos).
- [ ] Carga dentro de **transacciones**: si falla algo, rollback.
- [ ] **Idempotencia**: correr dos veces no duplica registros (`INSERT ... ON CONFLICT`).
- [ ] Tabla de auditoría `etl_runs` (ver sección 5).

### Etapa 5 · Análisis (consultas SQL en `sql/queries/`)
- [ ] Facturación diaria.
- [ ] Facturación mensual y variación % contra el mes anterior.
- [ ] Top 10 productos más vendidos (por unidades y por facturación).
- [ ] Top 10 clientes por facturación.
- [ ] Ventas por provincia y por localidad.
- [ ] Ventas por categoría de producto.
- [ ] Margen estimado: ventas vs. costo promedio de compras por producto.
- [ ] Clientes sin compras en los últimos 30 días.
- [ ] Al menos 2 consultas con **CTE** y 2 con **funciones de ventana** (`ROW_NUMBER`, `SUM() OVER`, `LAG`).
- [ ] Una **vista** (`CREATE VIEW`) con el resumen de ventas para reportes.

### Etapa 6 · Automatización y robustez
- [ ] `main.py` ejecuta todo el pipeline en orden: extract → transform/validate → load.
- [ ] Logging con niveles (INFO, WARNING, ERROR) a consola y a `logs/etl.log`.
- [ ] Manejo de excepciones con mensajes claros (nada de `except: pass`).
- [ ] Ejecución con `docker compose up` o `docker compose run etl`.
- [ ] Reprocesamiento: poder volver a correr el pipeline sobre los mismos archivos sin romper nada.
- [ ] Ejecución periódica (cron dentro del contenedor, o un servicio `scheduler`).
- [ ] Parámetros por CLI (`--entidad ventas`, `--fecha`, `--dry-run`).

---

## 4. Reglas de validación

Estas son las reglas mínimas. Para cada una vos decidís **qué hacer** (rechazar, corregir, completar) y lo justificás en el README.

| Entidad | Regla | Decisión sugerida |
|---|---|---|
| Clientes | `id_cliente` duplicado, registros idénticos | Quedarse con uno, loguear |
| Clientes | `id_cliente` duplicado, datos distintos | Decidir criterio (¿el último? ¿rechazar ambos?) y documentarlo |
| Clientes | Email vacío o sin `@` | Cargar con `NULL` o rechazar (decidir) |
| Clientes | Provincia vacía | Rechazar |
| Productos | Precio ≤ 0 | Rechazar |
| Productos | Categoría vacía | Asignar "Sin categoría" o rechazar |
| Productos | `id_producto` duplicado | Deduplicar |
| Ventas | `id_venta` repetido | Idempotencia: ¿conservar primero? ¿último? |
| Ventas | Fecha con formato incorrecto o imposible | Intentar parsear formatos conocidos; si no se puede, rechazar |
| Ventas | Fecha futura | Rechazar |
| Ventas | Cantidad ≤ 0 | Rechazar |
| Ventas | Precio unitario ≤ 0 o vacío | Rechazar (o tomar el precio del catálogo, decidir) |
| Ventas | `id_cliente` o `id_producto` inexistente | Rechazar (integridad referencial) |
| Ventas | Campos obligatorios vacíos | Rechazar |
| Compras | Mismas reglas de fecha, cantidad, costo y producto | Idem ventas |
| Compras | Proveedor vacío | Rechazar |

> 💡 Un buen Data Engineer no solo valida: **documenta por qué** tomó cada decisión.

---

## 5. Modelo de datos (propuesta inicial)

El diseño final lo definimos juntos en la Etapa 4. Punto de partida:

```
clientes (id_cliente PK, nombre, provincia, localidad, email)
productos (id_producto PK, producto, categoria, precio)
ventas (id_venta PK, fecha, id_cliente FK, id_producto FK, cantidad, precio_unitario)
compras (id_compra PK, fecha, proveedor, id_producto FK, cantidad, costo_unitario)

etl_runs (id PK, inicio, fin, entidad, filas_leidas, filas_validas,
          filas_rechazadas, estado, mensaje_error)
```

Cosas para pensar: ¿`proveedor` merece su propia tabla? ¿Conviene una columna calculada `total = cantidad * precio_unitario`? ¿Qué tipo de dato usar para el dinero? (pista: **no** `float`).

---

## 6. Cómo generar los CSV

Dos opciones. Recomiendo la **A**.

### Opción A — Script generador (recomendada)

Te dejé `generate_data.py`, que usa solo la librería estándar de Python (no hay que instalar nada).

```bash
# desde la raíz del repo
mkdir -p scripts
mv generate_data.py scripts/

python scripts/generate_data.py
# o con parámetros:
python scripts/generate_data.py --ventas 3000 --clientes 100 --seed 7
```

Genera en `data/raw/`:

| Archivo | Filas aprox. | Contenido |
|---|---|---|
| `clientes.csv` | 65 | 60 comercios + duplicados y emails/provincias malos |
| `productos.csv` | 26 | 25 productos + precio negativo/cero, categoría vacía, 1 duplicado |
| `ventas.csv` | 1520 | 1500 ventas de los últimos 60 días + ~100 con errores |
| `compras.csv` | 305 | 300 compras a 6 proveedores + errores |

Los errores que inyecta:

- **Duplicados:** clientes, productos, `id_venta` repetido (copias exactas y copias con datos *distintos*, que son las peores).
- **Fechas:** `13/11/2026`, `13-11-26`, `2026-13-45`, `ayer`, vacías.
- **Integridad referencial:** productos y clientes que no existen.
- **Valores inválidos:** cantidades negativas o cero, precios negativos o cero.
- **Vacíos:** campos obligatorios sin dato.

Detalles útiles:

- `--seed` fija la aleatoriedad: misma semilla, mismos datos. Útil para reproducir bugs y para tests.
- Genera además `data/ground_truth.json` con **cuántos errores de cada tipo** inyectó. Es tu clave de respuestas: cuando tu validador esté listo, compará lo que detecta contra eso. **No lo mires antes**, perdés la mitad del desafío.
- Para practicar reprocesamiento, corré el script otra vez con otra semilla y distinta cantidad de ventas, y simulá que "llegó el archivo de otro día".

### Opción B — Hacerlo vos (desafío extra)

Si querés sumar práctica, escribí tu propio generador con `random` o con la librería **Faker** (`pip install faker`, locale `es_AR`). Podés usar el mío como referencia.

### Archivos de ejemplo del enunciado

```csv
id_venta,fecha,id_cliente,id_producto,cantidad,precio_unitario
1001,2026-11-10,15,3,20,1500
1002,2026-11-10,18,5,10,2300
1003,2026-11-10,15,2,5,800
```

---

## 7. Estructura del repositorio

```
dataflow/
├── data/
│   ├── raw/             # CSV de entrada (no se versionan)
│   ├── processed/       # datos limpios
│   └── rejected/        # registros rechazados + motivo
├── scripts/
│   └── generate_data.py
├── src/
│   ├── config.py        # lectura de variables de entorno
│   ├── extract.py
│   ├── validate.py
│   ├── transform.py
│   ├── load.py
│   └── main.py
├── sql/
│   ├── schema.sql
│   └── queries/         # consultas de análisis
├── tests/
│   └── test_validate.py
├── logs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 8. Criterios de "listo para mostrar en una entrevista"

**Funcional**
- [ ] `git clone` + `cp .env.example .env` + `docker compose up` deja todo funcionando.
- [ ] El pipeline es idempotente.
- [ ] Los rechazados quedan registrados con motivo.
- [ ] Los números del pipeline coinciden con `ground_truth.json`.

**Calidad de código**
- [ ] Funciones chicas con una sola responsabilidad.
- [ ] Type hints y docstrings en las funciones principales.
- [ ] Sin credenciales en el código ni en el repo.
- [ ] Tests con `pytest` para las reglas de validación (mínimo 8 tests).

**Documentación (README)**
- [ ] Descripción del problema y del escenario.
- [ ] Diagrama de arquitectura / flujo del pipeline.
- [ ] Diagrama del modelo de datos (ER).
- [ ] Cómo ejecutarlo paso a paso.
- [ ] Tabla de reglas de validación y **decisiones tomadas**.
- [ ] Ejemplos de consultas SQL con sus resultados.
- [ ] Sección "Mejoras futuras" (Airflow, dbt, CI, particionado, etc.).

**Git**
- [ ] Commits chicos y descriptivos (`feat: agrega validación de fechas`).
- [ ] Una rama por etapa y PR al terminar cada una (aunque seas el único dev).

---

## 9. Extras opcionales (nivel "exigente")

- GitHub Actions: correr `pytest` y `ruff` en cada push.
- `pre-commit` con formateo y lint.
- Validación declarativa con **Pandera** o **Great Expectations**.
- Dashboard simple con **Metabase** o **Superset** en el mismo Compose.
- Carga incremental por fecha en lugar de recarga completa.
- Orquestación con **Airflow** o **Prefect** (buen puente hacia lo que viene después del bootcamp).
- Servicio de **pgAdmin** en el Compose.

---

## 10. Cómo vamos a trabajar (modo mixto)

Para cada etapa:

1. **Explicación:** yo te explico los conceptos clave y las decisiones de diseño.
2. **Desafío:** te doy los requerimientos y vos desarrollás.
3. **Revisión:** me mostrás tu código, lo revisamos juntos y lo mejoramos.

**Siguiente paso:** Etapa 1 (infraestructura). Armá la estructura de carpetas, corré el generador de datos y empezá con el `docker-compose.yml`. Cuando tengas algo, lo revisamos.
