# Generated by Django 5.1.4 on 2025-01-21 16:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_rentalpost_max_occupants'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='user',
            new_name='user_id',
        ),
    ]
