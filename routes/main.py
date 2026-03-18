from flask import Blueprint, render_template, request
from models import Recipe, Ingredient, Category, MenuType, Technique, IngredientPrice


UNIT_EQUIVALENTS = {
    'gr': 1.0,
    'gramo(s)': 1.0,
    'kg': 1000.0,
    'kilogramo(s)': 1000.0,
    'ml': 1.0,
    'cc': 1.0,
    'l': 1000.0,
    'litro(s)': 1000.0,
    'cda(s)': 15.0,
    'cucharada(s)': 15.0,
    'cdita(s)': 5.0,
    'cucharadita(s)': 5.0,
    'taza(s)': 240.0,
    'pizca': 1.0,
    'al gusto': 0.0,
}

WEIGHT_COMMERCIAL = {'gr': 1.0, 'kg': 1000.0}
VOLUME_COMMERCIAL = {'cc': 1.0, 'ml': 1.0, 'l': 1000.0}


def find_matching_price(all_prices, ingredient_name):
    normalized_name = ingredient_name.lower()
    for price_entry in all_prices:
        if price_entry.name.lower() == normalized_name:
            return price_entry
    for price_entry in all_prices:
        if price_entry.name.lower() in normalized_name or normalized_name in price_entry.name.lower():
            return price_entry
    return None


def compute_ingredient_cost(price_entry, ingredient):
    amount = ingredient.amount or 0
    if not amount:
        return None

    commercial_unit = (price_entry.commercial_unit or '').strip().lower()
    recipe_unit = (ingredient.unit or '').strip().lower()

    if commercial_unit == 'unidades':
        if price_entry.commercial_qty <= 0 or recipe_unit != 'unidad(es)':
            return None
        price_per_unit = price_entry.price / price_entry.commercial_qty
        return round(amount * price_per_unit)

    if commercial_unit in WEIGHT_COMMERCIAL:
        total_base_qty = price_entry.commercial_qty * WEIGHT_COMMERCIAL[commercial_unit]
    elif commercial_unit in VOLUME_COMMERCIAL:
        total_base_qty = price_entry.commercial_qty * VOLUME_COMMERCIAL[commercial_unit]
    else:
        return None

    if total_base_qty <= 0:
        return None

    equivalent_qty = UNIT_EQUIVALENTS.get(recipe_unit)
    if equivalent_qty is None or equivalent_qty <= 0:
        return None

    unit_price = price_entry.price / total_base_qty
    return round(equivalent_qty * amount * unit_price)


def compute_recipe_estimated_costs(recipes):
    all_prices = IngredientPrice.query.all()
    estimated = {}

    for recipe in recipes:
        total = 0
        for ing in recipe.ingredients:
            price_entry = find_matching_price(all_prices, ing.name)
            if not price_entry or not ing.amount:
                continue
            line_cost = compute_ingredient_cost(price_entry, ing)
            if line_cost is not None:
                total += line_cost
        estimated[recipe.id] = total if total > 0 else None

    return estimated

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
    estimated_costs = compute_recipe_estimated_costs(recipes)
    categories = Category.query.all()
    menu_types = MenuType.query.all()
    return render_template(
        'index.html',
        recipes=recipes,
        estimated_costs=estimated_costs,
        category=category,
        menu_type=menu_type,
        q=q,
        categories=categories,
        menu_types=menu_types,
    )

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
            estimated_costs = compute_recipe_estimated_costs(recipes)
            
            return render_template('what_to_cook.html', recipes=recipes, estimated_costs=estimated_costs, provided_ings=provided_ings_raw)

@bp.route('/techniques')
def techniques():
    techniques = Technique.query.order_by(Technique.order).all()
    return render_template('techniques.html', title='Técnicas Base', techniques=techniques)


@bp.route('/about')
def about():
    return render_template('about.html', title='Acerca de')
