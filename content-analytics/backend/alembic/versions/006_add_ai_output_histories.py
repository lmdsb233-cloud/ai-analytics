"""add ai_output_histories table"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_output_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ai_output_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False, server_default='update'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('strengths', postgresql.JSON(), nullable=True),
        sa.Column('weaknesses', postgresql.JSON(), nullable=True),
        sa.Column('suggestions', postgresql.JSON(), nullable=True),
        sa.Column('model_name', sa.String(length=50), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('tokens_used', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['ai_output_id'], ['ai_outputs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['analysis_result_id'], ['analysis_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_index(
        'ix_ai_output_histories_ai_output_id_created_at',
        'ai_output_histories',
        ['ai_output_id', 'created_at']
    )
    op.create_index(
        'ix_ai_output_histories_analysis_result_id',
        'ai_output_histories',
        ['analysis_result_id']
    )
    op.create_index(
        'ix_ai_output_histories_user_id',
        'ai_output_histories',
        ['user_id']
    )


def downgrade():
    op.drop_index('ix_ai_output_histories_user_id', table_name='ai_output_histories')
    op.drop_index('ix_ai_output_histories_analysis_result_id', table_name='ai_output_histories')
    op.drop_index('ix_ai_output_histories_ai_output_id_created_at', table_name='ai_output_histories')
    op.drop_table('ai_output_histories')
