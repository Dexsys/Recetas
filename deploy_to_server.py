#!/usr/bin/env python3
"""
Deploy automático - Recetas → Raspberry Pi (Server01)
Conecta una sola vez y copia todos los archivos sin pedir contraseña repetidamente.

Requisitos (instalar una sola vez en Windows):
    pip install paramiko scp
"""

import os
import sys
import time
import datetime
from pathlib import Path

# ── Configuración del servidor ──────────────────────────────────────────────
SERVER   = "192.168.0.89"
PORT     = 22
USERNAME = "ubuntu"
PASSWORD = os.environ.get("DEPLOY_SSH_PASSWORD")
REMOTE   = "/home/ubuntu/Developer/Flask/Recetas"
LOCAL    = Path(__file__).parent
# ────────────────────────────────────────────────────────────────────────────

# Archivos y carpetas a desplegar (excluye .venv, __pycache__, *.db local, etc.)
ITEMS = [
    "app.py",
    "auto_backup_db.py",
    "backup_db.py",
    "config.py",
    "requirements.txt",
    "readme.md",
    "TODO.md",
    "wsgi.py",
    "historial.md",
    "app",
    "instance",
    "logs",
    "backups",
    "alembic",
    "Documentacion",
    "recetas.service",
]

def check_dependencies():
    try:
        import paramiko
        from scp import SCPClient
        return paramiko, SCPClient
    except ImportError:
        print("=" * 60)
        print("  ERROR: Faltan dependencias de Python")
        print("=" * 60)
        print("\n  Instálalas ejecutando:\n")
        print("      pip install paramiko scp\n")
        print("  Luego vuelve a ejecutar este script.")
        print("=" * 60)
        sys.exit(1)

def progress(filename, size, sent):
    if isinstance(filename, bytes):
        filename = filename.decode()
    name = Path(filename).name
    pct  = (sent / size * 100) if size > 0 else 100
    bar  = int(pct / 5) * "#" + int((100 - pct) / 5) * "-"
    print(f"\r    [{bar}] {pct:5.1f}%  {name:<30}", end="", flush=True)
    if sent == size:
        print()

def main():
    if not PASSWORD:
        print("[ERROR] Falta la variable de entorno DEPLOY_SSH_PASSWORD")
        print("        Ejemplo PowerShell: $env:DEPLOY_SSH_PASSWORD='tu_password'")
        sys.exit(1)

    # ── 0. Migración Alembic ───────────────────────────────────────────────
    print("[0/4] Ejecutando migraciones de base de datos (flask db upgrade)...")
    os.environ["FLASK_APP"] = "app:create_app"
    migrate_result = os.system(".venv\\Scripts\\flask.exe db upgrade")
    if migrate_result != 0:
        print("  [ERROR] Error ejecutando flask db upgrade. Revisa la consola y corrige antes de desplegar.")
        sys.exit(1)
    print("  [OK] Migraciones aplicadas correctamente\n")
    paramiko, SCPClient = check_dependencies()

    # Generar versión
    now = datetime.datetime.now()
    version = f"1.2026.{now.strftime('%m%d')}"

    print()
    print("=" * 60)
    print(f"  DESPLIEGUE -> Raspberry Pi  |  Licencias App v{version}")
    print("=" * 60)
    print(f"  Servidor : {SERVER}")
    print(f"  Destino  : {REMOTE}")
    print("=" * 60)
    print()

    # ── 1. Conexión SSH ──────────────────────────────────────────────────────
    print("[1/4] Conectando al servidor...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SERVER, PORT, USERNAME, PASSWORD, timeout=15)
        print(f"  [OK] Conexión establecida con {SERVER}\n")
    except Exception as e:
        print(f"  [ERROR] Error de conexión: {e}")
        sys.exit(1)

    def run(cmd):
        _, stdout, stderr = ssh.exec_command(cmd)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out: print(f"    {out}")
        if err: print(f"    (stderr) {err}")

    # ── 2. Asegurar estructura remota ────────────────────────────────────────
    print("[2/4] Preparando directorio remoto y permisos...")
    run(f"mkdir -p {REMOTE}/instance {REMOTE}/logs")
    # Asegurar que el usuario ubuntu tiene permisos (usa sudo con el password configurado)
    ssh.exec_command(f"echo '{PASSWORD}' | sudo -S chown -R {USERNAME}:{USERNAME} {REMOTE}")
    print("  [OK] Estructura de directorios y permisos listos\n")

    # ── 3. Copiar archivos ───────────────────────────────────────────────────
    print("[3/4] Copiando archivos...")
    with SCPClient(ssh.get_transport(), progress=progress) as scp:
        for item in ITEMS:
            src = LOCAL / item
            if not src.exists():
                print(f"  [WARN] '{item}' no encontrado, omitiendo...")
                continue
            try:
                if src.is_dir():
                    print(f"\n  -> {item}/")
                    scp.put(str(src), remote_path=REMOTE, recursive=True)
                else:
                    print(f"\n  -> {item}")
                    scp.put(str(src), remote_path=f"{REMOTE}/{item}")
            except Exception as e:
                print(f"  [ERROR] Error copiando {item}: {e}")

    print("\n  [OK] Archivos copiados\n")

    # ── 4. Reiniciar servicio ────────────────────────────────────────────────
    print("[4/4] Reiniciando servicio en el servidor...")
    run(f"sudo systemctl restart licencias")
    time.sleep(2)
    _, stdout, _ = ssh.exec_command("systemctl is-active licencias")
    status = stdout.read().decode().strip()
    if status == "active":
        print("  [OK] Servicio 'licencias' activo y corriendo\n")
    else:
        print(f"  [WARN] Estado del servicio: {status}")
        print("     Revisa con: journalctl -u licencias -n 30\n")

    ssh.close()

    # ── 5. Actualizar historial ──────────────────────────────────────────────
    print("[5/5] Actualizando historial de cambios...")
    historial_path = LOCAL / "historial.md"
    try:
        with open(historial_path, 'r', encoding='utf-8') as f:
            content = f.read()
        new_entry = f"##{version}: \n1.- Despliegue automático a producción\n\n"
        with open(historial_path, 'w', encoding='utf-8') as f:
            f.write(new_entry + content)
        print("  [OK] Historial actualizado\n")
    except Exception as e:
        print(f"  [WARN] Error actualizando historial: {e}\n")

    print("=" * 60)
    print("  DONE - DESPLIEGUE COMPLETADO")
    print("=" * 60)
    print(f"\n  App disponible en: https://licencias.dexsys.cl\n")
    print(f"  Versión desplegada: {version}\n")

if __name__ == "__main__":
    main()
