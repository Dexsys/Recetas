"""
Script para hacer backup de la base de datos
Uso: python backup_db.py

Este script copia la base de datos actual a una carpeta de backups
con timestamp para fácil identificación.
"""

import shutil
import os
import sys
from datetime import datetime
from pathlib import Path

# Configurar encoding para Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def crear_carpeta_backups():
    """Crea carpeta de backups si no existe"""
    carpeta = Path('instance/backups')
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta

def hacer_backup():
    """Realiza backup de la base de datos"""
    # Ubicación de la BD principal (en instance/)
    origen = Path('instance/sabor_familia.db')

    if not origen.exists():
        print("[ERROR] No se encontro la base de datos en instance/sabor_familia.db")
        return False

    # Crear carpeta de backups
    carpeta_backups = crear_carpeta_backups()

    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    nombre_backup = f'sabor_familia_backup_{timestamp}.db'
    destino = carpeta_backups / nombre_backup

    try:
        # Copiar base de datos
        shutil.copy2(origen, destino)

        # Obtener tamaño del archivo
        tamaño = destino.stat().st_size / (1024 * 1024)  # Convertir a MB

        print("=" * 60)
        print("[OK] BACKUP REALIZADO EXITOSAMENTE")
        print("=" * 60)
        print(f"[*] Ubicacion: {destino}")
        print(f"[*] Tamaño: {tamaño:.2f} MB")
        print(f"[*] Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"[ERROR] Problema al hacer backup: {e}")
        return False

def listar_backups():
    """Lista todos los backups disponibles"""
    carpeta_backups = Path('instance/backups')

    if not carpeta_backups.exists():
        print("No hay backups disponibles aun.")
        return

    backups = sorted(carpeta_backups.glob('sabor_familia_backup_*.db'), reverse=True)

    if not backups:
        print("No hay backups disponibles.")
        return

    print("\n[*] BACKUPS DISPONIBLES")
    print("=" * 60)
    for i, backup in enumerate(backups, 1):
        tamaño = backup.stat().st_size / (1024 * 1024)
        fecha_mod = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{i}. {backup.name}")
        print(f"   Tamaño: {tamaño:.2f} MB | Fecha: {fecha_mod.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def restaurar_backup(nombre_archivo):
    """Restaura un backup específico"""
    backup = Path('instance/backups') / nombre_archivo
    destino = Path('instance/sabor_familia.db')

    if not backup.exists():
        print(f"[ERROR] Backup no encontrado: {backup}")
        return False

    try:
        # Hacer backup del archivo actual antes de restaurar
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        archivo_actual_backup = Path('instance/backups') / f'sabor_familia_backup_ANTES_RESTAURAR_{timestamp}.db'

        if destino.exists():
            shutil.copy2(destino, archivo_actual_backup)
            print(f"[*] Backup de seguridad creado: {archivo_actual_backup.name}")

        # Restaurar el backup
        shutil.copy2(backup, destino)

        print("=" * 60)
        print("[OK] BACKUP RESTAURADO EXITOSAMENTE")
        print("=" * 60)
        print(f"[*] Archivo: {backup.name}")
        print(f"[*] Restaurado a: {destino}")
        print(f"[*] Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print("\n[!] IMPORTANTE: Reinicia la aplicacion para que los cambios surtan efecto")
        print("Ejecuta: python app.py")

        return True

    except Exception as e:
        print(f"[ERROR] Problema al restaurar backup: {e}")
        return False

if __name__ == '__main__':

    print("\n" + "=" * 60)
    print("[*] UTILIDAD DE BACKUP DE BASE DE DATOS")
    print("=" * 60)

    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()

        if comando == 'backup' or comando == 'hacer':
            hacer_backup()

        elif comando == 'listar' or comando == 'list':
            listar_backups()

        elif comando == 'restaurar' or comando == 'restore':
            if len(sys.argv) < 3:
                print("[ERROR] Especifica el nombre del backup a restaurar")
                print("Uso: python backup_db.py restaurar <nombre_archivo>")
                print("\nBackups disponibles:")
                listar_backups()
            else:
                nombre_backup = sys.argv[2]
                restaurar_backup(nombre_backup)

        else:
            print(f"[ERROR] Comando no reconocido: {comando}")
            print("\nComandos disponibles:")
            print("  backup    - Hacer backup de la BD actual")
            print("  listar    - Listar todos los backups disponibles")
            print("  restaurar - Restaurar un backup especifico")

    else:
        print("\n[*] USO:")
        print("  Hacer backup:")
        print("    python backup_db.py backup")
        print("\n  Listar backups:")
        print("    python backup_db.py listar")
        print("\n  Restaurar backup:")
        print("    python backup_db.py restaurar <nombre_archivo>")
        print("\nEjemplo:")
        print("    python backup_db.py restaurar recetas_backup_2025-10-29_14-30-45.db")
        print("\n" + "=" * 60)
