"""add pdf parser features

Revision ID: 0010_add_pdf_features
Revises: 0009_update_monthly_limits
Create Date: 2026-01-31 00:00:00.000000

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '0010_add_pdf_features'
down_revision = '0009_update_monthly_limits'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add two new features for PDF parsing limits:
    - pdf_uploads_per_month: Monthly limit for PDF uploads
    - pdf_records_per_upload: Max records per single upload

    Plan limits:
    - Basic: 1 upload/month, 20 records/upload
    - Professional: 10 uploads/month, 100 records/upload
    - Enterprise: Unlimited (NULL)
    """

    # Step 1: Add new features to features table
    op.execute("""
        INSERT INTO features (code, name, description)
        VALUES
            ('pdf_uploads_per_month', 'PDF Uploads Per Month',
             'Number of PDF files user can upload per calendar month'),
            ('pdf_records_per_upload', 'PDF Records Per Upload',
             'Maximum number of records that can be processed per single PDF upload')
        ON CONFLICT (code) DO NOTHING;
    """)

    # Step 2: Add plan_features for BASIC plan
    op.execute("""
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'pdf_uploads_per_month', true, 1
        FROM plans p
        WHERE p.code = 'basic'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;

        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'pdf_records_per_upload', true, 20
        FROM plans p
        WHERE p.code = 'basic'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;
    """)

    # Step 3: Add plan_features for PROFESSIONAL plan
    op.execute("""
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'pdf_uploads_per_month', true, 10
        FROM plans p
        WHERE p.code = 'professional'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;

        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'pdf_records_per_upload', true, 100
        FROM plans p
        WHERE p.code = 'professional'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;
    """)

    # Step 4: Add plan_features for ENTERPRISE plan (unlimited = NULL)
    op.execute("""
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'pdf_uploads_per_month', true, NULL
        FROM plans p
        WHERE p.code = 'enterprise'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;

        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'pdf_records_per_upload', true, NULL
        FROM plans p
        WHERE p.code = 'enterprise'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;
    """)


def downgrade() -> None:
    """Remove PDF features"""
    op.execute("""
        DELETE FROM plan_features
        WHERE feature_code IN ('pdf_uploads_per_month', 'pdf_records_per_upload');
    """)
    op.execute("""
        DELETE FROM features
        WHERE code IN ('pdf_uploads_per_month', 'pdf_records_per_upload');
    """)
