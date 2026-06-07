"""update document model: add s3_key, metadata JSONB, DocumentStatus enum

Revision ID: b1c2d3e4f5a6
Revises: a0ea389122bb
Create Date: 2026-06-07 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "a0ea389122bb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: update document table untuk TASK-016."""

    # 1. Buat DocumentStatus enum type (skip jika sudah ada)
    document_status = sa.Enum(
        "UPLOADED", "PROCESSING", "COMPLETED", "FAILED", name="documentstatus"
    )
    document_status.create(op.get_bind(), checkfirst=True)

    # 2. Tambah kolom s3_key
    op.add_column(
        "document",
        sa.Column("s3_key", sa.String(length=512), nullable=True),
    )

    # 3. Tambah kolom metadata JSONB
    op.add_column(
        "document",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # 4. Konversi kolom status dari VARCHAR ke DocumentStatus enum
    # Pertama migrate nilai yang ada ke nilai uppercase agar cocok dengan enum
    op.execute(
        "UPDATE document SET status = UPPER(status) "
        "WHERE status NOT IN ('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED')"
    )
    # Set default status lama ke COMPLETED (sudah ada sebelum fitur ini)
    op.execute(
        "UPDATE document SET status = 'COMPLETED' "
        "WHERE status NOT IN ('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED')"
    )

    op.alter_column(
        "document",
        "status",
        existing_type=sa.VARCHAR(length=50),
        type_=document_status,
        existing_nullable=False,
        postgresql_using="status::documentstatus",
    )


def downgrade() -> None:
    """Downgrade schema: rollback document table changes."""

    # 1. Konversi enum kembali ke VARCHAR
    op.alter_column(
        "document",
        "status",
        existing_type=sa.Enum(
            "UPLOADED", "PROCESSING", "COMPLETED", "FAILED", name="documentstatus"
        ),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )

    # 2. Drop DocumentStatus enum type
    sa.Enum(name="documentstatus").drop(op.get_bind())

    # 3. Hapus kolom metadata
    op.drop_column("document", "metadata")

    # 4. Hapus kolom s3_key
    op.drop_column("document", "s3_key")
