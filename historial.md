# Sistema Recetario Familiar - Historial de Versiones

**Aplicacion** : Sistema de Gestion Recetas Familiares
**URL**        : http://recetas.dexsys.cl
**Repositorio**: https://github.com/Dexsys/Recetas

---
<<<<<<< HEAD
## [1.2026.0328] - 2026-03-28

### Agregado
- Sin cambios registrados.

### Corregido
- Sin cambios registrados.

### Tecnico
- Sin cambios registrados.

### Modificado
- Sin cambios registrados.

### Migracion de Base de Datos
- Sin cambios de esquema.

### Eliminado
- Sin cambios.

### Infraestructura
- Respaldo a GitHub ejecutado mediante backup_to_github.py.
- Deploy a produccion ejecutado mediante deploy_to_server.py.

---

=======
>>>>>>> e94558180f7dfdbc023da4e15692cb4323499fc7
## [1.2026.0322] - 2026-03-22

### Agregado
- Sin cambios registrados.

### Corregido
- Sin cambios registrados.

### Tecnico
- Sin cambios registrados.

### Modificado
- Sin cambios registrados.

### Migracion de Base de Datos
- Sin cambios de esquema.

### Eliminado
- Sin cambios.

### Infraestructura
- Respaldo a GitHub ejecutado mediante backup_to_github.py.
- Deploy a produccion ejecutado mediante deploy_to_server.py.

---

## [1.2026.0321] - 2026-03-21

### Agregado
- Script `setup_dev_db.py`: crea la base de datos de desarrollo `dev_sabor_familia` clonando el esquema de produccion.
- Script `import_prod_sqlite.py`: descarga el SQLite del servidor via SSH/SCP y migra los datos a MariaDB `sabor_familia`.
- Script `full_backup.py`: orquesta respaldo completo (backup DB, compresion de uploads y respaldo de codigo a GitHub en un solo flujo).
- Archivo `.env.prod`: configuracion de produccion separada (no versionada), subida automaticamente al servidor en cada deploy.
- Archivo `.env.example`: plantilla publica de referencia para configurar el entorno.

### Corregido
- `routes/recipes.py`: solucionado error 500 al crear/editar recetas por duplicado en `ingredient_price` (MariaDB 1062, `Duplicate entry ... for key 'name'`).
- La auto-creacion de precios de ingredientes ahora valida existencia en BD en forma case-insensitive antes de insertar, evitando colisiones por mayusculas/minusculas.

### Tecnico
- `config.py`: eliminado el fallback a SQLite. Ahora MariaDB es obligatorio. Si faltan credenciales, se lanza `EnvironmentError` con mensaje claro.
- `config.py`: agregada funcion `_load_dotenv()` que carga automaticamente el archivo `.env` al importar el modulo, sin dependencias externas.
- `backup_db.py`: reescrito completamente para MariaDB usando pymysql. Exporta backups como `.sql` con timestamp. Muestra SQLite legacy en listado si existen.
- `migrate_to_mariadb.py`: credenciales leidas desde variables de entorno (no hardcodeadas). Acepta ruta SQLite como argumento CLI. Funcion `migrate()` reutilizable desde otros scripts.
- `deploy_to_server.py`: nuevo paso `[0]` verifica existencia de `.env.prod` antes del deploy. Nuevo paso `[3.0/4]` sube `.env.prod` al servidor como `.env`. Nuevo paso `[3.1.5/4]` verifica conexion a la base de datos en el servidor.
- `.env`: actualizado a `DB_NAME=dev_sabor_familia` y `APP_ENV=development` para entorno local.
- `.gitignore`: agregado `.env.prod` para que las credenciales de produccion no sean versionadas.

### Migracion de Base de Datos
- Separacion definitiva de entornos: desarrollo usa `dev_sabor_familia`, produccion usa `sabor_familia`, ambas en MariaDB 192.168.0.100.
- Eliminadas todas las referencias a SQLite del codigo de produccion.

