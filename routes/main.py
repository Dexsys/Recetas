from flask import Blueprint, render_template, request
from models import Recipe, Ingredient, Category, MenuType, Technique

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    category = request.args.get('category')
    menu_type = request.args.get('menu_type')
    q = request.args.get('q')

    query = Recipe.query.filter_by(is_approved=True)

    if category:
        query = query.filter(Recipe.category == category)
    if menu_type:
        query = query.filter(Recipe.menu_type == menu_type)
    if q:
        query = query.filter(Recipe.title.ilike(f'%{q}%'))

    recipes = query.order_by(Recipe.created_at.desc()).all()
    categories = Category.query.all()
    menu_types = MenuType.query.all()
    return render_template('index.html', recipes=recipes, category=category, menu_type=menu_type, q=q, categories=categories, menu_types=menu_types)

@bp.route('/suggest', methods=['GET', 'POST'])
def suggest():
    recipes = []
    provided_ings_raw = ""
    if request.method == 'POST':
        provided_ings_raw = request.form.get('ingredients', '')
        provided_ings = [i.strip().lower() for i in provided_ings_raw.split(',') if i.strip()]
        if provided_ings:
            all_recipes = Recipe.query.filter_by(is_approved=True).all()
            for r in all_recipes:
                recipe_ings = [i.name.lower() for i in r.ingredients]
                matches = sum(1 for pi in provided_ings if any(pi in ri for ri in recipe_ings))
                if matches > 0:
                    recipes.append((r, matches))
            recipes.sort(key=lambda x: x[1], reverse=True)
            recipes = [r[0] for r in recipes]
            
    return render_template('what_to_cook.html', recipes=recipes, provided_ings=provided_ings_raw)

@bp.route('/techniques')
def techniques():
    techniques = Technique.query.order_by(Technique.order).all()
    return render_template('techniques.html', title='Técnicas Base', techniques=techniques)
