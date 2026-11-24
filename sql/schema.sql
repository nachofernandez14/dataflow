CREATE TABLE IF NOT EXISTS clientes (
    id_cliente int PRIMARY KEY,
    nombre varchar(100) NOT NULL,
    provincia varchar(100) NOT NULL,
    localidad varchar(100) NOT NULL,
    email varchar(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS productos (
    id_producto int PRIMARY KEY,
    producto varchar(100) NOT NULL,
    categoria varchar(100) NOT NULL,
    precio numeric(10,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS proveedores (
    id_proveedor int PRIMARY KEY,
    nombre varchar(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS ventas (
    id_venta int PRIMARY KEY,
    id_cliente int NOT NULL REFERENCES clientes(id_cliente),
    id_producto int NOT NULL REFERENCES productos(id_producto),
    fecha date NOT NULL,
    cantidad int NOT NULL,
    precio_unitario numeric(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS compras (
    id_compra int PRIMARY KEY,
    id_proveedor int NOT NULL REFERENCES proveedores(id_proveedor),
    id_producto int NOT NULL REFERENCES productos(id_producto),
    fecha date NOT NULL,
    cantidad int NOT NULL,
    costo_unitario numeric(10,2) NOT NULL
);
