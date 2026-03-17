#!/usr/bin/env python3
"""
Respaldo de codigo a GitHub con actualizacion previa de documentacion.

Uso:
    python backup_to_github.py
"""

import datetime
import re
import subprocess
from pathlib import Path

LOCAL = Path(__file__).parent


def run(cmd):
    result = subprocess.run(cmd, cwd=str(LOCAL), text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip())
        raise SystemExit(result.returncode)


def get_version_info():
    now = datetime.datetime.now()
    version = f"1.{now.year}.{now.strftime('%m%d')}"
    date_iso = now.strftime("%Y-%m-%d")
    return version, date_iso


def update_readme(version, date_iso):
    readme_path = LOCAL / "README.md"
    if not readme_path.exists():
        return

    content = readme_path.read_text(encoding="utf-8")
    updated = re.sub(r"(?m)^- Version:.*$", f"- Version: {version}", content)
    updated = re.sub(r"(?m)^- Ultima actualizacion:.*$", f"- Ultima actualizacion: {date_iso}", updated)

    if updated != content:
        readme_path.write_text(updated, encoding="utf-8")
        print("[OK] README.md actualizado")


def update_historial(version, date_iso):
    historial_path = LOCAL / "historial.md"
    if not historial_path.exists():
        return

    content = historial_path.read_text(encoding="utf-8")
    header = f"## [{version}] - {date_iso}"
    action_message = "Respaldo a GitHub ejecutado mediante backup_to_github.py."

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
        print("[OK] historial.md actualizado (nueva version)")
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
    print("[OK] historial.md actualizado")


def main():
    version, date_iso = get_version_info()
    update_readme(version, date_iso)
    update_historial(version, date_iso)

    run(["git", "add", "README.md", "historial.md"])
    run(["git", "add", "."])

    commit_message = f"chore: respaldo GitHub {version}"
    commit_result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        cwd=str(LOCAL),
        text=True,
        capture_output=True,
    )
    if commit_result.returncode == 0:
        print(commit_result.stdout.strip())
    else:
        stderr = commit_result.stderr.strip()
        stdout = commit_result.stdout.strip()
        combined = "\n".join([line for line in [stdout, stderr] if line])
        if "nothing to commit" in combined.lower():
            print("[INFO] No hay cambios para commit.")
        else:
            print(combined)
            raise SystemExit(commit_result.returncode)

    run(["git", "push", "origin", "main"])
    print(f"[OK] Respaldo completado en GitHub. Version: {version}")


if __name__ == "__main__":
    main()
