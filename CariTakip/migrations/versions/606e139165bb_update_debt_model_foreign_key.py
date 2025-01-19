"""Update Debt model foreign key"""

from alembic import op
import sqlalchemy as sa


revision = '606e139165bb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create user table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(80), nullable=False, unique=True),
        sa.Column('email', sa.String(120), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(128))
    )
    # Add user_id column to debt table
    op.add_column('debt', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_debt_user_id', 'debt', 'user', ['user_id'], ['id'])


def downgrade():
    """
    Downgrade function to revert schema changes from this migration.
    """
    # Drop the foreign key constraint
    op.drop_constraint('fk_debt_user_id', 'debt', type_='foreignkey')
    # Drop the user_id column
    op.drop_column('debt', 'user_id')
    # Drop the user table
    op.drop_table('user')
