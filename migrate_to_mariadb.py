#!/usr/bin/env python3
"""Migra datos de un archivo SQLite a MariaDB.

Uso:
    python migrate_to_mariadb.py                    # ruta por defecto
    python migrate_to_mariadb.py /ruta/archivo.db   # ruta explicita
    SQLITE_PATH=/ruta/archivo.db python migrate_to_mariadb.py

Las credenciales de MariaDB se leen desde las variables de entorno
(cargadas desde .env si existe): DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME.
"""
import sqlite3
import pymysql
import sys
import os
from pathlib import Path

# Cargar .env si existe
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

# Ruta al SQLite: argumento CLI > variable de entorno > valor por defecto
if len(sys.argv) > 1:
    SQLITE_PATH = sys.argv[1]
else:
    SQLITE_PATH = os.environ.get("SQLITE_PATH", "instance/sabor_familia.db")

# Credenciales MariaDB desde entorno
MARIA_HOST = os.environ.get("DB_HOST", "192.168.0.100")
MARIA_PORT = int(os.environ.get("DB_PORT") or 3306)
MARIA_USER = os.environ.get("DB_USER", "root")
MARIA_PASSWORD = os.environ.get("DB_PASSWORD", "")
MARIA_DB = os.environ.get("DB_NAME", "sabor_familia")

TABLES = [
    "user",
    "category",
    "menu_type",
    "unit",
    "ingredient_price",
    "technique",
    "recipe",
    "ingredient",
    "comment",
    "recipe_image",
    "site_stats",
]


def migrate(sqlite_path=None, maria_host=None, maria_port=None,
            maria_user=None, maria_password=None, maria_db=None):
    """Migra datos de SQLite a MariaDB.

    Los parametros permiten sobreescribir los valores globales,
    lo que facilita el uso desde otros scripts (ej: import_prod_sqlite.py).
    """
    sqlite_path = sqlite_path or SQLITE_PATH
    maria_host = maria_host or MARIA_HOST
    maria_port = maria_port if maria_port is not None else MARIA_PORT
    maria_user = maria_user or MARIA_USER
    maria_password = maria_password if maria_password is not None else MARIA_PASSWORD
    maria_db = maria_db or MARIA_DB

    if not os.path.exists(sqlite_path):
        print(f"[ERROR] No se encontro el archivo SQLite: {sqlite_path}")
        sys.exit(1)

    print(f"[*] Origen  : SQLite -> {sqlite_path}")
    print(f"[*] Destino : MariaDB -> {maria_host}:{maria_port}/{maria_db}")
    print()

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    maria_conn = pymysql.connect(
        host=maria_host,
        port=maria_port,
        user=maria_user,
        password=maria_password,
        database=maria_db,
        charset="utf8mb4",
    )
    maria_cursor = maria_conn.cursor()

    total_rows = 0
    for table in TABLES:
        try:
            sqlite_cursor.execute(f"SELECT * FROM {table}")
        except sqlite3.OperationalError:
            print(f"  {table}: tabla no encontrada en SQLite, omitida")
            continue

        rows = sqlite_cursor.fetchall()
        if not rows:
            print(f"  {table}: 0 filas (omitido)")
            continue

        columns = [desc[0] for desc in sqlite_cursor.description]
        placeholders = ", ".join(["%s"] * len(columns))
        cols_str = ", ".join(f"`{c}`" for c in columns)

        inserted = 0
        skipped = 0
        for row in rows:
            values = []
            for val in row:
                if isinstance(val, str):
                    val = val.encode("utf-8", errors="replace").decode("utf-8")
                values.append(val)

            try:
                query = f"INSERT INTO `{table}` ({cols_str}) VALUES ({placeholders})"
                maria_cursor.execute(query, values)
                inserted += 1
            except pymysql.err.IntegrityError as e:
                if e.args[0] == 1062:
                    skipped += 1
                    continue
                raise

        maria_conn.commit()
        msg = f"  {table}: {inserted} filas migradas"
        if skipped:
            msg += f" ({skipped} duplicadas omitidas)"
        print(msg)
        total_rows += inserted

    print(f"\n[OK] Total: {total_rows} filas migradas a {maria_db}")

    sqlite_conn.close()
    maria_conn.close()


if __name__ == "__main__":
    migrate()
