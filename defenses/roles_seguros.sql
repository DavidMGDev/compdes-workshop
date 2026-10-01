-- =============================================================================
--  roles_seguros.sql — Mínimo privilegio por identidad (Hora 3, defensa 3.5)
--  Defiende: la exfiltración de columnas sensibles (Lab 2.1) y la escritura
--  destructiva (Lab 2.3), aunque todo lo demás falle.
-- =============================================================================
--  Idea: cada herramienta MCP usa el rol con el MÍNIMO privilegio necesario.
--  Aunque secuestren el agente, el privilegio para leer notas_internas o
--  borrar tablas simplemente NO EXISTE en la identidad de lectura.
--
--  Aplicar contra la base del laboratorio (se puede aplicar varias veces):
--    Linux/macOS:  docker exec -i compdes-db psql -U onyx_app -d distribuidora < defenses/roles_seguros.sql
--    Windows PS:   Get-Content defenses\roles_seguros.sql | docker exec -i compdes-db psql -U onyx_app -d distribuidora
-- =============================================================================

-- Si los roles ya existen (segunda aplicación), primero se les quitan sus
-- permisos; si no, DROP ROLE falla con "some objects depend on it".
DO $$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['lector', 'escritor_stock'] LOOP
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = r) THEN
      EXECUTE format('DROP OWNED BY %I', r);
    END IF;
  END LOOP;
END $$;

-- Rol de SOLO LECTURA para consultas. Nota: sin acceso a columnas sensibles.
DROP ROLE IF EXISTS lector;
CREATE ROLE lector LOGIN PASSWORD 'lector_pwd';
GRANT SELECT (sku, producto, stock, precio_unit) ON inventario TO lector;  -- todo menos costo_unit (el margen)
GRANT SELECT (id, nombre) ON clientes TO lector;  -- solo id y nombre, NUNCA notas_internas ni credito_max

-- Rol de ESCRITURA acotada SOLO a la columna stock (usado bajo HITL, defensa 3.6).
DROP ROLE IF EXISTS escritor_stock;
CREATE ROLE escritor_stock LOGIN PASSWORD 'escritor_pwd';
GRANT SELECT (sku, stock), UPDATE (stock) ON inventario TO escritor_stock;  -- no puede tocar precio ni costo

-- El servidor MCP endurecido (inventory_mcp_server_seguro.py) se conecta como
-- 'lector' para consultar y como 'escritor_stock' para actualizar_stock, que
-- el agente solo ejecuta tras aprobación humana.
