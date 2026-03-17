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
import subprocess
import shlex
import re
import importlib
from pathlib import Path

# ── Configuración del servidor ──────────────────────────────────────────────
SERVER   = "192.168.0.89"
PORT     = 22
USERNAME = "ubuntu"
REMOTE   = "/home/ubuntu/Developer/Flask/Recetas"
DEFAULT_SERVICE = "recetas"
DEFAULT_REMOTE_PYTHON = "python3"
DEFAULT_REMOTE_VENV = ".venv"
LOCAL    = Path(__file__).parent
# ────────────────────────────────────────────────────────────────────────────

# Fallback en caso de no poder leer archivos versionados con Git.
FALLBACK_ITEMS = [
    "app.py",
    "backup_db.py",
    "config.py",
    "decorators.py",
    "extensions.py",
    "forms.py",
    "models.py",
    "requirements.txt",
    "README.md",
    "historial.md",
    "recetas.service",
]


def get_version_info():
    now = datetime.datetime.now()
    version = f"1.{now.year}.{now.strftime('%m%d')}"
    date_iso = now.strftime("%Y-%m-%d")
    return version, date_iso


def load_env_file(env_path):
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if (value.startswith("\"") and value.endswith("\"")) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        os.environ[key] = value


def update_readme(version, date_iso):
    readme_path = LOCAL / "README.md"
    if not readme_path.exists():
        return

    content = readme_path.read_text(encoding="utf-8")
    updated = re.sub(r"(?m)^- Version:.*$", f"- Version: {version}", content)
    updated = re.sub(r"(?m)^- Ultima actualización:.*$", f"- Ultima actualización: {date_iso}", updated)

    if updated != content:
        readme_path.write_text(updated, encoding="utf-8")
        print("  [OK] README.md actualizado")


def update_historial(version, date_iso, action_message):
    historial_path = LOCAL / "historial.md"
    if not historial_path.exists():
        return

    content = historial_path.read_text(encoding="utf-8")
    header = f"## [{version}] - {date_iso}"

    if header not in content:
        entry = (
            f"{header}\n\n"
            "### Agregado\n"
            "- Sin cambios registrados.\n\n"
            "### Corregido\n"
            "- Sin cambios registrados.\n\n"
            "### Tecnico\n"
            "- Sin cambios registrados.\n\n"
            "### Modificado\n"
            "- Sin cambios registrados.\n\n"
            "### Migracion de Base de Datos\n"
            "- Sin cambios de esquema.\n\n"
            "### Eliminado\n"
            "- Sin cambios.\n\n"
            "### Infraestructura\n"
            f"- {action_message}\n\n"
            "---\n\n"
        )
        first_version_pos = content.find("## [")
        if first_version_pos == -1:
            content = content.rstrip() + "\n\n" + entry
        else:
            content = content[:first_version_pos] + entry + content[first_version_pos:]
        historial_path.write_text(content, encoding="utf-8")
        print("  [OK] historial.md actualizado (nueva version)")
        return

    start = content.find(header)
    end = content.find("\n## [", start + 1)
    if end == -1:
        end = len(content)
    block = content[start:end]

    if action_message in block:
        return

    section = "### Infraestructura"
    section_pos = block.find(section)
    if section_pos == -1:
        block = block.rstrip() + f"\n\n{section}\n- {action_message}\n"
    else:
        insert_pos = section_pos + len(section)
        block = block[:insert_pos] + f"\n- {action_message}" + block[insert_pos:]

    content = content[:start] + block + content[end:]
    historial_path.write_text(content, encoding="utf-8")
    print("  [OK] historial.md actualizado")


def update_docs_before_operation(action_message):
    version, date_iso = get_version_info()
    print("[pre] Actualizando historial y README...")
    update_readme(version, date_iso)
    update_historial(version, date_iso, action_message)
    return version


