from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='invitado') # admin, colaborador, invitado
    recipes = db.relationship('Recipe', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    original_author = db.Column(db.String(100))
    url_reference = db.Column(db.String(200))
    category = db.Column(db.String(50))
    menu_type = db.Column(db.String(50))
    portions = db.Column(db.String(50))
    prep_time_minutes = db.Column(db.Integer)
    difficulty = db.Column(db.Integer) # 1 to 5
    cost = db.Column(db.Integer) # 1 to 5
    cost_usd = db.Column(db.Float)
    instructions = db.Column(db.Text)
    image_filename = db.Column(db.String(140))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    ingredients = db.relationship('Ingredient', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    images = db.relationship('RecipeImage', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    unit = db.Column(db.String(20))
    name = db.Column(db.String(100), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class MenuType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class IngredientPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False, default=0.0)   # legacy compat con DB actual
    price = db.Column(db.Float, nullable=False, default=0.0)           # CLP que pagas
    commercial_qty = db.Column(db.Float, nullable=False, default=1.0)  # cantidad en la unidad comercial
    commercial_unit = db.Column(db.String(30), nullable=False, default='kg')  # gr, kg, ml, l, unidades
    url_reference = db.Column(db.String(300))

class Technique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    youtube_url = db.Column(db.String(300))  # URL embed de YouTube
    order = db.Column(db.Integer, default=0)

class RecipeImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, default=0)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
