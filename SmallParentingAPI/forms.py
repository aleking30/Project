from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from django.contrib.auth.models import User

class RegistroForm(UserCreationForm):
    nombre = forms.CharField(max_length=30)
    apellido = forms.CharField(max_length=30)
    fecha_nacimiento = forms.DateField()
    genero = forms.ChoiceField(choices=(('SELECCIONAR', 'Seleccionar'), ('FEMENINO', 'Femenino'), ('MASCULINO', 'Masculino'), ('PREFIERO NO DECIRLO', 'Prefiero no decirlo')))
    email = forms.EmailField()

    def clean_genero(self):
        genero = self.cleaned_data['genero']
        if genero == 'SELECCIONAR':
            raise forms.ValidationError("Por favor, selecciona una opción válida para el género.")
        return genero

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("El nombre de usuario ya existe. Por favor, elige otro.")
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        nombre = self.cleaned_data.get("nombre").lower()  # Convertimos el nombre a minúsculas

        if password1 and nombre in password1:
            raise forms.ValidationError("La contraseña no puede contener tu nombre.")
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2:
            try:
                password_validation.validate_password(password2, self.instance)
            except forms.ValidationError as error:
                self.add_error('password2', error)

            if len(password2) < 8:
                raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")

            if not any(char.isdigit() for char in password2):
                raise forms.ValidationError("La contraseña debe contener al menos un número.")

            if not any(char.isupper() for char in password2):
                raise forms.ValidationError("La contraseña debe contener al menos una letra mayúscula.")

            nombre = self.cleaned_data.get("nombre").lower()  # Convertimos el nombre a minúsculas
            if nombre in password2:
                raise forms.ValidationError("La contraseña no puede contener tu nombre.")

        return password2

    class Meta:
        model = User
        fields = ['nombre', 'apellido', 'fecha_nacimiento', 'genero', 'email', 'username', 'password1', 'password2']