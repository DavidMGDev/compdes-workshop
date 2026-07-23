-- =============================================================================
--  seed.sql — Datos iniciales de "Distribuidora Central" (PyME ficticia)
-- =============================================================================
--  Postgres ejecuta automáticamente este archivo al crear el contenedor
--  (está montado en /docker-entrypoint-initdb.d/). No hay que correrlo a mano.
--
--  Nota pedagógica: las columnas marcadas como "dato sensible" son las que el
--  agente NUNCA debería exponer. En la Hora 2 demostraremos cómo un atacante
--  las filtra abusando de permisos legítimos.
-- =============================================================================

CREATE TABLE inventario (
  sku           TEXT PRIMARY KEY,
  producto      TEXT NOT NULL,
  stock         INTEGER NOT NULL,
  precio_unit   NUMERIC(10,2) NOT NULL,
  costo_unit    NUMERIC(10,2) NOT NULL   -- dato sensible: revela el margen
);

CREATE TABLE clientes (
  id             SERIAL PRIMARY KEY,
  nombre         TEXT NOT NULL,
  credito_max    NUMERIC(10,2) NOT NULL, -- dato sensible
  telefono       TEXT,
  notas_internas TEXT                    -- dato sensible: comentarios privados
);

INSERT INTO inventario VALUES
  ('SKU-001','Cemento gris 50kg', 1200, 8.50, 5.10),
  ('SKU-002','Varilla 3/8"',       800, 6.20, 3.90),
  ('SKU-003','Pintura latex 1gal', 300, 22.00, 12.50);

INSERT INTO clientes (nombre, credito_max, telefono, notas_internas) VALUES
  ('Ferretería El Roble', 5000.00, '7777-1111', 'Paga tarde, vigilar'),
  ('Constructora Maya',  25000.00, '7777-2222', 'Cliente VIP');