def get_items_to_deploy():
    """Use tracked git files to avoid copying local basura to production."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(LOCAL),
            check=True,
            capture_output=True,
            text=True,
        )
        items = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if items:
            return items
    except Exception as exc:
        print(f"  [WARN] No se pudo leer git ls-files ({exc}). Usando fallback.")

    return [item for item in FALLBACK_ITEMS if (LOCAL / item).exists()]

def check_dependencies():
    try:
        paramiko = importlib.import_module("paramiko")
        scp_module = importlib.import_module("scp")
        SCPClient = scp_module.SCPClient
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
    load_env_file(LOCAL / ".env")

    password = os.environ.get("DEPLOY_SSH_PASSWORD")
    service = os.environ.get("DEPLOY_SERVICE_NAME", DEFAULT_SERVICE)
    remote_python = os.environ.get("DEPLOY_PYTHON", DEFAULT_REMOTE_PYTHON)
    remote_venv = os.environ.get("DEPLOY_REMOTE_VENV", DEFAULT_REMOTE_VENV)

    if not password:
        print("[ERROR] Falta la variable de entorno DEPLOY_SSH_PASSWORD")
        print("        Definela en .env o en PowerShell: $env:DEPLOY_SSH_PASSWORD='tu_password'")
        sys.exit(1)

    version = update_docs_before_operation("Deploy a produccion ejecutado mediante deploy_to_server.py.")
    paramiko, SCPClient = check_dependencies()

    items = get_items_to_deploy()
    if not items:
        print("[ERROR] No se encontraron archivos para desplegar.")
        sys.exit(1)

    print()
    print("=" * 60)
    print(f"  DESPLIEGUE -> Raspberry Pi  |  Recetas App v{version}")
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
        ssh.connect(SERVER, PORT, USERNAME, password, timeout=15)
        print(f"  [OK] Conexión establecida con {SERVER}\n")
    except Exception as e:
        print(f"  [ERROR] Error de conexión: {e}")
        sys.exit(1)

    def run(cmd):
        _, stdout, stderr = ssh.exec_command(cmd)
        status_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(f"    {out}")
        if err:
            print(f"    (stderr) {err}")
        return status_code

    def run_sudo(cmd):
        return run(f"echo {shlex.quote(password)} | sudo -S {cmd}")

    # ── 2. Asegurar estructura remota ────────────────────────────────────────
    print("[2/4] Preparando directorio remoto y permisos...")
    run(f"mkdir -p {shlex.quote(REMOTE)}")
    run(f"mkdir -p {shlex.quote(REMOTE + '/instance')}")
    run(f"mkdir -p {shlex.quote(REMOTE + '/uploads')}")
    # Asegurar que el usuario ubuntu tiene permisos (usa sudo con el password configurado)
    run_sudo(f"chown -R {USERNAME}:{USERNAME} {shlex.quote(REMOTE)}")
    print("  [OK] Estructura de directorios y permisos listos\n")

    # ── 3. Copiar archivos ───────────────────────────────────────────────────
    print("[3/4] Copiando archivos...")

    remote_dirs = sorted({
        Path(item).parent.as_posix()
        for item in items
        if Path(item).parent.as_posix() not in ('', '.')
    })
    for rel_dir in remote_dirs:
        run(f"mkdir -p {shlex.quote(REMOTE + '/' + rel_dir)}")

    with SCPClient(ssh.get_transport(), progress=progress) as scp:
        for item in items:
            src = LOCAL / item
            if not src.exists():
                print(f"  [WARN] '{item}' no encontrado, omitiendo...")
                continue
            try:
                if src.is_dir():
                    continue
                print(f"\n  -> {item}")
                remote_file = f"{REMOTE}/{Path(item).as_posix()}"
                scp.put(str(src), remote_path=remote_file)
            except Exception as e:
                print(f"  [ERROR] Error copiando {item}: {e}")

    print("\n  [OK] Archivos copiados\n")

    # Instalar dependencias en venv remoto y ejecutar migraciones.
    print("[3.1/4] Aplicando migraciones en servidor remoto...")
    remote_venv_python = f"{REMOTE}/{remote_venv}/bin/python"

    if run(f"cd {shlex.quote(REMOTE)} && {remote_python} -m venv {shlex.quote(remote_venv)}") != 0:
        print("  [ERROR] Fallo creando entorno virtual remoto.")
        sys.exit(1)

    if run(f"cd {shlex.quote(REMOTE)} && {shlex.quote(remote_venv_python)} -m pip install --upgrade pip") != 0:
        print("  [ERROR] Fallo actualizando pip en el entorno remoto.")
        sys.exit(1)

    if run(f"cd {shlex.quote(REMOTE)} && {shlex.quote(remote_venv_python)} -m pip install -r requirements.txt") != 0:
        print("  [ERROR] Fallo instalando dependencias en el servidor.")
        sys.exit(1)
    if run(f"cd {shlex.quote(REMOTE)} && FLASK_APP=app:create_app {shlex.quote(remote_venv_python)} -m flask db upgrade") != 0:
        print("  [ERROR] Fallo aplicando migraciones en el servidor.")
        sys.exit(1)
    print("  [OK] Migraciones remotas aplicadas\n")

    # Validar e instalar unit file de systemd antes de reiniciar.
    print("[3.2/4] Instalando servicio systemd...")
    remote_service_source = f"{REMOTE}/{service}.service"
    if run(f"test -f {shlex.quote(remote_service_source)}") != 0:
        fallback_service_source = f"{REMOTE}/recetas.service"
        if service != "recetas" and run(f"test -f {shlex.quote(fallback_service_source)}") == 0:
            print(f"  [WARN] No existe {service}.service en el repo. Usando recetas.service como fuente.")
            remote_service_source = fallback_service_source
        else:
            print(f"  [ERROR] No se encontró el archivo de servicio remoto: {remote_service_source}")
            sys.exit(1)

    if run_sudo(f"cp {shlex.quote(remote_service_source)} /etc/systemd/system/{service}.service") != 0:
        print("  [ERROR] Fallo instalando el archivo de servicio en /etc/systemd/system.")
        sys.exit(1)
    if run_sudo("systemctl daemon-reload") != 0:
        print("  [ERROR] Fallo en systemctl daemon-reload.")
        sys.exit(1)
    if run_sudo(f"systemctl enable {service}") != 0:
        print(f"  [WARN] No se pudo habilitar el servicio {service} en el arranque.")
    print("  [OK] Servicio systemd instalado/actualizado\n")

    # ── 4. Reiniciar servicio ────────────────────────────────────────────────
    print("[4/4] Reiniciando servicio en el servidor...")
    if run_sudo(f"systemctl restart {service}") != 0:
        print(f"  [ERROR] No se pudo reiniciar {service}.service")
        print("  [INFO] Diagnostico rapido del servicio:")
        run_sudo(f"systemctl status {service}.service --no-pager -l")
        run_sudo(f"journalctl -xeu {service}.service -n 80 --no-pager")
        sys.exit(1)
    time.sleep(2)
    _, stdout, _ = ssh.exec_command(f"systemctl is-active {service}")
    status = stdout.read().decode().strip()
    if status == "active":
        print(f"  [OK] Servicio '{service}' activo y corriendo\n")
    else:
        print(f"  [WARN] Estado del servicio: {status}")
        print(f"     Revisa con: journalctl -u {service} -n 30\n")

    ssh.close()

    print("=" * 60)
    print("  DONE - DESPLIEGUE COMPLETADO")
    print("=" * 60)
    print(f"\n  App disponible en: https://recetas.dexsys.cl\n")
    print(f"  Versión desplegada: {version}\n")

if __name__ == "__main__":
    main()
