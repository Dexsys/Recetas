#!/usr/bin/env python3
"""Crea la base de datos de desarrollo (dev_sabor_familia) clonando
el esquema de la base de datos de produccion (sabor_familia).

Uso:
    python setup_dev_db.py

Este script no copia datos, solo crea la estructura de tablas.
Luego ejecuta 'flask db upgrade' para asegurarte de que las migraciones
esten al dia.
"""
import os
import sys
from pathlib import Path

# Cargar .env
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _, _v = _line.partition("=")
        _k = _k.strip()
        _v = _v.strip().strip('"').strip("'")
        if _k not in os.environ:
            os.environ[_k] = _v

try:
    import pymysql
except ImportError:
    print("[ERROR] Falta pymysql. Instala con: pip install pymysql")
    sys.exit(1)

DB_HOST = os.environ.get("DB_HOST", "192.168.0.100")
DB_PORT = int(os.environ.get("DB_PORT") or 3306)
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

DB_SOURCE = "sabor_familia"
DB_DEV = "dev_sabor_familia"


def get_connection(database=None):
    kwargs = dict(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        charset="utf8mb4",
        autocommit=True,
    )
    if database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


def main():
    print("=" * 60)
    print("  SETUP BASE DE DATOS DE DESARROLLO")
    print("=" * 60)
    print(f"  Origen : {DB_SOURCE}  @ {DB_HOST}:{DB_PORT}")
    print(f"  Destino: {DB_DEV} @ {DB_HOST}:{DB_PORT}")
    print("=" * 60)
    print()

    try:
        conn = get_connection()
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MariaDB ({DB_HOST}:{DB_PORT}): {e}")
        sys.exit(1)

    cursor = conn.cursor()

    # Crear la base de datos dev si no existe
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_DEV}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    print(f"[OK] Base de datos '{DB_DEV}' creada o ya existente")

    # Obtener la lista de tablas en la BD fuente
    cursor.execute(f"USE `{DB_SOURCE}`")
    cursor.execute("SHOW TABLES")
    source_tables = [row[0] for row in cursor.fetchall()]

    if not source_tables:
        print(f"[WARN] La base de datos '{DB_SOURCE}' no tiene tablas todavia.")
        print("       Ejecuta primero: flask db upgrade (apuntando a sabor_familia)")
        conn.close()
        sys.exit(1)

    print(f"[*] Tablas en {DB_SOURCE}: {', '.join(source_tables)}")
    print()

    # Clonar estructura tabla por tabla (sin datos)
    cursor.execute(f"USE `{DB_DEV}`")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    cloned = 0
    skipped = 0
    for table in source_tables:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = %s",
            (DB_DEV, table),
        )
        exists = cursor.fetchone()[0] > 0

        if exists:
            print(f"  {table}: ya existe, omitida")
            skipped += 1
            continue

        # Obtener CREATE TABLE de la fuente
        cursor.execute(f"SHOW CREATE TABLE `{DB_SOURCE}`.`{table}`")
        _, create_sql = cursor.fetchone()

        cursor.execute(create_sql)
        print(f"  {table}: creada")
        cloned += 1

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.close()

    print()
    print(f"[OK] {cloned} tablas clonadas, {skipped} ya existian")
    print()
    print("Siguientes pasos:")
    print("  1. Verifica que .env tiene  DB_NAME=dev_sabor_familia")
    print("  2. Marca la BD al dia:      flask db stamp head")
    print("  3. Aplica migraciones:      flask db upgrade")
    print("  4. Inicia la app:           python app.py")


if __name__ == "__main__":
    main()
