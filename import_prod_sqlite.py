#!/usr/bin/env python3
"""Importa los datos del SQLite de produccion (servidor 192.168.0.89)
a la base de datos MariaDB 'sabor_familia' en 192.168.0.100.

Pasos que realiza:
  1. Conecta via SSH a 192.168.0.89
  2. Verifica que existe instance/sabor_familia.db en el servidor
  3. Descarga el archivo SQLite via SCP
  4. Guarda copia de respaldo en instance/backups/
  5. Muestra conteo de filas por tabla (SQLite vs MariaDB antes)
  6. Migra todos los datos a MariaDB sabor_familia (omite duplicados)
  7. Muestra tabla comparativa de filas antes/despues

Uso:
    python import_prod_sqlite.py

Requiere:
    pip install paramiko scp pymysql
"""
import os
import sys
import shutil
import sqlite3
from datetime import datetime
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
    import paramiko
    from scp import SCPClient
except ImportError:
    print("[ERROR] Faltan dependencias: pip install paramiko scp")
    sys.exit(1)

try:
    import pymysql
except ImportError:
    print("[ERROR] Falta pymysql: pip install pymysql")
    sys.exit(1)

# ── Configuracion SSH (servidor produccion) ──────────────────────────────────
SSH_HOST = "192.168.0.89"
SSH_PORT = 22
SSH_USER = "ubuntu"
SSH_PASSWORD = os.environ.get("DEPLOY_SSH_PASSWORD", "")

REMOTE_BASE = "/home/ubuntu/Developer/Flask/Recetas"
REMOTE_SQLITE = f"{REMOTE_BASE}/instance/sabor_familia.db"

# ── Configuracion MariaDB (SIEMPRE produccion, independiente del .env) ────────
MARIA_HOST = os.environ.get("DB_HOST", "192.168.0.100")
MARIA_PORT = int(os.environ.get("DB_PORT") or 3306)
MARIA_USER = os.environ.get("DB_USER", "root")
MARIA_PASSWORD = os.environ.get("DB_PASSWORD", "")
MARIA_DB = "sabor_familia"  # siempre produccion, no dev

LOCAL_DOWNLOAD = Path("instance/prod_sqlite_download.db")
BACKUP_DIR = Path("instance/backups")

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


def count_sqlite_rows(db_path):
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    counts = {}
    for table in TABLES:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            counts[table] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            counts[table] = None
    conn.close()
    return counts


def count_mariadb_rows():
    try:
        conn = pymysql.connect(
            host=MARIA_HOST, port=MARIA_PORT, user=MARIA_USER,
            password=MARIA_PASSWORD, database=MARIA_DB, charset="utf8mb4",
        )
        cursor = conn.cursor()
        counts = {}
        for table in TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                counts[table] = cursor.fetchone()[0]
            except Exception:
                counts[table] = None
        conn.close()
        return counts
    except Exception as e:
        print(f"  [WARN] No se pudo contar filas en MariaDB: {e}")
        return {}


def migrate_to_mariadb(sqlite_path):
    """Inserta filas de SQLite en MariaDB, omitiendo duplicados."""
    conn_lite = sqlite3.connect(str(sqlite_path))
    conn_lite.row_factory = sqlite3.Row
    cursor_lite = conn_lite.cursor()

    conn_maria = pymysql.connect(
        host=MARIA_HOST, port=MARIA_PORT, user=MARIA_USER,
        password=MARIA_PASSWORD, database=MARIA_DB, charset="utf8mb4",
    )
    cursor_maria = conn_maria.cursor()

    total_inserted = 0
    total_skipped = 0

    for table in TABLES:
        try:
            cursor_lite.execute(f"SELECT * FROM {table}")
        except sqlite3.OperationalError:
            print(f"  {table}: no existe en SQLite, omitida")
            continue

        rows = cursor_lite.fetchall()
        if not rows:
            print(f"  {table}: 0 filas")
            continue

        columns = [desc[0] for desc in cursor_lite.description]
        placeholders = ", ".join(["%s"] * len(columns))
        cols_str = ", ".join(f"`{c}`" for c in columns)
        query = f"INSERT INTO `{table}` ({cols_str}) VALUES ({placeholders})"

        inserted = 0
        skipped = 0
        for row in rows:
            values = []
            for val in row:
                if isinstance(val, str):
                    val = val.encode("utf-8", errors="replace").decode("utf-8")
                values.append(val)
            try:
                cursor_maria.execute(query, values)
                inserted += 1
            except pymysql.err.IntegrityError as e:
                if e.args[0] == 1062:
                    skipped += 1
                else:
                    raise

        conn_maria.commit()
        msg = f"  {table}: {inserted} filas insertadas"
        if skipped:
            msg += f" ({skipped} duplicadas omitidas)"
        print(msg)
        total_inserted += inserted
        total_skipped += skipped

    conn_lite.close()
    conn_maria.close()
    return total_inserted, total_skipped


