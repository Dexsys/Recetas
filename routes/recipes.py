from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Recipe, Ingredient, Category, MenuType, Unit, IngredientPrice, RecipeImage
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime
import urllib.request
import json
from rich_text import sanitize_rich_text, normalize_rich_text_for_editor

def get_usd_rate(date_obj):
    date_str = date_obj.strftime('%d-%m-%Y')
    url = f"https://mindicador.cl/api/dolar/{date_str}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data.get('serie') and len(data['serie']) > 0:
                return data['serie'][0]['valor']
    except Exception:
        pass
    return 950.0  # Fallback manual aprox si falla internet o la API


def get_ingredient_suggestions():
    ingredient_names = [row[0] for row in db.session.query(Ingredient.name).distinct().all() if row[0]]
    priced_names = [row[0] for row in db.session.query(IngredientPrice.name).distinct().all() if row[0]]
    suggestions = sorted({name.strip() for name in ingredient_names + priced_names if name and name.strip()}, key=str.lower)
    return suggestions


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
        return None, None, None

    commercial_unit = (price_entry.commercial_unit or '').strip().lower()
    recipe_unit = (ingredient.unit or '').strip().lower()

    if commercial_unit == 'unidades':
        if price_entry.commercial_qty <= 0 or recipe_unit != 'unidad(es)':
            return None, None, None
        price_per_unit = price_entry.price / price_entry.commercial_qty
        return amount, 'ud.', round(amount * price_per_unit)

    if commercial_unit in WEIGHT_COMMERCIAL:
        total_base_qty = price_entry.commercial_qty * WEIGHT_COMMERCIAL[commercial_unit]
        display_unit = 'gr'
    elif commercial_unit in VOLUME_COMMERCIAL:
        total_base_qty = price_entry.commercial_qty * VOLUME_COMMERCIAL[commercial_unit]
        display_unit = 'cc'
    else:
        return None, None, None

    if total_base_qty <= 0:
        return None, None, None

    equivalent_qty = UNIT_EQUIVALENTS.get(recipe_unit)
    if equivalent_qty is None or equivalent_qty <= 0:
        return None, None, None

    unit_price = price_entry.price / total_base_qty
    return equivalent_qty * amount, display_unit, round(equivalent_qty * amount * unit_price)

bp = Blueprint('recipes', __name__)

@bp.route('/')
@login_required
def index():
    recipes = current_user.recipes.all()
    all_prices = IngredientPrice.query.all()

    def _compute_recipe_cost(recipe):
        total = 0
        for ing in recipe.ingredients:
            price_entry = find_matching_price(all_prices, ing.name)
            if not price_entry or not ing.amount:
                continue
            _, _, line_cost = compute_ingredient_cost(price_entry, ing)
            if line_cost is not None:
                total += line_cost
        return total if total > 0 else None

    calculated_costs = {r.id: _compute_recipe_cost(r) for r in recipes}
    return render_template('recipes/index.html', title='Mis Recetas', recipes=recipes, calculated_costs=calculated_costs)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        menu_type = request.form.get('menu_type')
        portions = request.form.get('portions')
        prep_time = request.form.get('prep_time')
        difficulty = request.form.get('difficulty')
        cost = request.form.get('cost')
        instructions_raw = request.form.get('instructions', '')
        instructions = sanitize_rich_text(instructions_raw)
        original_author = request.form.get('original_author')
        url_reference = request.form.get('url_reference')

        if not instructions:
            flash('La preparación no puede estar vacía.', 'error')
            return redirect(url_for('recipes.create'))
        
        # Guardar Imágenes (múltiples)
        image_filename = None
        saved_extra_files = []
        uploaded_files = request.files.getlist('images')
        for idx, file in enumerate(uploaded_files):
            if file and file.filename != '':
                fn = secure_filename(file.filename)
                new_fn = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}_{fn}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], new_fn))
                if idx == 0:
                    image_filename = new_fn
                else:
                    saved_extra_files.append(new_fn)

        is_approved = current_user.role == 'admin'

        try:
            cost_val = int(cost) if cost else None
        except ValueError:
            cost_val = None
        
        cost_usd_val = None
        if cost_val:
            rate = get_usd_rate(datetime.now())
            cost_usd_val = round(cost_val / rate, 2) if rate > 0 else None

        recipe = Recipe(
            title=title,
            category=category,
            menu_type=menu_type,
            portions=portions,
            prep_time_minutes=prep_time if prep_time else None,
            difficulty=difficulty if difficulty else None,
            cost=cost_val,
            cost_usd=cost_usd_val,
            instructions=instructions,
            original_author=original_author,
            url_reference=url_reference,
            image_filename=image_filename,
            is_approved=is_approved,
            author=current_user
        )
        db.session.add(recipe)
        db.session.commit()

        # Imágenes adicionales (desde index 1 en adelante)
        for order_idx, fn in enumerate(saved_extra_files, start=1):
            db.session.add(RecipeImage(filename=fn, recipe_id=recipe.id, order=order_idx))
        
        # Procesar ingredientes extraídos de Vanilla JS
        ingredient_names = request.form.getlist('ingredient_name[]')
        ingredient_amounts = request.form.getlist('ingredient_amount[]')
        ingredient_units = request.form.getlist('ingredient_unit[]')

        existing_price_names = {p.name.lower() for p in IngredientPrice.query.all()}
        for i in range(len(ingredient_names)):
            name = ingredient_names[i].strip()
            if name != '':
                amount = float(ingredient_amounts[i]) if ingredient_amounts[i] else None
                ing = Ingredient(
                    name=name,
                    amount=amount,
                    unit=ingredient_units[i],
                    recipe=recipe
                )
                db.session.add(ing)
                # Auto-registrar en IngredientPrice si no existe aún
                if name.lower() not in existing_price_names:
                    db.session.add(IngredientPrice(
                        name=name,
                        price=0.0,
                        price_per_kg=0.0,
                        commercial_qty=1.0,
                        commercial_unit='kg'
                    ))
                    existing_price_names.add(name.lower())
        
        db.session.commit()
        
        if is_approved:
            flash('Receta publicada con éxito.', 'success')
        else:
            flash('Receta enviada a revisión. Un administrador la aprobará pronto.', 'success')
            
        return redirect(url_for('recipes.index'))

    categories = Category.query.all()
    menu_types = MenuType.query.all()
    units = Unit.query.all()
    ingredient_suggestions = get_ingredient_suggestions()
    
    return render_template('recipes/create.html', title='Crear Receta', categories=categories, menu_types=menu_types, units=units,
                           ingredient_suggestions=ingredient_suggestions)

