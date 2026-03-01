from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('find_mosque', '0003_mosque_additional_info_mosque_contact_person'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FavoriteMosque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mosque', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorited_by', to='find_mosque.mosque')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_mosques', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Favorite Mosque',
                'verbose_name_plural': 'Favorite Mosques',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'mosque')},
            },
        ),
    ]
