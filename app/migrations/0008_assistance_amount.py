# Generated by Django 5.1.3 on 2024-12-03 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_remove_assistance_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='assistance',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=7000, max_digits=10, null=True),
        ),
    ]