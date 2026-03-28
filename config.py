import os
from pathlib import Path

basedir = os.path.abspath(os.path.dirname(__file__))


def _load_dotenv():
    """Carga el archivo .env del directorio raiz del proyecto en os.environ.

    Solo establece variables que aun no estan definidas en el entorno,
    de modo que las variables del sistema siempre tienen prioridad.
    Esto permite que 'config.py' funcione correctamente tanto en
    desarrollo (leyendo .env local) como en produccion (donde el
    sistema ya tiene las variables definidas via EnvironmentFile).
    """
    env_path = Path(basedir) / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "sabor-familia-secreto-123"

    # ── Base de datos (MariaDB obligatorio) ────────────────────────────────
    _db_host = os.environ.get("DB_HOST")
    _db_port = int(os.environ.get("DB_PORT") or 3306)
    _db_user = os.environ.get("DB_USER")
    _db_password = os.environ.get("DB_PASSWORD")
    _db_name = os.environ.get("DB_NAME")

    if not (_db_host and _db_user and _db_password and _db_name):
        raise EnvironmentError(
            "Faltan credenciales de base de datos MariaDB. "
            "Define DB_HOST, DB_USER, DB_PASSWORD y DB_NAME en el archivo .env"
        )

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or os.path.join(basedir, "uploads")
    # Limite total del body HTTP (texto + imagenes) en MB.
    MAX_CONTENT_LENGTH_MB = env_int("MAX_CONTENT_LENGTH_MB", 50)
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH_MB * 1024 * 1024

    # SMTP para recuperación de contraseña
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = env_bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = env_bool("MAIL_USE_SSL", False)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_TIMEOUT = env_int("MAIL_TIMEOUT", 15)
    MAIL_CA_BUNDLE = os.environ.get("MAIL_CA_BUNDLE")
    MAIL_TLS_ALLOW_INVALID_CERT = env_bool("MAIL_TLS_ALLOW_INVALID_CERT", False)
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get(
        "MAIL_USERNAME"
    )

    # Destinatario administrativo para aprobar/rechazar nuevos registros.
    REGISTRATION_ALERT_EMAIL = os.environ.get("REGISTRATION_ALERT_EMAIL") or "dexsys@gmail.com"
