# Generated by Django 5.1.1 on 2024-09-13 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('habits', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='habit',
            name='is_bad',
            field=models.BooleanField(default=False),
        ),
    ]