### Infraestructura
- Respaldo a GitHub ejecutado mediante backup_to_github.py.
- Deploy a produccion ejecutado mediante deploy_to_server.py.
- Deploy actualizado para subir configuracion de produccion al servidor automaticamente.

---

## [1.2026.0318] - 2026-03-18

### Agregado
- Sin cambios registrados.

### Corregido
- Sin cambios registrados.

### Tecnico
- Sin cambios registrados.

### Modificado
- Sin cambios registrados.

### Migracion de Base de Datos
- Sin cambios de esquema.

### Eliminado
- Sin cambios.

### Infraestructura
- Respaldo a GitHub ejecutado mediante backup_to_github.py.
- Deploy a produccion ejecutado mediante deploy_to_server.py.

---

## [1.2026.0317] - 2026-03-17

### Agregado
- Archivo requirements.txt generado con versiones fijas de dependencias.
- Flujo "Olvidé mi contraseña" con token temporal y formulario de reseteo.

### Corregido
- Password del usuario dexsys@gmail.com actualizada y validada mediante hash.

### Tecnico
- Recreacion del entorno virtual local para asegurar instalacion limpia.
- Estandarizacion de uso del entorno .venv en comandos operativos.
- Refactor de deploy_to_server.py para copiar solo archivos versionados en Git.
- Migraciones de base de datos ejecutadas en servidor remoto durante deploy.
- Cambio de puerto de aplicacion y proxy a 5110 para evitar conflicto en productivo.
- Instalacion automatica de service file systemd durante deploy.
- Instalacion automatica de configuracion Nginx (sites-available/sites-enabled) cuando Nginx existe.
- Validacion preventiva de archivos `git untracked` en deploy_to_server.py para evitar fallos por archivos nuevos no copiados.
- Soporte de reemplazo robusto para fecha en README (actualizacion/actualización) durante tareas automatizadas.

### Modificado
- README.md actualizado con instrucciones de instalacion y ejecucion reales.
- historial.md actualizado con cambios operativos del dia.
- Deploy endurecido para productivo (validaciones, servicio configurable, limpieza de items).
- Nuevo script backup_to_github.py para respaldo con actualizacion previa de documentacion.
- nginx_recetas.conf y nginx_cloudflare.conf ajustados para rutas reales y proxy a 127.0.0.1:5110.
- Configuracion SMTP incorporada para envio de recuperacion de contraseña (con fallback a logs).
- Formularios de receta (crear/editar) con editor de texto enriquecido para la preparacion.
- Vista de detalle de receta adaptada para renderizar preparacion con formato sanitizado.

### Migracion de Base de Datos
- Sin cambios de esquema.

### Eliminado
- Sin cambios.

### Infraestructura
- Respaldo a GitHub ejecutado mediante backup_to_github.py.
- Deploy a produccion ejecutado mediante deploy_to_server.py.
- Sin cambios de despliegue o servidor.
- Regla operativa: antes de deploy o respaldo GitHub se actualizan historial.md y README.md.

---

## [1.2026.0306] - 2026-03-06

### Agregado
- Sin cambios registrados.

### Corregido
- Sin cambios registrados.

### Tecnico
- Sin cambios registrados.

### Modificado
- Sin cambios registrados.

### Migracion de Base de Datos
- Sin cambios registrados.

### Eliminado
- Scripts de migracion de la raiz del proyecto (movidos a Migracion/).
- actualizar_periodo_2025.py
- crear_admin.py
- crear_usuarios_batch.py
- Scripts de migracion de base de datos antiguos.

### Infraestructura
- Respaldo completo en GitHub (Dexsys/Inventario).
- Resolucion de conflictos de merge con rama origin/master.
- Configuracion automatica de hooks de Git para integracion continua.
- Sistema de versionado sincronizado entre codigo y UI.

---

## Notas sobre Versionado

El esquema de version utiliza el formato: 1.AAAA.MMDD

- 1: Numero principal (cambiar unicamente en actualizaciones mayores).
- AAAA: Ano actual.
- MMDD: Mes y dia de la version.

Ejemplo: 1.2026.0317 = Version 1, ano 2026, marzo 17.

