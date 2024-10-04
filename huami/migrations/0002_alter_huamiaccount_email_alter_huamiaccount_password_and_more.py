# Generated by Django 4.2.7 on 2024-09-25 04:34

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('huami', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='huamiaccount',
            name='email',
            field=models.EmailField(db_column='email', db_comment='huami account email address', help_text='화웨이(Zepp Life) 계정 이메일', max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='huamiaccount',
            name='password',
            field=models.CharField(db_column='password', db_comment='huami account password address', help_text='화웨이(Zepp Life) 계정 패스워드', max_length=100),
        ),
        migrations.AlterField(
            model_name='huamiaccount',
            name='sync_date',
            field=models.DateTimeField(db_column='sync_date', db_comment='huami account sync date', default=datetime.datetime(1970, 1, 1, 0, 0), help_text='화웨이(Zepp Life) 계정 동기화 날짜'),
        ),
    ]