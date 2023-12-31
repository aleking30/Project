# Generated by Django 2.2.3 on 2023-07-17 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SmallParentingAPI', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hijo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('fecha_de_nacimiento', models.DateField()),
                ('genero', models.CharField(max_length=10)),
                ('grado_academico', models.CharField(max_length=100)),
                ('Enfermedad_diagnosticada', models.BooleanField(default=False)),
                ('Asignatura_Favorita', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='hijos',
            field=models.ManyToManyField(to='SmallParentingAPI.Hijo'),
        ),
    ]
