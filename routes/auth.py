from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user
from extensions import db
from models import User
from forms import LoginForm, RegistrationForm
from urllib.parse import urlsplit

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
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
        if User.query.filter_by(username=form.username.data).first():
            flash('El nombre de usuario ya está en uso.', 'error')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=form.email.data).first():
            flash('El email ya está en uso.', 'error')
            return redirect(url_for('auth.register'))

        is_first = User.query.count() == 0
        role = 'admin' if is_first else 'invitado'

        user = User(username=form.username.data, email=form.email.data, role=role)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Felicidades, te has registrado exitosamente!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Registrarse', form=form)
