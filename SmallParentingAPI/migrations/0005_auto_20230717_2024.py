# Generated by Django 2.2.3 on 2023-07-18 00:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SmallParentingAPI', '0004_auto_20230717_1848'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hijo',
            name='enfermedad_diagnosticada',
            field=models.CharField(max_length=100),
        ),
    ]