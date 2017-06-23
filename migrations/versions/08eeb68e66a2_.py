"""empty message

Revision ID: 08eeb68e66a2
Revises: 
Create Date: 2017-06-23 16:29:11.247295

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08eeb68e66a2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('log_file', sa.Column('comment', sa.String(length=300), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('log_file', 'comment')
    # ### end Alembic commands ###
