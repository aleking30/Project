from django.contrib.auth.models import User
from django.db import models

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Campo para almacenar el usuario
    message = models.CharField(max_length=255)  # Campo para almacenar el mensaje del usuario
    response = models.CharField(max_length=255)  # Campo para almacenar la respuesta del asistente
    timestamp = models.DateTimeField(auto_now_add=True)  # Campo para almacenar la fecha y hora del chat

    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"

class Hijo(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_de_nacimiento = models.DateField()
    genero = models.CharField(max_length=10)
    grado_academico = models.CharField(max_length=100)
    enfermedad_diagnosticada = models.CharField(max_length=100)
    materia_favorita = models.CharField(max_length=100)  # Actualización del campo
    respuesta_api = models.TextField(blank=True, null=True)
    conversacion_personalizada = models.TextField(default="[]")  # Campo para almacenar la respuesta de la API

    def __str__(self):
        return self.nombre

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=30)
    apellido = models.CharField(max_length=30)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=30)
    email = models.EmailField(null=True, default="")
    chat_history = models.ManyToManyField(Chat)
    hijos = models.ManyToManyField(Hijo)

    def __str__(self):
        return self.user.username