def main():
    if not SSH_PASSWORD:
        print("[ERROR] DEPLOY_SSH_PASSWORD no esta definido en .env")
        sys.exit(1)

    print("=" * 60)
    print("  IMPORTACION SQLite PRODUCCION -> MariaDB")
    print("=" * 60)
    print(f"  Origen SSH : {SSH_USER}@{SSH_HOST}")
    print(f"  Archivo    : {REMOTE_SQLITE}")
    print(f"  Destino DB : {MARIA_HOST}:{MARIA_PORT}/{MARIA_DB}")
    print("=" * 60)
    print()

    # ── 1. Conectar SSH ───────────────────────────────────────────────────────
    print("[1/5] Conectando via SSH a produccion...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(SSH_HOST, SSH_PORT, SSH_USER, SSH_PASSWORD, timeout=15)
        print(f"  [OK] Conexion establecida con {SSH_HOST}\n")
    except Exception as e:
        print(f"  [ERROR] {e}")
        sys.exit(1)

    # ── 2. Verificar SQLite en servidor ───────────────────────────────────────
    print("[2/5] Verificando archivo SQLite en servidor...")
    _, stdout, _ = ssh.exec_command(
        f"test -f {REMOTE_SQLITE} && echo found || echo missing"
    )
    result = stdout.read().decode().strip()
    if result != "found":
        print(f"  [WARN] Archivo no encontrado: {REMOTE_SQLITE}")
        print("         Es posible que el servidor ya este usando MariaDB.")
        ssh.close()
        sys.exit(1)

    _, stdout, _ = ssh.exec_command(f"stat -c '%s' {REMOTE_SQLITE}")
    size_bytes = int(stdout.read().decode().strip() or 0)
    print(f"  [OK] Archivo encontrado ({size_bytes / 1024:.1f} KB)\n")

    # ── 3. Descargar SQLite via SCP ───────────────────────────────────────────
    print("[3/5] Descargando SQLite del servidor...")
    LOCAL_DOWNLOAD.parent.mkdir(parents=True, exist_ok=True)
    with SCPClient(ssh.get_transport()) as scp:
        scp.get(REMOTE_SQLITE, str(LOCAL_DOWNLOAD))
    print(f"  [OK] Descargado a {LOCAL_DOWNLOAD}")

    ssh.close()

    # Respaldar copia local
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUP_DIR / f"prod_sqlite_backup_{timestamp}.db"
    shutil.copy2(LOCAL_DOWNLOAD, backup_path)
    print(f"  [OK] Respaldo guardado: {backup_path.name}\n")

    # ── 4. Conteos antes de migrar ────────────────────────────────────────────
    print("[4/5] Conteo de filas (antes de migrar):")
    sqlite_counts = count_sqlite_rows(LOCAL_DOWNLOAD)
    mariadb_before = count_mariadb_rows()
    print()
    print(f"  {'Tabla':<22} {'SQLite':>8} {'MariaDB':>8}")
    print(f"  {'-'*22} {'-'*8} {'-'*8}")
    for table in TABLES:
        s = sqlite_counts.get(table)
        m = mariadb_before.get(table)
        s_str = str(s) if s is not None else "-"
        m_str = str(m) if m is not None else "-"
        print(f"  {table:<22} {s_str:>8} {m_str:>8}")
    print()

    # ── 5. Migrar datos ───────────────────────────────────────────────────────
    print("[5/5] Migrando datos a MariaDB...")
    print()
    total_in, total_sk = migrate_to_mariadb(LOCAL_DOWNLOAD)

    # Conteo final
    mariadb_after = count_mariadb_rows()

    print()
    print("=" * 60)
    print("  RESULTADO FINAL")
    print("=" * 60)
    print(f"  {'Tabla':<22} {'Antes':>8} {'Despues':>8} {'Nuevo':>8}")
    print(f"  {'-'*22} {'-'*8} {'-'*8} {'-'*8}")
    for table in TABLES:
        before = mariadb_before.get(table) or 0
        after = mariadb_after.get(table) or 0
        new = after - before
        new_str = f"+{new}" if new > 0 else str(new)
        print(f"  {table:<22} {before:>8} {after:>8} {new_str:>8}")
    print("=" * 60)
    print(f"  Total insertadas : {total_in}")
    print(f"  Duplicadas omit. : {total_sk}")
    print("=" * 60)
    print()
    print("[OK] Importacion completada.")

    # Limpiar archivo temporal descargado
    LOCAL_DOWNLOAD.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
