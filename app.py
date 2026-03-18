import os
from flask import Flask, render_template
from config import Config
from sqlalchemy import inspect as sqlalchemy_inspect
from extensions import db, login_manager, migrate


def seed_reference_data():
    """Seed catalog tables only when schema already exists."""
    inspector = sqlalchemy_inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {"category", "menu_type", "unit", "technique"}
    if not required_tables.issubset(existing_tables):
        return

    from models import Category, MenuType, Unit, Technique

    changed = False

    if not Category.query.first():
        db.session.add_all([Category(name=n) for n in ['Tortas', 'Kuchenes', 'Queques', 'Mermeladas', 'Mistelas y Licores', 'Otros']])
        changed = True

    if not MenuType.query.first():
        db.session.add_all([MenuType(name=n) for n in ['Postre', 'Almuerzo', 'Cena', 'Desayuno/Once', 'Picoteo']])
        changed = True

    default_units = ['gr', 'kg', 'ml', 'cc', 'l', 'taza(s)', 'cda(s)', 'cdita(s)', 'unidad(es)', 'pizca', 'al gusto']
    existing_units = {unit.name for unit in Unit.query.all()}
    missing_units = [Unit(name=name) for name in default_units if name not in existing_units]
    if missing_units:
        db.session.add_all(missing_units)
        changed = True

    if not Technique.query.first():
        db.session.add_all([
            Technique(title='Claras a Punto de Nieve',
                      description='El punto de nieve perfecto se logra batiendo claras a temperatura ambiente en un bol totalmente limpio y sin rastros de grasa o yema. ¡Ideal para merengues y bizcochos esponjosos!',
                      youtube_url='https://www.youtube.com/embed/Qu5-0ZLeboc', order=1),
            Technique(title='Derretir a Baño María',
                      description='Una técnica suave e indirecta de dar calor para derretir chocolate o hacer cremas sin peligro de que se quemen. El agua hirviendo nunca debe tocar la base del bol superior.',
                      youtube_url='https://www.youtube.com/embed/5T8L_7-B2t0', order=2),
            Technique(title='Punto de Caramelo',
                      description='Aprende el color ámbar exacto que necesitas antes de que el azúcar se queme. Paciencia y no remover con cuchara, sino moviendo la olla directamente.',
                      youtube_url='https://www.youtube.com/embed/Xm_w75gT5jQ', order=3),
        ])
        changed = True

    if changed:
        db.session.commit()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

    from models import User
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    with app.app_context():
        from routes.auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from routes.admin import bp as admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')

        from routes.recipes import bp as recipes_bp
        app.register_blueprint(recipes_bp, url_prefix='/recipes')

        from routes.main import bp as main_bp
        app.register_blueprint(main_bp)

        seed_reference_data()

    from flask import send_from_directory
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5110, debug=True)
