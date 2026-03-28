#!/usr/bin/env python3
"""Respaldo completo del proyecto.

Incluye en un solo flujo:
- Backup de base de datos (backup_db.py).
- Compresion de uploads en tar.gz.
- Respaldo del codigo en GitHub (backup_to_github.py).

Uso:
    python full_backup.py
    python full_backup.py --skip-github
    python full_backup.py --skip-db
    python full_backup.py --skip-uploads
    python full_backup.py --out-dir instance/full_backups
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).parent.resolve()
BACKUP_DIR = ROOT / "instance" / "backups"
DEFAULT_FULL_DIR = ROOT / "instance" / "full_backups"


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        env=env,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip())
        raise RuntimeError(f"Comando fallido ({result.returncode}): {' '.join(cmd)}")
    if result.stderr.strip():
        print(result.stderr.strip())
    return result


def _latest_sql_from_backup(before_files: set[Path]) -> Path:
    after_files = set(BACKUP_DIR.glob("*.sql"))
    created = sorted(after_files - before_files, key=lambda p: p.stat().st_mtime, reverse=True)
    if created:
        return created[0]
    if after_files:
        return max(after_files, key=lambda p: p.stat().st_mtime)
    raise RuntimeError("No se encontro archivo .sql en instance/backups luego del backup de DB")


def _archive_uploads(destination_dir: Path, timestamp: str) -> tuple[Path, int]:
    uploads_dir = ROOT / "uploads"
    archive_path = destination_dir / f"uploads_{timestamp}.tar.gz"
    file_count = 0

    with tarfile.open(archive_path, mode="w:gz") as tar:
        if uploads_dir.exists():
            tar.add(uploads_dir, arcname="uploads")
            file_count = sum(1 for p in uploads_dir.rglob("*") if p.is_file())

    return archive_path, file_count


def _git_info() -> dict[str, str]:
    info = {"branch": "unknown", "head": "unknown"}
    try:
        info["branch"] = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        info["head"] = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    except Exception:
        pass
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description="Respaldo completo: DB + uploads + GitHub")
    parser.add_argument("--skip-db", action="store_true", help="Omitir backup de base de datos")
    parser.add_argument("--skip-uploads", action="store_true", help="Omitir compresion de uploads")
    parser.add_argument("--skip-github", action="store_true", help="Omitir respaldo a GitHub")
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_FULL_DIR),
        help="Directorio donde se guarda el paquete de respaldo completo",
    )
    args = parser.parse_args()

    now = dt.datetime.now()
    stamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    out_root = Path(args.out_dir)
    if not out_root.is_absolute():
        out_root = (ROOT / out_root).resolve()

    full_dir = out_root / f"full_backup_{stamp}"
    full_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, object] = {
        "timestamp": now.isoformat(timespec="seconds"),
        "project_root": str(ROOT),
        "output_dir": str(full_dir),
        "steps": {},
        "git": _git_info(),
    }

    print("=" * 70)
    print("[FULL BACKUP] Iniciando proceso")
    print(f"[FULL BACKUP] Destino: {full_dir}")
    print("=" * 70)

    try:
        if not args.skip_db:
            print("\n[1/3] Backup de base de datos...")
            before = set(BACKUP_DIR.glob("*.sql"))
            _run([sys.executable, "backup_db.py", "backup"])
            latest_sql = _latest_sql_from_backup(before)
            db_dest_dir = full_dir / "db"
            db_dest_dir.mkdir(parents=True, exist_ok=True)
            copied_sql = db_dest_dir / latest_sql.name
            shutil.copy2(latest_sql, copied_sql)
            manifest["steps"]["db"] = {
                "ok": True,
                "source": str(latest_sql),
                "copied_to": str(copied_sql),
            }
            print(f"[OK] DB respaldada: {copied_sql}")
        else:
            manifest["steps"]["db"] = {"ok": False, "skipped": True}
            print("\n[1/3] Backup de base de datos omitido (--skip-db)")

        if not args.skip_uploads:
            print("\n[2/3] Compresion de uploads...")
            uploads_archive, uploads_files = _archive_uploads(full_dir, stamp)
            manifest["steps"]["uploads"] = {
                "ok": True,
                "archive": str(uploads_archive),
                "files": uploads_files,
            }
            print(f"[OK] Uploads comprimidos: {uploads_archive}")
            print(f"[OK] Archivos incluidos: {uploads_files}")
        else:
            manifest["steps"]["uploads"] = {"ok": False, "skipped": True}
            print("\n[2/3] Compresion de uploads omitida (--skip-uploads)")

        if not args.skip_github:
            print("\n[3/3] Respaldo de codigo a GitHub...")
            env = os.environ.copy()
            _run([sys.executable, "backup_to_github.py"], env=env)
            manifest["steps"]["github"] = {"ok": True}
            print("[OK] Respaldo en GitHub completado")
        else:
            manifest["steps"]["github"] = {"ok": False, "skipped": True}
            print("\n[3/3] Respaldo a GitHub omitido (--skip-github)")

        manifest_path = full_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")

        print("\n" + "=" * 70)
        print("[OK] FULL BACKUP COMPLETADO")
        print(f"[OK] Manifest: {manifest_path}")
        print("=" * 70)
        return 0
    except Exception as exc:
        manifest["error"] = str(exc)
        manifest_path = full_dir / "manifest.error.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")
        print("\n" + "=" * 70)
        print(f"[ERROR] Full backup fallido: {exc}")
        print(f"[ERROR] Registro: {manifest_path}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
