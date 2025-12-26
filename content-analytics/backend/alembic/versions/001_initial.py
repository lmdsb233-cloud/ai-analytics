"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Datasets表
    op.create_table(
        'datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('row_count', sa.Integer(), default=0),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Posts表
    op.create_table(
        'posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('data_id', sa.String(100), nullable=False),
        sa.Column('publish_time', sa.DateTime(), nullable=True),
        sa.Column('publish_link', sa.String(500), nullable=True),
        sa.Column('content_type', sa.String(50), nullable=True),
        sa.Column('post_type', sa.String(100), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('style_info', sa.Text(), nullable=True),
        sa.Column('read_7d', sa.Float(), nullable=True),
        sa.Column('interact_7d', sa.Float(), nullable=True),
        sa.Column('visit_7d', sa.Float(), nullable=True),
        sa.Column('want_7d', sa.Float(), nullable=True),
        sa.Column('read_14d', sa.Float(), nullable=True),
        sa.Column('interact_14d', sa.Float(), nullable=True),
        sa.Column('visit_14d', sa.Float(), nullable=True),
        sa.Column('want_14d', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_posts_data_id', 'posts', ['data_id'])

    # Analyses表
    op.create_table(
        'analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('config', postgresql.JSON(), nullable=True),
        sa.Column('progress', sa.String(50), default='0%'),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Analysis Results表
    op.create_table(
        'analysis_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('performance', sa.String(20), nullable=True),
        sa.Column('result_data', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # AI Outputs表
    op.create_table(
        'ai_outputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('strengths', postgresql.JSON(), nullable=True),
        sa.Column('weaknesses', postgresql.JSON(), nullable=True),
        sa.Column('suggestions', postgresql.JSON(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(50), nullable=True),
        sa.Column('tokens_used', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_result_id'], ['analysis_results.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('analysis_result_id')
    )

    # Exports表
    op.create_table(
        'exports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('format', sa.String(20), default='excel'),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('exports')
    op.drop_table('ai_outputs')
    op.drop_table('analysis_results')
    op.drop_table('analyses')
    op.drop_index('ix_posts_data_id', table_name='posts')
    op.drop_table('posts')
    op.drop_table('datasets')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
