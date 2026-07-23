-- =============================================================================
--  roles_seguros.sql — Mínimo privilegio por identidad (Hora 3, defensa 3.5)
--  Defiende: Lab 2.4 (ASI03, abuso de privilegio).
-- =============================================================================
--  Idea: cada herramienta MCP usa el rol con el MÍNIMO privilegio necesario.
--  Aunque secuestren el agente, el privilegio para leer notas_internas o
--  borrar tablas simplemente NO EXISTE en la identidad de lectura.
--
--  Aplicar contra la base del laboratorio:
--    docker exec -i compdes-db psql -U onyx_app -d distribuidora < defenses/roles_seguros.sql
-- =============================================================================

-- Rol de SOLO LECTURA para consultas. Nota: sin acceso a columnas sensibles.
DROP ROLE IF EXISTS lector;
CREATE ROLE lector LOGIN PASSWORD 'lector_pwd';
GRANT SELECT ON inventario TO lector;          -- puede ver inventario (menos costo, si se desea, revóquelo)
REVOKE ALL ON clientes FROM lector;            -- nada de clientes por defecto...
GRANT SELECT (id, nombre) ON clientes TO lector;  -- ...solo id y nombre, NUNCA notas_internas ni credito_max

-- Rol de ESCRITURA acotada SOLO a la columna stock (usado bajo HITL, defensa 3.6).
DROP ROLE IF EXISTS escritor_stock;
CREATE ROLE escritor_stock LOGIN PASSWORD 'escritor_pwd';
GRANT SELECT, UPDATE (stock) ON inventario TO escritor_stock;  -- no puede tocar precio ni costo

-- El servidor MCP endurecido (inventory_mcp_server_seguro.py) se conecta como
-- 'lector' para consultar. Si añade una herramienta de escritura de stock,
-- que se conecte como 'escritor_stock' y solo tras aprobación humana.
