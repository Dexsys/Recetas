from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from extensions import db
from models import User, Recipe, Comment, Category, MenuType, Unit, Ingredient, IngredientPrice, Technique
from decorators import admin_required
import re
import unicodedata

bp = Blueprint('admin', __name__)

def youtube_to_embed(url):
    """Convierte cualquier URL de YouTube al formato embed."""
    if not url:
        return ''
    url = url.strip()
    if 'youtube.com/embed/' in url:
        return url
    m = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
    if m:
        return f'https://www.youtube.com/embed/{m.group(1)}'
    m = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    if m:
        return f'https://www.youtube.com/embed/{m.group(1)}'
    m = re.search(r'vid:([a-zA-Z0-9_-]{11})', url)
    if m:
        return f'https://www.youtube.com/embed/{m.group(1)}'
    return url


def legacy_price_per_kg(price_val, qty_val, unit):
    # Compatibilidad con columna antigua NOT NULL en SQLite
    if qty_val <= 0:
        return price_val
    if unit in ['gr', 'ml', 'cc']:
        return (price_val / qty_val) * 1000
    if unit in ['kg', 'l', 'unidades']:
        return price_val / qty_val
    return price_val


def normalize_ingredient_name(value):
    """Normalize ingredient names for accent/case-insensitive comparisons."""
    if not value:
        return ''
    text = ' '.join(value.strip().split())
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    return text.casefold()


def rename_ingredient_references(old_name, new_name):
    """Rename ingredient names in recipe lines using normalized matching."""
    if not old_name or not new_name:
        return 0

    old_norm = normalize_ingredient_name(old_name)
    if not old_norm:
        return 0

    renamed = 0
    for ing in Ingredient.query.all():
        if normalize_ingredient_name(ing.name) == old_norm and ing.name != new_name:
            ing.name = new_name
            renamed += 1
    return renamed

@bp.route('/')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    pending_recipes = Recipe.query.filter_by(is_approved=False).all()
    pending_comments = Comment.query.filter_by(is_approved=False).all()
    categories = Category.query.all()
    menu_types = MenuType.query.all()
    units = Unit.query.all()
    ingredient_prices = IngredientPrice.query.order_by(IngredientPrice.name).all()
    techniques = Technique.query.order_by(Technique.order).all()
    return render_template('admin/dashboard.html',
                         users=users,
                         pending_recipes=pending_recipes,
                         pending_comments=pending_comments,
                         categories=categories,
                         menu_types=menu_types,
                         units=units,
                         ingredient_prices=ingredient_prices,
                         techniques=techniques)

@bp.route('/approve_recipe/<int:recipe_id>')
@login_required
@admin_required
def approve_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    recipe.is_approved = True
    db.session.commit()
    flash(f'Receta "{recipe.title}" aprobada.', 'success')
    return redirect(url_for('admin.dashboard'))

@bp.route('/approve_comment/<int:comment_id>')
@login_required
@admin_required
def approve_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.is_approved = True
    db.session.commit()
    flash('Comentario aprobado.', 'success')
    return redirect(url_for('admin.dashboard'))

@bp.route('/change_role/<int:user_id>/<string:new_role>')
@login_required
@admin_required
def change_role(user_id, new_role):
    if new_role not in ['admin', 'colaborador', 'invitado']:
        flash('Rol inválido.', 'error')
        return redirect(url_for('admin.dashboard'))
    user = User.query.get_or_404(user_id)
    if user.id == 1 and new_role != 'admin':
        flash('No puedes quitarle el rol de admin al superusuario.', 'error')
        return redirect(url_for('admin.dashboard'))
    user.role = new_role
    db.session.commit()
    flash(f'Rol de {user.username} cambiado a {new_role}.', 'success')
    return redirect(url_for('admin.dashboard'))

@bp.route('/add_item/<model_type>', methods=['POST'])
@login_required
@admin_required
def add_item(model_type):
    name = request.form.get('name')
    if name:
        if model_type == 'category':
            db.session.add(Category(name=name))
        elif model_type == 'menu_type':
            db.session.add(MenuType(name=name))
        elif model_type == 'unit':
            db.session.add(Unit(name=name))
        db.session.commit()
        flash('Ítem agregado exitosamente.', 'success')
    return redirect(url_for('admin.dashboard'))

@bp.route('/delete_item/<model_type>/<int:item_id>')
@login_required
@admin_required
def delete_item(model_type, item_id):
    model = None
    if model_type == 'category':
        model = Category
    elif model_type == 'menu_type':
        model = MenuType
    elif model_type == 'unit':
        model = Unit
    
    if model:
        item = model.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash('Ítem eliminado.', 'success')
    return redirect(url_for('admin.dashboard'))


# ── Precios de ingredientes ────────────────────────────────────────────────────

