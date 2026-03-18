#!/usr/bin/env python3
"""
Respaldo de codigo a GitHub con actualizacion previa de documentacion.

Uso:
    python backup_to_github.py
"""

import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

LOCAL = Path(__file__).parent
MANDATORY_DOCS = ["historial.md", "TODO.md", "README.md"]


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


def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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


def update_todo(date_iso):
    todo_path = LOCAL / "TODO.md"
    if not todo_path.exists():
        return

    content = todo_path.read_text(encoding="utf-8")
    marker = "- Ultima revision prebackup:"
    replacement = f"{marker} {date_iso}"

    if marker in content:
        updated = re.sub(r"(?m)^- Ultima revision prebackup:.*$", replacement, content)
    else:
        lines = content.splitlines()
        if lines:
            lines.insert(1, "")
            lines.insert(2, "## Control de respaldo")
            lines.insert(3, replacement)
            lines.insert(4, "")
            updated = "\n".join(lines)
            if content.endswith("\n"):
                updated += "\n"
        else:
            updated = f"# TODO\n\n## Control de respaldo\n{replacement}\n"

    if updated != content:
        todo_path.write_text(updated, encoding="utf-8")
        print("[OK] TODO.md actualizado")


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


def ensure_mandatory_docs_present():
    missing = [name for name in MANDATORY_DOCS if not (LOCAL / name).exists()]
    if missing:
        print("[ERROR] Faltan archivos obligatorios de documentacion prebackup:")
        for item in missing:
            print(f"        - {item}")
        raise SystemExit(1)


def get_worktree_changed_files():
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(LOCAL),
            check=True,
            capture_output=True,
            text=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def confirm_requirements_if_needed():
    changed_files = get_worktree_changed_files()
    if not changed_files:
        return

    has_python_changes = any(
        file_path.endswith('.py') or file_path.startswith('migrations/')
        for file_path in changed_files
    )
    requirements_changed = 'requirements.txt' in changed_files

    if not has_python_changes or requirements_changed:
        return

    skip_check = env_flag("BACKUP_SKIP_REQUIREMENTS_CHECK", False)
    if skip_check:
        print("[WARN] Omitiendo validacion de requirements por BACKUP_SKIP_REQUIREMENTS_CHECK=1")
        return

    print("[pre][ATENCION] Se detectaron cambios Python/migraciones sin cambios en requirements.txt")
    print("               Si agregaste dependencias, actualiza requirements.txt antes del respaldo.")
    answer = input("               Confirmas que requirements.txt no necesita cambios? [s/N]: ").strip().lower()
    if answer not in {"s", "si", "sí", "y", "yes"}:
        print("[ERROR] Respaldo cancelado. Actualiza requirements.txt y vuelve a intentar.")
        sys.exit(1)


def main():
    ensure_mandatory_docs_present()
    version, date_iso = get_version_info()
    update_readme(version, date_iso)
    update_todo(date_iso)
    update_historial(version, date_iso)
    confirm_requirements_if_needed()

    run(["git", "add", "README.md", "TODO.md", "historial.md"])
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
