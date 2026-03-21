"""add visit counters

Revision ID: a1f4d6c2b9e0
Revises: 59cb1472f941
Create Date: 2026-03-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1f4d6c2b9e0'
down_revision = '59cb1472f941'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recipe', sa.Column('views', sa.Integer(), nullable=False, server_default=sa.text('0')))

    op.create_table(
        'site_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('total_visits', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.PrimaryKeyConstraint('id')
    )

    op.execute(sa.text('INSERT INTO site_stats (id, total_visits) VALUES (1, 0)'))


def downgrade():
    op.drop_table('site_stats')
    op.drop_column('recipe', 'views')
