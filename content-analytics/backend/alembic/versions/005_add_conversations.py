"""add conversations and conversation_messages tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 conversations 表
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('context_type', sa.String(length=20), nullable=False, server_default='general'),
        sa.Column('context_analysis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('context_analysis_result_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['context_analysis_id'], ['analyses.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['context_analysis_result_id'], ['analysis_results.id'], ondelete='SET NULL'),
    )
    
    # 创建索引
    op.create_index('ix_conversations_user_id_updated_at', 'conversations', ['user_id', 'updated_at'])
    op.create_index('ix_conversations_context_analysis', 'conversations', ['context_analysis_id'])
    op.create_index('ix_conversations_context_result', 'conversations', ['context_analysis_result_id'])
    
    # 创建 conversation_messages 表
    op.create_table(
        'conversation_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tokens_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )
    
    # 创建索引
    op.create_index('ix_conversation_messages_conversation_id', 'conversation_messages', ['conversation_id'])
    op.create_index('ix_conversation_messages_created_at', 'conversation_messages', ['created_at'])


def downgrade():
    op.drop_index('ix_conversation_messages_created_at', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_conversation_id', table_name='conversation_messages')
    op.drop_table('conversation_messages')
    
    op.drop_index('ix_conversations_context_result', table_name='conversations')
    op.drop_index('ix_conversations_context_analysis', table_name='conversations')
    op.drop_index('ix_conversations_user_id_updated_at', table_name='conversations')
    op.drop_table('conversations')

