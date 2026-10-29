from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_detector', '0006_alter_aidetectionscan_explanation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='aidetectionscan',
            name='chunks_analysed',
            field=models.IntegerField(default=1, help_text='Number of chunks successfully analysed'),
        ),
        migrations.AddField(
            model_name='aidetectionscan',
            name='chunks_total',
            field=models.IntegerField(default=1, help_text='Total chunks document was split into'),
        ),
        migrations.AddField(
            model_name='aidetectionscan',
            name='ai_sentence_count',
            field=models.IntegerField(default=0, help_text='Number of sentences flagged as AI'),
        ),
        migrations.AddField(
            model_name='aidetectionscan',
            name='total_sentence_count',
            field=models.IntegerField(default=0, help_text='Total sentences analysed'),
        ),
    ]
