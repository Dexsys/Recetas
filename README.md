# Sistema de Gestion de Recetas Familiares

Proyecto web en Flask para administrar recetas, usuarios, tecnicas y comentarios.

## Estado

- Version: 1.2026.0317
- Ultima actualizacion: 2026-03-17
- Entorno recomendado: .venv

## Requisitos

- Python 3.12+ (compatible con 3.14)
- pip actualizado
- Dependencias en requirements.txt

## Instalacion

### Windows (PowerShell)

1. Crear entorno virtual:

   python -m venv .venv

2. Activar entorno:

   .\.venv\Scripts\Activate.ps1

3. Instalar dependencias:

   pip install -r requirements.txt

### Linux/macOS

1. Crear entorno virtual:

   python3 -m venv .venv

2. Activar entorno:

   source .venv/bin/activate

3. Instalar dependencias:

   pip install -r requirements.txt

## Ejecucion local

Con el entorno activo:

python app.py

La aplicacion queda disponible en:

- http://127.0.0.1:5080

## Estructura principal

- app.py: fabrica y arranque de la app Flask.
- config.py: configuracion general.
- models.py: modelos SQLAlchemy.
- routes/: blueprints (auth, admin, recipes, main).
- templates/: vistas HTML.
- static/: css, js e imagenes.
- uploads/: archivos subidos.
- requirements.txt: dependencias Python fijadas.
- historial.md: historial de cambios por version.

## Base de datos

- Archivo principal: instance/sabor_familia.db (si esta configurado en instancia).
- El esquema se gestiona con migraciones Alembic (Flask-Migrate).

### Comandos de migracion

Con el entorno activo:

1. Aplicar migraciones pendientes:

   flask db upgrade

2. Crear una nueva migracion desde cambios en modelos:

   flask db migrate -m "descripcion del cambio"

3. Aplicar la nueva migracion:

   flask db upgrade

4. (Opcional) Volver una revision atras:

   flask db downgrade -1

## Utilidades

- Backup:

  python backup_db.py backup

- Listar backups:

  python backup_db.py listar

## Notas operativas

- Si existen tanto venv como .venv, usar solo .venv para evitar confusiones.
- Si cambias dependencias, volver a generar requirements.txt.

## Historial

- Ver historial de versiones en historial.md.

