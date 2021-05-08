"""last seen and groups

Revision ID: 2626be446e3b
Revises: 53466bb654a3
Create Date: 2021-05-08 18:03:16.346826

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2626be446e3b'
down_revision = '53466bb654a3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('last_seen', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_user_last_seen'), 'user', ['last_seen'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_last_seen'), table_name='user')
    op.drop_column('user', 'last_seen')
    # ### end Alembic commands ###
