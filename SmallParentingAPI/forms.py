from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class RegistroForm(UserCreationForm):
    nombre = forms.CharField(max_length=30)
    apellido = forms.CharField(max_length=30)
    fecha_nacimiento = forms.DateField()
    genero = forms.ChoiceField(choices=(('M', 'Masculino'), ('F', 'Femenino'), ('N', 'Prefiero no decirlo')))
    email = forms.EmailField()

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("El nombre de usuario ya existe. Por favor, elige otro.")
        return username

    class Meta:
        model = User
        fields = ['nombre', 'apellido', 'fecha_nacimiento', 'genero', 'email', 'username', 'password1', 'password2']
