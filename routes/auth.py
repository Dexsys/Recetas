import os
import site
import smtplib
import ssl
from email.message import EmailMessage

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func
from extensions import db
from models import User
from forms import LoginForm, RegistrationForm, RequestPasswordResetForm, ResetPasswordForm
from urllib.parse import urlsplit

bp = Blueprint('auth', __name__)


def _normalize_email(value):
    return (value or '').strip().lower()


def _resolve_ca_bundle_path():
    configured_bundle = current_app.config.get('MAIL_CA_BUNDLE')
    if configured_bundle:
        return configured_bundle

    # Detecta certifi si está instalado sin depender de importarlo directamente.
    for base in site.getsitepackages() + [site.getusersitepackages()]:
        candidate = os.path.join(base, 'certifi', 'cacert.pem')
        if os.path.isfile(candidate):
            return candidate

    return None


def _build_smtp_ssl_context():
    cafile = _resolve_ca_bundle_path()
    context = ssl.create_default_context(cafile=cafile) if cafile else ssl.create_default_context()

    if current_app.config.get('MAIL_TLS_ALLOW_INVALID_CERT', False):
        current_app.logger.warning(
            'MAIL_TLS_ALLOW_INVALID_CERT activo: deshabilitando validacion TLS SMTP (solo desarrollo).'
        )
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    return context


def _looks_like_gmail_app_password(password):
    if not password:
        return False
    compact = ''.join(password.split())
    return len(compact) == 16 and compact.isalnum()


def send_reset_password_email(user):
    token = user.get_reset_password_token()
    reset_link = url_for('auth.reset_password', token=token, _external=True)

    sender = current_app.config.get('MAIL_DEFAULT_SENDER')
    smtp_server = current_app.config.get('MAIL_SERVER')

    if not smtp_server or not sender:
        current_app.logger.warning('SMTP no configurado. Enlace de recuperación para %s: %s', user.email, reset_link)
        return False

    msg = EmailMessage()
    msg['Subject'] = 'Recuperación de contraseña - Recetas'
    msg['From'] = sender
    msg['To'] = user.email
    msg.set_content(
        'Hola,\n\n'
        'Recibimos una solicitud para restablecer tu contraseña.\n'
        f'Usa este enlace (válido por 1 hora):\n{reset_link}\n\n'
        'Si no solicitaste este cambio, puedes ignorar este mensaje.\n'
    )

    port = current_app.config.get('MAIL_PORT', 587)
    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')
    use_ssl = current_app.config.get('MAIL_USE_SSL', False)
    use_tls = current_app.config.get('MAIL_USE_TLS', True)

    timeout = current_app.config.get('MAIL_TIMEOUT', 15)

    try:
        if smtp_server == 'smtp.gmail.com' and username and password and not _looks_like_gmail_app_password(password):
            current_app.logger.warning(
                'Configuracion Gmail detectada pero MAIL_PASSWORD no parece App Password de 16 caracteres.'
            )

        if use_ssl:
            with smtplib.SMTP_SSL(
                smtp_server,
                port,
                timeout=timeout,
                context=_build_smtp_ssl_context(),
            ) as server:
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, port, timeout=timeout) as server:
                if use_tls:
                    server.starttls(context=_build_smtp_ssl_context())
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
        return True
    except Exception:
        current_app.logger.exception('Error enviando correo de recuperación para %s', user.email)
        current_app.logger.warning('Enlace de recuperación para %s: %s', user.email, reset_link)
        return False

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        email = _normalize_email(form.email.data)
        user = User.query.filter(func.lower(User.email) == email).first()
        if user is None or not user.check_password(form.password.data):
            flash('Email o contraseña inválidos', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        email = _normalize_email(form.email.data)
        if User.query.filter_by(username=form.username.data).first():
            flash('El nombre de usuario ya está en uso.', 'error')
            return redirect(url_for('auth.register'))
        if User.query.filter(func.lower(User.email) == email).first():
            flash('El email ya está en uso.', 'error')
            return redirect(url_for('auth.register'))

        is_first = User.query.count() == 0
        role = 'admin' if is_first else 'invitado'

        user = User(username=form.username.data, email=email, role=role)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Felicidades, te has registrado exitosamente!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Registrarse', form=form)


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        email = _normalize_email(form.email.data)
        user = User.query.filter(func.lower(User.email) == email).first()
        if user:
            sent = send_reset_password_email(user)
            if not sent:
                flash('No fue posible enviar el correo automáticamente. Contacta al administrador.', 'warning')
        flash('Si el email existe, se ha enviado un enlace de recuperación.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', title='Recuperar contraseña', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.verify_reset_password_token(token)
    if not user:
        flash('El enlace de recuperación es inválido o expiró.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Tu contraseña fue actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', title='Nueva contraseña', form=form)
