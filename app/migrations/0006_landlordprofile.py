# Generated by Django 4.2.16 on 2024-11-24 22:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_alter_tenantapprovalrequest_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='LandlordProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('banned', 'Banned')], default='active', max_length=20)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('profile_picture', models.ImageField(blank=True, upload_to='profile_pics/')),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('registered_date', models.DateTimeField(auto_now_add=True)),
                ('emergency_contact', models.CharField(blank=True, max_length=15)),
                ('notes', models.TextField(blank=True)),
                ('landlord', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='app.landlord')),
            ],
        ),
    ]