"""add datasets.progress column"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE datasets ADD COLUMN IF NOT EXISTS progress VARCHAR(50)")


def downgrade():
    op.execute("ALTER TABLE datasets DROP COLUMN IF EXISTS progress")
