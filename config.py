import os

basedir = os.path.abspath(os.path.dirname(__file__))


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def env_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sabor-familia-secreto-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance/sabor_familia.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'uploads')
    # Limite total del body HTTP (texto + imagenes) en MB.
    MAX_CONTENT_LENGTH_MB = env_int('MAX_CONTENT_LENGTH_MB', 50)
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH_MB * 1024 * 1024

    # SMTP para recuperación de contraseña
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = env_bool('MAIL_USE_TLS', True)
    MAIL_USE_SSL = env_bool('MAIL_USE_SSL', False)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')
