# Merge migration — resolves conflicting branches:
#   Branch 1: 0003_add_sentence_analysis (new sentence_analysis field)
#   Branch 2: 0004_rename_... (index rename fixes from server auto-generation)
# Both branches depend on 0002. This merge brings them together.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_detector', '0003_add_sentence_analysis'),
        ('ai_detector', '0004_rename_ai_detector_user_id_d7c4fe_idx_ai_detector_user_id_idx_and_more'),
    ]

    operations = [
        # No operations — this is purely a merge point
    ]
