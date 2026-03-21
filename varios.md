##Base de Datos
Tipo :MariaDB
IP Servidor: 192.168.0.100
user root: root
password root: Isijoa827@
base de datos:
Entorno desarrollo : dev_sabor_familia
Entorno Produccion : sabor_familia

revisa todo el codigo para que no tenga referencias a SQLite, ya que ahora estamos migrando a MariaDB

prepara todo para hacer la migracion correcta en produccion, que esta en el servidor 192.168.0.89, usuarios ubuntu 
password Isijoa827@, actualiza las referencias y modificaciones en historial.md, todo.md, readme.md, tambien actualiza el archivo deploy_to_server.py que verifique que se realice la igracion y los cambios para apuntar al servidor de base de datos.

rocura respaldar la base de datos actual de SQLite que esta en el servidor, y actualizar  la base de datos con los datos de SQLite del servidor de produccion a la base dedatos actual en maria DB.

Sera bueno que desde aqui en adelante creemos una base de datos de desarrollo, para no interrumpir la base de datos de produccion, y que apunte automaticamente a una u otra dependiendo del entorno osea en desarrollo utilizar la base de datos de desarrollo pero cuando se envie a el servidor de produccion en 192.168.0.89 usar la base de datos de produccion.
si tienes dudas o necesito aclarar algo me avisas