@bp.route('/<int:recipe_id>')
def detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if not recipe.is_approved:
        if not current_user.is_authenticated or (current_user.id != recipe.user_id and current_user.role != 'admin'):
            flash('Esta receta está pendiente de aprobación.', 'error')
            return redirect(url_for('main.index'))

    all_prices = IngredientPrice.query.all()

    cost_breakdown = []
    total_estimated_cost = 0
    for ing in recipe.ingredients:
        price_entry = find_matching_price(all_prices, ing.name)
        qty_display = None
        qty_unit = None
        line_cost = None
        if price_entry and ing.amount:
            qty_display, qty_unit, line_cost = compute_ingredient_cost(price_entry, ing)
            if line_cost is not None:
                total_estimated_cost += line_cost
        cost_breakdown.append({
            'ing': ing,
            'price_entry': price_entry,
            'qty_display': qty_display,
            'qty_unit': qty_unit,
            'line_cost': line_cost,
        })

    all_images = ([recipe.image_filename] if recipe.image_filename else []) + \
                 [img.filename for img in recipe.images.order_by(RecipeImage.order)]

    category_name = (recipe.category or '').lower()
    menu_name = (recipe.menu_type or '').lower()
    theme = {
        'slug': 'cocina-casera',
        'label': 'Cocina casera',
        'accent': 'Sabores del hogar',
        'elements': ['ajo', 'hierbas', 'madera', 'cerámica'],
    }

    if category_name in ['tortas', 'kuchenes', 'queques'] or menu_name == 'postre':
        theme = {
            'slug': 'dulce-horno',
            'label': 'Pastelería familiar',
            'accent': 'Mantequilla, vainilla y fruta horneada',
            'elements': ['vainilla', 'crema', 'frutos rojos', 'glasé'],
        }
    elif category_name in ['mermeladas', 'mistelas y licores']:
        theme = {
            'slug': 'frascos-despensa',
            'label': 'Despensa artesanal',
            'accent': 'Fruta cocida, especias y frascos de cocina',
            'elements': ['frascos', 'canela', 'cítricos', 'azúcar rubia'],
        }
    elif menu_name in ['almuerzo', 'cena']:
        theme = {
            'slug': 'mesa-salada',
            'label': 'Mesa salada',
            'accent': 'Hierbas, aceite de oliva y cocina lenta',
            'elements': ['romero', 'ajo', 'aceite', 'pimienta'],
        }
    elif menu_name == 'desayuno/once':
        theme = {
            'slug': 'desayuno-once',
            'label': 'Desayuno y once',
            'accent': 'Miel, café y horno tibio',
            'elements': ['café', 'miel', 'canela', 'mermelada'],
        }

    return render_template('recipes/detail.html', title=recipe.title, recipe=recipe,
                           cost_breakdown=cost_breakdown,
                           total_estimated_cost=total_estimated_cost,
                           has_any_price=len(all_prices) > 0,
                           all_images=all_images,
                           recipe_theme=theme)

from models import Comment

