# Safe replacement for RenameIndex — handles ALL scenarios:
# 1. Fresh DB where indexes were already created by initial migration
# 2. Existing DB with old custom index names (org_slug_idx, org_status_idx)
# 3. Existing DB where indexes were already renamed
#
# Uses CREATE INDEX IF NOT EXISTS — safe to run in any state.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organisations', '0006_organisation_industry_sales_notes'),
    ]

    operations = [
        # ── slug index ──────────────────────────────────────────────────────────
        migrations.RunSQL(
            sql='CREATE INDEX IF NOT EXISTS "organisatio_slug_b3fbe9_idx" ON "organisations_organisation" ("slug");',
            reverse_sql='DROP INDEX IF EXISTS "organisatio_slug_b3fbe9_idx";',
        ),
        # ── status index ────────────────────────────────────────────────────────
        migrations.RunSQL(
            sql='CREATE INDEX IF NOT EXISTS "organisatio_status_d2bac9_idx" ON "organisations_organisation" ("status");',
            reverse_sql='DROP INDEX IF EXISTS "organisatio_status_d2bac9_idx";',
        ),
    ]
