from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('find_mosque', '0001_initial'),
        ('subscribe', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='duration_days',
            field=models.PositiveSmallIntegerField(default=30),
        ),
        migrations.AddField(
            model_name='subscription',
            name='notification_method',
            field=models.CharField(choices=[('whatsapp', 'WhatsApp'), ('email', 'Email')], default='whatsapp', max_length=20),
        ),
        migrations.AddField(
            model_name='subscription',
            name='notification_minutes_before',
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.AddField(
            model_name='subscription',
            name='selected_mosques',
            field=models.ManyToManyField(blank=True, related_name='subscriptions', to='find_mosque.mosque'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='selected_prayers',
            field=models.JSONField(default=list),
        ),
    ]
