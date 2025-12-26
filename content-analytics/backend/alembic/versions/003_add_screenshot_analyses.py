"""add screenshot_analyses table

Revision ID: 003
Revises: 002
Create Date: 2025-12-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'screenshot_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('image_path', sa.String(500), nullable=False, comment='图片存储路径'),
        sa.Column('summary', sa.Text(), comment='总结'),
        sa.Column('strengths', postgresql.JSON(), comment='优点列表'),
        sa.Column('weaknesses', postgresql.JSON(), comment='问题列表'),
        sa.Column('suggestions', postgresql.JSON(), comment='建议列表'),
        sa.Column('model_name', sa.String(100), comment='使用的AI模型'),
        sa.Column('tokens_used', postgresql.JSON(), comment='Token使用情况'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), comment='创建时间'),
        comment='截图分析记录表'
    )

    # 创建索引
    op.create_index('ix_screenshot_analyses_user_id_created_at', 'screenshot_analyses', ['user_id', 'created_at'])


def downgrade():
    op.drop_index('ix_screenshot_analyses_user_id_created_at', 'screenshot_analyses')
    op.drop_table('screenshot_analyses')