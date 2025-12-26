"""Add performance indexes

Revision ID: 002
Revises: 001
Create Date: 2025-12-24 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_datasets_user_id_created_at ON datasets (user_id, created_at)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_posts_dataset_id ON posts (dataset_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_analyses_user_id_created_at ON analyses (user_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_analyses_user_id_dataset_id_created_at "
        "ON analyses (user_id, dataset_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_analysis_results_analysis_id_created_at "
        "ON analysis_results (analysis_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_analysis_results_analysis_id_performance "
        "ON analysis_results (analysis_id, performance)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_analysis_results_analysis_id_post_id "
        "ON analysis_results (analysis_id, post_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_exports_user_id_created_at ON exports (user_id, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_exports_user_id_created_at")
    op.execute("DROP INDEX IF EXISTS ix_analysis_results_analysis_id_post_id")
    op.execute("DROP INDEX IF EXISTS ix_analysis_results_analysis_id_performance")
    op.execute("DROP INDEX IF EXISTS ix_analysis_results_analysis_id_created_at")
    op.execute("DROP INDEX IF EXISTS ix_analyses_user_id_dataset_id_created_at")
    op.execute("DROP INDEX IF EXISTS ix_analyses_user_id_created_at")
    op.execute("DROP INDEX IF EXISTS ix_posts_dataset_id")
    op.execute("DROP INDEX IF EXISTS ix_datasets_user_id_created_at")
