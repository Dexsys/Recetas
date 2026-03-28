#!/usr/bin/env python3
"""Backup de la base de datos MariaDB.

Uso:
    python backup_db.py backup              Crear nuevo backup (.sql)
    python backup_db.py listar              Listar backups disponibles
    python backup_db.py restaurar <archivo> Restaurar un backup .sql

Los backups se guardan en instance/backups/ como archivos .sql.
Las credenciales se leen desde .env (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME).
"""

import os
import sys
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
    import pymysql
except ImportError:
    print("[ERROR] Falta pymysql. Instala con: pip install pymysql")
    sys.exit(1)

DB_HOST = os.environ.get("DB_HOST", "192.168.0.100")
DB_PORT = int(os.environ.get("DB_PORT") or 3306)
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "sabor_familia")

BACKUP_DIR = Path("instance/backups")


def _get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )


def hacer_backup():
    """Exporta la base de datos MariaDB a un archivo .sql con timestamp."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = BACKUP_DIR / f"{DB_NAME}_backup_{timestamp}.sql"

    print("=" * 60)
    print("[*] INICIANDO BACKUP MariaDB")
    print("=" * 60)
    print(f"[*] Servidor      : {DB_HOST}:{DB_PORT}")
    print(f"[*] Base de datos : {DB_NAME}")
    print(f"[*] Destino       : {dest}")
    print()

    try:
        conn = _get_connection()
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MariaDB: {e}")
        return False

    cursor = conn.cursor()
    lines = [
        f"-- Backup de {DB_NAME}",
        f"-- Fecha   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Servidor: {DB_HOST}:{DB_PORT}",
        "",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "",
    ]

    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]

    total_rows = 0
    for table in tables:
        print(f"  Exportando: {table}...", end=" ", flush=True)

        cursor.execute(f"SHOW CREATE TABLE `{table}`")
        _, create_sql = cursor.fetchone()
        lines.append(f"-- Tabla: {table}")
        lines.append(f"DROP TABLE IF EXISTS `{table}`;")
        lines.append(create_sql + ";")
        lines.append("")

        cursor.execute(f"SELECT * FROM `{table}`")
        rows = cursor.fetchall()
        if rows:
            cursor.execute(f"SHOW COLUMNS FROM `{table}`")
            cols = [row[0] for row in cursor.fetchall()]
            cols_str = ", ".join(f"`{c}`" for c in cols)
            row_strs = []

            # Usa el escapado del conector activo para compatibilidad entre versiones de PyMySQL.
            def _sql_literal(value):
                if value is None:
                    return "NULL"
                if isinstance(value, (int, float)):
                    return str(value)
                return conn.escape(str(value))

            for row in rows:
                vals = ", ".join(_sql_literal(v) for v in row)
                row_strs.append(f"  ({vals})")
            lines.append(f"INSERT INTO `{table}` ({cols_str}) VALUES")
            lines.append(",\n".join(row_strs) + ";")
            lines.append("")

        print(f"{len(rows)} filas")
        total_rows += len(rows)

    lines.append("SET FOREIGN_KEY_CHECKS = 1;")
    conn.close()

    dest.write_text("\n".join(lines), encoding="utf-8")
    size_kb = dest.stat().st_size / 1024

    print()
    print("=" * 60)
    print("[OK] BACKUP COMPLETADO")
    print("=" * 60)
    print(f"[*] Archivo : {dest}")
    print(f"[*] Tamaño  : {size_kb:.1f} KB")
    print(f"[*] Filas   : {total_rows}")
    print(f"[*] Fecha   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    return True


def listar_backups():
    """Lista todos los backups disponibles (SQL y SQLite legacy)."""
    if not BACKUP_DIR.exists():
        print("No hay backups disponibles aun.")
        return

    sql_backups = sorted(BACKUP_DIR.glob("*.sql"), reverse=True)
    sqlite_backups = sorted(BACKUP_DIR.glob("*.db"), reverse=True)
    all_backups = [(b, "MariaDB SQL") for b in sql_backups] + \
                  [(b, "SQLite DB ") for b in sqlite_backups]
    all_backups.sort(key=lambda x: x[0].name, reverse=True)

    if not all_backups:
        print("No hay backups disponibles.")
        return

    print("\n[*] BACKUPS DISPONIBLES")
    print("=" * 60)
    for i, (backup, kind) in enumerate(all_backups, 1):
        size_kb = backup.stat().st_size / 1024
        fecha = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{i}. [{kind}] {backup.name}")
        print(f"   Tamaño: {size_kb:.1f} KB | Fecha: {fecha.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def restaurar_backup(nombre_archivo):
    """Restaura un backup .sql a la base de datos MariaDB."""
    backup = BACKUP_DIR / nombre_archivo

    if not backup.exists():
        print(f"[ERROR] Backup no encontrado: {backup}")
        return False

    if not nombre_archivo.endswith(".sql"):
        print("[ERROR] Solo se pueden restaurar archivos .sql de MariaDB.")
        print("        Para migrar un SQLite usa: python migrate_to_mariadb.py <archivo.db>")
        return False

    print("=" * 60)
    print("[!] ADVERTENCIA: Esto sobreescribira las tablas actuales en:")
    print(f"    {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("=" * 60)
    confirmar = input("¿Confirmas la restauracion? [s/N]: ").strip().lower()
    if confirmar not in ("s", "si", "sí", "y", "yes"):
        print("Operacion cancelada.")
        return False

    try:
        conn = _get_connection()
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MariaDB: {e}")
        return False

    print("[*] Creando backup de seguridad antes de restaurar...")
    hacer_backup()

    print(f"[*] Restaurando desde: {backup.name}...")
    sql_content = backup.read_text(encoding="utf-8")

    cursor = conn.cursor()
    errors = 0
    for stmt in sql_content.split(";"):
        stmt = stmt.strip()
        if not stmt or stmt.startswith("--"):
            continue
        try:
            cursor.execute(stmt)
        except Exception as e:
            print(f"  [WARN] {e}")
            errors += 1
    conn.commit()
    conn.close()

    print()
    print("=" * 60)
    print("[OK] RESTAURACION COMPLETADA")
    print("=" * 60)
    if errors:
        print(f"[WARN] {errors} sentencias con advertencias")
    print(f"[*] Restaurado a : {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"[*] Hora         : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("[*] UTILIDAD DE BACKUP - MariaDB")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\nUso:")
        print("  python backup_db.py backup              Crear backup")
        print("  python backup_db.py listar              Ver backups")
        print("  python backup_db.py restaurar <archivo> Restaurar backup")
        sys.exit(0)

    comando = sys.argv[1].lower()
    if comando in ("backup", "hacer"):
        hacer_backup()
    elif comando in ("listar", "list"):
        listar_backups()
    elif comando in ("restaurar", "restore"):
        if len(sys.argv) < 3:
            print("[ERROR] Especifica el nombre del backup")
            print("Uso: python backup_db.py restaurar <nombre_archivo>")
            print()
            listar_backups()
        else:
            restaurar_backup(sys.argv[2])
    else:
        print(f"[ERROR] Comando no reconocido: {comando}")
        sys.exit(1)
