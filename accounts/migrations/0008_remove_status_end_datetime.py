# Generated by Django 4.2.7 on 2024-07-11 05:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_status_note'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='status',
            name='end_datetime',
        ),
    ]