@bp.route('/<int:recipe_id>/comment', methods=['POST'])
@login_required
def comment(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    text = request.form.get('text')
    
    # Autoaprobar si es admin, de lo contrario pendiente
    is_approved = current_user.role == 'admin'
    
    if text:
        new_comment = Comment(text=text, recipe=recipe, author=current_user, is_approved=is_approved)
        db.session.add(new_comment)
        db.session.commit()
        if is_approved:
            flash('Comentario publicado correctamente.', 'success')
        else:
            flash('Tu comentario fue enviado y está pendiente de aprobación por el administrador.', 'success')
    
    return redirect(url_for('recipes.detail', recipe_id=recipe.id))

@bp.route('/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Only author or admin can edit
    if current_user.id != recipe.user_id and current_user.role != 'admin':
        flash('No tienes permiso para editar esta receta.', 'error')
        return redirect(url_for('recipes.detail', recipe_id=recipe.id))
        
    if request.method == 'POST':
        recipe.title = request.form.get('title')
        recipe.original_author = request.form.get('original_author')
        recipe.url_reference = request.form.get('url_reference')
        recipe.category = request.form.get('category')
        recipe.menu_type = request.form.get('menu_type')
        recipe.portions = request.form.get('portions')
        recipe.prep_time_minutes = request.form.get('prep_time', type=int)
        recipe.difficulty = request.form.get('difficulty', type=int)
        cost_input = request.form.get('cost')
        try:
            cost_val = int(cost_input) if cost_input else None
        except ValueError:
            cost_val = None
            
        recipe.cost = cost_val
        if cost_val:
            rate = get_usd_rate(recipe.created_at or datetime.now())
            recipe.cost_usd = round(cost_val / rate, 2) if rate > 0 else None
        else:
            recipe.cost_usd = None
            
        instructions_raw = request.form.get('instructions', '')
        recipe.instructions = sanitize_rich_text(instructions_raw)
        if not recipe.instructions:
            flash('La preparación no puede estar vacía.', 'error')
            return redirect(url_for('recipes.edit', recipe_id=recipe.id))
        recipe.updated_at = datetime.now()

        # Eliminar imagen principal si fue marcada
        if request.form.get('delete_main_image'):
            recipe.image_filename = None

        # Eliminar imágenes extra marcadas
        delete_ids = request.form.getlist('delete_image_id[]')
        for img_id in delete_ids:
            try:
                img = RecipeImage.query.get(int(img_id))
                if img and img.recipe_id == recipe.id:
                    db.session.delete(img)
            except (ValueError, TypeError):
                pass

        # Nuevas imágenes subidas
        new_files = request.files.getlist('images')
        max_order_val = db.session.query(db.func.max(RecipeImage.order)).filter_by(recipe_id=recipe.id).scalar() or 0
        for idx, file in enumerate(new_files):
            if file and file.filename != '':
                fn = secure_filename(file.filename)
                unique_fn = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}_{fn}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_fn))
                if not recipe.image_filename:
                    recipe.image_filename = unique_fn
                else:
                    max_order_val += 1
                    db.session.add(RecipeImage(filename=unique_fn, recipe_id=recipe.id, order=max_order_val))
            
        # Re-create ingredients (clear old, add new ones)
        Ingredient.query.filter_by(recipe_id=recipe.id).delete()
        amounts = request.form.getlist('ingredient_amount[]')
        units = request.form.getlist('ingredient_unit[]')
        names = request.form.getlist('ingredient_name[]')
        
        existing_price_names = {p.name.lower() for p in IngredientPrice.query.all()}
        for amount, unit, name in zip(amounts, units, names):
            name = name.strip()
            if name:
                try:
                    amt = float(amount) if amount else None
                except ValueError:
                    amt = None
                ing = Ingredient(amount=amt, unit=unit, name=name, recipe=recipe)
                db.session.add(ing)
                # Auto-registrar en IngredientPrice si no existe aún
                if name.lower() not in existing_price_names:
                    db.session.add(IngredientPrice(
                        name=name,
                        price=0.0,
                        price_per_kg=0.0,
                        commercial_qty=1.0,
                        commercial_unit='kg'
                    ))
                    existing_price_names.add(name.lower())
        
        db.session.commit()
        flash('Receta actualizada exitosamente.', 'success')
        return redirect(url_for('recipes.detail', recipe_id=recipe.id))

    categories = Category.query.all()
    menu_types = MenuType.query.all()
    units = Unit.query.all()
    ingredient_suggestions = get_ingredient_suggestions()
    
    return render_template('recipes/edit.html', title='Editar Receta', recipe=recipe, categories=categories, menu_types=menu_types, units=units,
                           instructions_editor_html=normalize_rich_text_for_editor(recipe.instructions),
                           ingredient_suggestions=ingredient_suggestions)

@bp.route('/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if current_user.id != recipe.user_id and current_user.role != 'admin':
        flash('No tienes permiso para eliminar esta receta.', 'error')
        return redirect(url_for('recipes.detail', recipe_id=recipe.id))
        
    db.session.delete(recipe)
    db.session.commit()
    flash('Receta eliminada.', 'success')
    return redirect(url_for('main.index'))
