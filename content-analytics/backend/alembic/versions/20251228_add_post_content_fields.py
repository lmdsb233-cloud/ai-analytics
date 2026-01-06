"""add post content fields"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column('content_title', sa.String(length=255), nullable=True))
    op.add_column('posts', sa.Column('content_text', sa.Text(), nullable=True))
    op.add_column('posts', sa.Column('cover_image', sa.String(length=1000), nullable=True))
    op.add_column('posts', sa.Column('image_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    op.drop_column('posts', 'image_urls')
    op.drop_column('posts', 'cover_image')
    op.drop_column('posts', 'content_text')
    op.drop_column('posts', 'content_title')
