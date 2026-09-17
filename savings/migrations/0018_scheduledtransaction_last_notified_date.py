from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0017_scheduledtransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledtransaction',
            name='last_notified_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