@bp.route('/ingredient_prices/add', methods=['POST'])
@login_required
@admin_required
def add_ingredient_price():
    name = request.form.get('name', '').strip()
    price_str = request.form.get('price', '').strip()
    qty_str = request.form.get('commercial_qty', '1').strip()
    c_unit = request.form.get('commercial_unit', 'kg').strip()
    url_ref = request.form.get('url_reference', '').strip() or None
    if name and price_str:
        try:
            price_val = float(price_str)
            qty_val = float(qty_str) if qty_str else 1.0
            if qty_val <= 0:
                qty_val = 1.0
            existing = IngredientPrice.query.filter(
                db.func.lower(IngredientPrice.name) == name.lower()
            ).first()
            if existing:
                existing.price = price_val
                existing.commercial_qty = qty_val
                existing.commercial_unit = c_unit
                existing.url_reference = url_ref
                existing.price_per_kg = legacy_price_per_kg(price_val, qty_val, c_unit)
                flash(f'Precio de "{name}" actualizado.', 'success')
            else:
                db.session.add(IngredientPrice(
                    name=name, price=price_val,
                    commercial_qty=qty_val, commercial_unit=c_unit,
                    url_reference=url_ref,
                    price_per_kg=legacy_price_per_kg(price_val, qty_val, c_unit)
                ))
                flash(f'Precio de "{name}" agregado.', 'success')
            db.session.commit()
        except ValueError:
            flash('Precio o cantidad inválidos.', 'error')
    return redirect(url_for('admin.dashboard'))


@bp.route('/ingredient_prices/<int:price_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_ingredient_price(price_id):
    entry = IngredientPrice.query.get_or_404(price_id)
    old_name = entry.name
    name = request.form.get('name', entry.name).strip()
    price_str = request.form.get('price', str(entry.price)).strip()
    qty_str = request.form.get('commercial_qty', str(entry.commercial_qty)).strip()
    c_unit = request.form.get('commercial_unit', entry.commercial_unit).strip()
    url_ref = request.form.get('url_reference', '').strip() or None
    propagate_name = request.form.get('propagate_name') == '1'

    try:
        price_val = float(price_str)
        qty_val = float(qty_str) if qty_str else 1.0
        if qty_val <= 0:
            qty_val = 1.0
        entry.name = name
        entry.price = price_val
        entry.commercial_qty = qty_val
        entry.commercial_unit = c_unit
        entry.url_reference = url_ref
        entry.price_per_kg = legacy_price_per_kg(price_val, qty_val, c_unit)

        renamed_count = 0
        if propagate_name and old_name != name:
            renamed_count = rename_ingredient_references(old_name, name)

        db.session.commit()
        if renamed_count > 0:
            flash(f'Precio de "{entry.name}" actualizado. Se renombraron {renamed_count} referencia(s) en recetas.', 'success')
        else:
            flash(f'Precio de "{entry.name}" actualizado.', 'success')
    except Exception:
        db.session.rollback()
        flash('No se pudo actualizar: revisa si ya existe otro ingrediente con ese nombre.', 'error')
    except ValueError:
        flash('Precio o cantidad inválidos.', 'error')

    return redirect(url_for('admin.dashboard') + '#precios-ingredientes')


@bp.route('/ingredient_prices/<int:price_id>/delete')
@login_required
@admin_required
def delete_ingredient_price(price_id):
    entry = IngredientPrice.query.get_or_404(price_id)
    db.session.delete(entry)
    db.session.commit()
    flash('Precio eliminado.', 'success')
    return redirect(url_for('admin.dashboard'))


# ── Técnicas ───────────────────────────────────────────────────────────────────

@bp.route('/techniques/add', methods=['POST'])
@login_required
@admin_required
def add_technique():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    url = request.form.get('youtube_url', '').strip()
    if title:
        max_order = db.session.query(db.func.max(Technique.order)).scalar() or 0
        db.session.add(Technique(
            title=title,
            description=description,
            youtube_url=youtube_to_embed(url),
            order=max_order + 1
        ))
        db.session.commit()
        flash('Técnica añadida.', 'success')
    return redirect(url_for('admin.dashboard'))


@bp.route('/techniques/<int:technique_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_technique(technique_id):
    tech = Technique.query.get_or_404(technique_id)
    tech.title = request.form.get('title', tech.title).strip()
    tech.description = request.form.get('description', tech.description or '').strip()
    url = request.form.get('youtube_url', '').strip()
    if url:
        tech.youtube_url = youtube_to_embed(url)
    db.session.commit()
    flash('Técnica actualizada.', 'success')
    return redirect(url_for('admin.dashboard') + '#tecnicas')


@bp.route('/techniques/<int:technique_id>/delete')
@login_required
@admin_required
def delete_technique(technique_id):
    tech = Technique.query.get_or_404(technique_id)
    db.session.delete(tech)
    db.session.commit()
    flash('Técnica eliminada.', 'success')
    return redirect(url_for('admin.dashboard'))
