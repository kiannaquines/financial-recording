# Generated by Django 5.1.3 on 2024-12-02 05:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_remove_client_relationship_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assistance',
            name='amount',
        ),
    ]
