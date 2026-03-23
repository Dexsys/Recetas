# Sistema de Gestión de Recetas Familiares

Proyecto web en Flask para administrar recetas, usuarios, tecnicas y comentarios.

## Estado

- Version: 1.2026.0322
- Ultima actualizacion: 2026-03-22
- Entorno recomendado: .venv

## Correcciones recientes (2026-03-21)

- Corregido error 500 al crear/editar recetas cuando un ingrediente ya existia en `ingredient_price` (`Duplicate entry ... for key 'name'`, MariaDB 1062).
- La validacion de auto-registro de precios de ingredientes en backend ahora consulta existencia case-insensitive antes de insertar.

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

- Motor: MariaDB (mysql+pymysql). El esquema se gestiona con Alembic (Flask-Migrate).
- **Desarrollo**: base de datos `dev_sabor_familia` en 192.168.0.100
- **Produccion**: base de datos `sabor_familia` en 192.168.0.100
- La seleccion es automatica segun el archivo `.env` activo.

### Configuracion de entornos

| Entorno      | Archivo  | DB_NAME              | Cuando se usa             |
|--------------|----------|----------------------|---------------------------|
| Desarrollo   | `.env`   | `dev_sabor_familia`  | Maquina local             |
| Produccion   | `.env.prod` | `sabor_familia`  | Servidor 192.168.0.89     |

Para crear la base de datos de desarrollo por primera vez:

   python setup_dev_db.py

Para importar datos del SQLite del servidor a MariaDB (una sola vez):

   python import_prod_sqlite.py

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

- Respaldo completo (DB + uploads + GitHub):

   python full_backup.py

- Respaldo completo sin push a GitHub:

   python full_backup.py --skip-github

- Listar backups:

  python backup_db.py listar

- Restaurar backup:

   python backup_db.py restaurar <nombre_archivo.sql>

- Crear BD de desarrollo (primera vez):

   python setup_dev_db.py

- Importar datos SQLite del servidor a MariaDB produccion (una sola vez):

   python import_prod_sqlite.py

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
   - Opcional: `MAIL_CA_BUNDLE` (ruta a bundle CA PEM), `MAIL_TIMEOUT`
   - Solo desarrollo: `MAIL_TLS_ALLOW_INVALID_CERT=1` para deshabilitar validacion TLS
- Si SMTP no está configurado o falla, el enlace se registra en logs para soporte administrativo.
- En macOS con Python de python.org, si hay errores de certificados tambien puedes ejecutar `Install Certificates.command`.

## Historial

- Ver historial de versiones en historial.md.

