"""Update Debt model foreign key"""

from alembic import op
import sqlalchemy as sa


revision = '606e139165bb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
  def upgrade():
    # op.add_column('debt', sa.Column('user_id', sa.Integer(), nullable=False))
 
   def downgrade():
    """
    Downgrade function to revert schema changes from this migration.
    """
    # Drop the foreign key constraint
    op.drop_constraint('fk_debt_user_id', 'debt', type_='foreignkey')
    # Drop the user_id column
    op.drop_column('debt', 'user_id')