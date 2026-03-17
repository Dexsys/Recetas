"""initial schema

Revision ID: 59cb1472f941
Revises: 
Create Date: 2026-03-17 15:50:52.961285

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59cb1472f941'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)

    op.create_table(
        'category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'menu_type',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'unit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'ingredient_price',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price_per_kg', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('commercial_qty', sa.Float(), nullable=False),
        sa.Column('commercial_unit', sa.String(length=30), nullable=False),
        sa.Column('url_reference', sa.String(length=300), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'technique',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=140), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('youtube_url', sa.String(length=300), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'recipe',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=140), nullable=False),
        sa.Column('original_author', sa.String(length=100), nullable=True),
        sa.Column('url_reference', sa.String(length=200), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('menu_type', sa.String(length=50), nullable=True),
        sa.Column('portions', sa.String(length=50), nullable=True),
        sa.Column('prep_time_minutes', sa.Integer(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('image_filename', sa.String(length=140), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipe_created_at'), 'recipe', ['created_at'], unique=False)

    op.create_table(
        'comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('recipe_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipe.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comment_created_at'), 'comment', ['created_at'], unique=False)

    op.create_table(
        'ingredient',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipe.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'recipe_image',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=200), nullable=False),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('recipe_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipe.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('recipe_image')
    op.drop_table('ingredient')
    op.drop_index(op.f('ix_comment_created_at'), table_name='comment')
    op.drop_table('comment')
    op.drop_index(op.f('ix_recipe_created_at'), table_name='recipe')
    op.drop_table('recipe')
    op.drop_table('technique')
    op.drop_table('ingredient_price')
    op.drop_table('unit')
    op.drop_table('menu_type')
    op.drop_table('category')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
