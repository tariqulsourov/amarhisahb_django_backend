from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_userssettings_reminder_enabled_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userssettings',
            name='last_reminder_sent_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
