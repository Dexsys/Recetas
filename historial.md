# Sistema Recetario Familiar - Historial de Versiones

**Aplicacion** : Sistema de Gestion Recetas Familiares
**URL**        : http://recetas.dexsys.cl
**Repositorio**: https://github.com/Dexsys/Recetas

---

## [1.2026.0317] - 2026-03-17

### Agregado
- Archivo requirements.txt generado con versiones fijas de dependencias.

### Corregido
- Password del usuario dexsys@gmail.com actualizada y validada mediante hash.

### Tecnico
- Recreacion del entorno virtual local para asegurar instalacion limpia.
- Estandarizacion de uso del entorno .venv en comandos operativos.

### Modificado
- README.md actualizado con instrucciones de instalacion y ejecucion reales.
- historial.md actualizado con cambios operativos del dia.

### Migracion de Base de Datos
- Sin cambios de esquema.

### Eliminado
- Sin cambios.

### Infraestructura
- Sin cambios de despliegue o servidor.

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

