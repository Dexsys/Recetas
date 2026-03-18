# Sistema de Gestión de Recetas Familiares

Proyecto web en Flask para administrar recetas, usuarios, tecnicas y comentarios.

## Estado

- Version: 1.2026.0318
- Ultima actualizacion: 2026-03-18
- Entorno recomendado: .venv

## Requisitos

- Python 3.12+ (compatible con 3.14)
- pip actualizado
- Dependencias en requirements.txt

## Instalación

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

La aplicación queda disponible en:

- http://127.0.0.1:5110

sudo systemctl daemon-reload && sudo systemctl enable recetas && sudo systemctl restart recetas
sudo journalctl -u recetas -n 30 
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

- Respaldo a GitHub (actualiza historial/readme antes de push):

   python backup_to_github.py

- Deploy a servidor (actualiza historial/TODO/README y valida requirements cuando aplica):

   python deploy_to_server.py

## Notas operativas

- Si existen tanto venv como .venv, usar solo .venv para evitar confusiones.
- Si cambias dependencias, volver a generar requirements.txt.
- Antes de desplegar, el script actualiza automaticamente historial.md, TODO.md y README.md.
- Si detecta cambios Python/migraciones sin cambios en requirements.txt, pedira confirmacion para continuar.
- Puerto de runtime de la app/Gunicorn: 5110.
- El deploy instala/actualiza `recetas.service` en systemd automaticamente.
- El deploy instala/activa configuracion Nginx automaticamente si Nginx está instalado en el servidor.
- El deploy valida archivos `untracked` antes de copiar para evitar errores por modulos nuevos no versionados.
- Si necesitas incluir `untracked` de forma excepcional, usa `DEPLOY_INCLUDE_UNTRACKED=1`.

## Editor de preparacion enriquecido

- La preparacion de recetas usa editor visual (negrita, italica, subrayado, resaltado, listas y citas).
- El contenido HTML se sanitiza en backend antes de guardar para mitigar XSS.
- Dependencias agregadas para sanitizacion: `bleach`, `tinycss2` y `webencodings`.

## Recuperacion de contraseña

- El login incluye la opcion "¿Olvidaste tu contraseña?".
- Para envio real por correo, configurar en `.env`:
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USE_SSL`
   - `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
- Si SMTP no está configurado o falla, el enlace se registra en logs para soporte administrativo.

## Historial

- Ver historial de versiones en historial.md.

