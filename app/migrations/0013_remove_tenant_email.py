# Generated by Django 4.2.16 on 2024-11-29 00:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_tenant_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tenant',
            name='email',
        ),
    ]
