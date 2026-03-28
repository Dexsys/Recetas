"""add user approval workflow

Revision ID: b2d9e7f4c111
Revises: a1f4d6c2b9e0
Create Date: 2026-03-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2d9e7f4c111'
down_revision = 'a1f4d6c2b9e0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    )

    # Ajuste de roles legado a nuevo nombre por defecto.
    op.execute(sa.text("UPDATE `user` SET role = 'usuario' WHERE role = 'invitado'"))

    # Los administradores quedan aprobados por defecto.
    op.execute(sa.text("UPDATE `user` SET is_approved = 1 WHERE role = 'admin'"))


def downgrade():
    op.execute(sa.text("UPDATE `user` SET role = 'invitado' WHERE role = 'usuario'"))
    op.drop_column('user', 'is_approved')
