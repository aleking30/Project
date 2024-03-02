from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PerfilUsuario, Hijo
from .forms import RegistroForm
import openai, json

llave = ""
openai.api_key = llave

def ask_openai(conversa):
    print(conversa) #supervision de contexto de la aplicacion
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=conversa,
        temperature = 0.9
    )
    answer = response.choices[0].message.content.strip()
    return answer

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()

            perfil = PerfilUsuario(
                user=user,
                nombre=form.cleaned_data['nombre'],
                apellido=form.cleaned_data['apellido'],
                fecha_nacimiento=form.cleaned_data['fecha_nacimiento'],
                genero=form.cleaned_data['genero'],
                email=form.cleaned_data['email'],
            )
            perfil.save()

            # Autenticar y realizar el inicio de sesión
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(request, username=username, password=password)
            login(request, user)

            request.session['registro_exitoso'] = True

            return redirect('inicio')  # Reemplaza 'nombre_de_la_vista_de_inicio' con el nombre de la vista de inicio en tus urls.py

    else:
        # Si la solicitud es GET, verifica si hay un usuario existente y usa sus datos para inicializar el formulario
        user = request.user if request.user.is_authenticated else None
        initial_data = {
            'nombre': user.nombre if user else '',  # Aquí debes ajustar el nombre del campo en User que almacena el nombre
            'apellido': user.apellido if user else '',
            'username': user.username if user else '',
            'genero': user.genero if user else '',
            'fecha_nacimiento': user.fecha_nacimiento if user else '',
            'email': user.email if user else ''  # Ajusta el nombre del campo en User que almacena el apellido
        }
        form = RegistroForm(initial=initial_data)

    campos_con_errores = form.errors.keys() if form.errors else None
    return render(request, 'registro.html', {'form': form, 'campos_con_errores': campos_con_errores})

def inicio(request):
    login_exitoso = request.session.pop('login_exitoso', False)

    registro_exitoso = request.session.pop('registro_exitoso', False)
    # Verificar si el usuario ha iniciado sesión
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session['login_exitoso'] = True
            messages.success(request, "Inicio de sesión exitoso.")
            return redirect('/inicio/?username={}'.format(username))
        else:
            error_message = 'Credenciales inválidas. Por favor, intenta nuevamente.'
            return render(request, 'Pantalla_de_inicio.html', {'error_message': error_message})
    
    if request.user.is_authenticated:
        perfil_usuario = PerfilUsuario.objects.get(user=request.user)
        hijos = perfil_usuario.hijos.all()
    else:
        hijos = []

    return render(request, 'Pantalla_de_inicio.html', {'hijos': hijos, 'registro_exitoso': registro_exitoso, 'login_exitoso':login_exitoso})

@login_required
def EliminarHijo(request):
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)
    
    if request.method == 'POST':
        # Obtén el ID del hijo a eliminar desde la solicitud POST
        hijo_id = request.POST.get('hijo_id')
        
        try:
            hijo = Hijo.objects.get(id=hijo_id)
            
            # Verifica si el hijo pertenece al perfil del usuario actual
            if hijo in perfil_usuario.hijos.all():
                hijo.delete()  # Elimina el hijo
                return redirect('inicio')
            else:
                raise Http404("No tienes permisos para eliminar este hijo.")
        except Hijo.DoesNotExist:
            # Manejar el caso en el que el hijo no existe
            raise Http404("El hijo que intentas eliminar no existe.")
    
    # Renderiza la vista con la lista de hijos para seleccionar uno para eliminar
    hijos = perfil_usuario.hijos.all()  # Solo los hijos del usuario actual
    return render(request, 'Eliminarhijo.html', {'hijos': hijos})

def cerrar_sesion(request):
    logout(request)
    return redirect('/inicio/')

def agregar_hijo(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombrehijo')
        fecha_de_nacimiento = request.POST.get('F_N')
        genero = request.POST.get('genero_sexo')
        grado_academico = request.POST.get('Grado_Academico')
        enfermedad_diagnosticada = request.POST.get('enfermedad')
        materia_favorita = request.POST.get('materia_favorita', '')  # Valor por defecto en caso de que no se proporcione

        perfil_usuario = PerfilUsuario.objects.get(user=request.user)

        hijo = Hijo(
            nombre=nombre,
            fecha_de_nacimiento=fecha_de_nacimiento,
            genero=genero,
            grado_academico=grado_academico,
            enfermedad_diagnosticada=enfermedad_diagnosticada,
            materia_favorita=materia_favorita,
        )
        hijo.save()

        perfil_usuario.hijos.add(hijo)
        perfil_usuario.save()

        return redirect('inicio')

    return render(request, 'agregar_hijo.html')

@login_required(login_url='/inicio/')
def chat_DIFICULTADES_DE_APRENDIZAJE(request):
    # Obtener el perfil del usuario actual
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)

    # Obtener la lista de hijos asociados al usuario actual
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)

    if request.method == 'POST':
        perfil_hijo_seleccionado = request.POST.get('perfil_hijo', '')
        conversa = []

        # Agregar los datos del perfil del hijo seleccionado al mensaje
        if perfil_hijo_seleccionado:
            perfil_hijo = Hijo.objects.get(id=perfil_hijo_seleccionado)
            mensaje_perfil_hijo = f"Perfil del hijo seleccionado:  " \
                                  f"Nombre: {perfil_hijo.nombre}, " \
                                  f"Fecha de nacimiento: {perfil_hijo.fecha_de_nacimiento}, " \
                                  f"Género: {perfil_hijo.genero}, " \
                                  f"Grado académico: {perfil_hijo.grado_academico}, " \
                                  f"Enfermedad diagnosticada: {perfil_hijo.enfermedad_diagnosticada}, " \
                                  f"Materia favorita: {perfil_hijo.materia_favorita}, "
            conversa.append({"role": "system", "content": mensaje_perfil_hijo})

        # Obtener los valores de los campos del formulario
        pregunta1 = request.POST.get('p1', '')
        pregunta2 = request.POST.get('p2', '')
        pregunta3 = request.POST.get('p3', '')
        pregunta4 = request.POST.get('p4', '')
        pregunta5 = request.POST.get('p5', '')
        
        #Crear el mensaje con los valores obtenidos
        conversa.append({"role": "system", "content": "Necesito que actues como un experto en dificultades de aprendizaje, necesito que brindes la solucion mas completa posible a cada problema que se presente y no solicites mas informacion de la que ya te facilitan."})
        mensaje_formulario = f"Hola soy {request.user}, " \
                             f"Área que presenta mayor dificultad de aprendizaje: {pregunta1}, " \
                             f"Dificultades sociales o emocionales: {pregunta2}, " \
                             f"Síntomas: {pregunta3}, " \
                             f"Qué tipo de apoyo sería beneficio para tu hijo: {pregunta4}, " \
                             f"Estrategias realizadas: {pregunta5}"
        conversa.append({"role": "user", "content": mensaje_formulario})
        
        # Enviar el mensaje a chatbot y obtener la respuesta
        response = ask_openai(conversa)
        print(response)

        # Guardar la respuesta en el perfil del hijo seleccionado
        if perfil_hijo_seleccionado:
            hijo_seleccionado = Hijo.objects.get(id=perfil_hijo_seleccionado)
            hijo_seleccionado.respuesta_api = response
            hijo_seleccionado.save()

        # Redirigir a otra vista después de enviar el formulario
        return render(request, 'respuestaAPI.html', {'response': response, 'hijos': hijos, 'perfil_hijo_seleccionado': perfil_hijo_seleccionado})

    return render(request, 'dificultadesAprendizaje.html', {'hijos': hijos})

@login_required(login_url='/inicio/')
def chat_PRESION_ACADEMICA(request):
    # Obtener el perfil del usuario actual
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)

    # Obtener la lista de hijos asociados al usuario actual
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)

    if request.method == 'POST':
        perfil_hijo_seleccionado = request.POST.get('perfil_hijo', '')
        conversa = []

        # Agregar los datos del perfil del hijo seleccionado al mensaje
        if perfil_hijo_seleccionado:
            perfil_hijo = Hijo.objects.get(id=perfil_hijo_seleccionado)
            mensaje_perfil_hijo = f"Perfil del hijo seleccionado:  " \
                                  f"Nombre: {perfil_hijo.nombre}, " \
                                  f"Fecha de nacimiento: {perfil_hijo.fecha_de_nacimiento}, " \
                                  f"Género: {perfil_hijo.genero}, " \
                                  f"Grado académico: {perfil_hijo.grado_academico}, " \
                                  f"Enfermedad diagnosticada: {perfil_hijo.enfermedad_diagnosticada}, " \
                                  f"Materia favorita: {perfil_hijo.materia_favorita}, "
            conversa.append({"role": "system", "content": mensaje_perfil_hijo})

        # Obtener los valores de los campos del formulario
        pregunta1 = request.POST.get('p1', '')
        pregunta2 = request.POST.get('p2', '')
        pregunta3 = request.POST.get('p3', '')
        pregunta4 = request.POST.get('p4', '')
        pregunta5 = request.POST.get('p5', '')
        
        #Crear el mensaje con los valores obtenidos
        conversa.append({"role": "system", "content": "Necesito que actues como un experto en PRESION ACADEMICA, necesito que le brindes una solucion completa para que pueda solucionar sus problemas de presion academica."})
        mensaje = f"Hola soy {request.user}, " \
                  f"Area o areas que presenta mayor Presion Academica: {pregunta1}, " \
                  f"Que estrategia de afrontamiento a utilizado tu hijo: {pregunta2}, " \
                  f"Cuales son tus mayores desafios para abordar el problema: {pregunta3}, " \
                  f"Como la presion academica esta afectando el bienestar de tu hijo: {pregunta4}, " \
                  f"Estrategias realizadas: {pregunta5}"
        conversa.append({"role": "user", "content": mensaje})
        # Enviar el mensaje a chatbot y obtener la respuesta
        response = ask_openai(conversa)
        print(response)

        # Guardar la respuesta en el perfil del hijo seleccionado
        if perfil_hijo_seleccionado:
            hijo_seleccionado = Hijo.objects.get(id=perfil_hijo_seleccionado)
            hijo_seleccionado.respuesta_api = response
            hijo_seleccionado.save()

        # Redirigir a otra vista después de enviar el formulario
        return render(request, 'respuestaAPI.html', {'response': response, 'hijos': hijos, 'perfil_hijo_seleccionado': perfil_hijo_seleccionado})
    return render(request, 'PresionAcademica.html', {'hijos': hijos})

@login_required(login_url='/inicio/')
def chat_SALUD_MENTAL_ESTUDIANTIL(request):
    # Obtener el perfil del usuario actual
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)

    # Obtener la lista de hijos asociados al usuario actual
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)

    if request.method == 'POST':
        perfil_hijo_seleccionado = request.POST.get('perfil_hijo', '')
        conversa = []

        # Agregar los datos del perfil del hijo seleccionado al mensaje
        if perfil_hijo_seleccionado:
            perfil_hijo = Hijo.objects.get(id=perfil_hijo_seleccionado)
            mensaje_perfil_hijo = f"Perfil del hijo seleccionado:  " \
                                  f"Nombre: {perfil_hijo.nombre}, " \
                                  f"Fecha de nacimiento: {perfil_hijo.fecha_de_nacimiento}, " \
                                  f"Género: {perfil_hijo.genero}, " \
                                  f"Grado académico: {perfil_hijo.grado_academico}, " \
                                  f"Enfermedad diagnosticada: {perfil_hijo.enfermedad_diagnosticada}, " \
                                  f"Materia favorita: {perfil_hijo.materia_favorita}, "
            conversa.append({"role": "system", "content": mensaje_perfil_hijo})
        
        # Obtener los valores de los campos del formulario
        pregunta1 = request.POST.get('p1', '')
        pregunta2 = request.POST.get('p2', '')
        pregunta3 = request.POST.get('p3', '')
        pregunta4 = request.POST.get('p4', '')
        pregunta5 = request.POST.get('p5', '')
        
        #Crear el mensaje con los valores obtenidos
        conversa.append({"role": "system", "content": "Eres un experto en SALUD MENTAL ESTUDIANTIL, por lo tanto, por toda la informacion que recopiles en base al formulario y a los datos del usuario, brindaras una respuesta completo y precisa para poder ayudar al usuario con su problema. "})
        mensaje = f"Hola soy {request.user}, " \
                  f": La persona tiene alguna enfermedad de salud mental detectada: {pregunta1}, " \
                  f": Dificultades sociales o emocionales ha experimentado en relacion con sun rendimiento academico: {pregunta2}, " \
                  f": Cual de los siguientes sintomas describe mejor el comportamiento de la persona: {pregunta3}, " \
                  f": Que apoyo educativo puede ser el mas beneficioso: {pregunta4}, " \
                  f": Estrategias de apoyo utilizadas: {pregunta5}"
        conversa.append({"role": "user", "content": mensaje})

        # Enviar el mensaje a chatbot y obtener la respuesta
        response = ask_openai(conversa)
        print(response)

        # Guardar la respuesta en el perfil del hijo seleccionado
        if perfil_hijo_seleccionado:
            hijo_seleccionado = Hijo.objects.get(id=perfil_hijo_seleccionado)
            hijo_seleccionado.respuesta_api = response
            hijo_seleccionado.save()

        # Redirigir a otra vista después de enviar el formulario
        return render(request, 'respuestaAPI.html', {'response': response, 'hijos': hijos, 'perfil_hijo_seleccionado': perfil_hijo_seleccionado})
    return render(request, 'SaludMentalEstudiantil.html', {'hijos': hijos})

@login_required(login_url='/inicio/')
def chat_PROBLEMAS_DE_CONDUCTA(request):
    return render(request, 'ProblemasConducta.html')

def Bullying(request):
    # Obtener el perfil del usuario actual
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)

    # Obtener la lista de hijos asociados al usuario actual
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)

    if request.method == 'POST':
        perfil_hijo_seleccionado = request.POST.get('perfil_hijo', '')
        conversa = []

        # Agregar los datos del perfil del hijo seleccionado al mensaje
        if perfil_hijo_seleccionado:
            perfil_hijo = Hijo.objects.get(id=perfil_hijo_seleccionado)
            mensaje_perfil_hijo = f"Perfil del hijo seleccionado:  " \
                                  f"Nombre: {perfil_hijo.nombre}, " \
                                  f"Fecha de nacimiento: {perfil_hijo.fecha_de_nacimiento}, " \
                                  f"Género: {perfil_hijo.genero}, " \
                                  f"Grado académico: {perfil_hijo.grado_academico}, " \
                                  f"Enfermedad diagnosticada: {perfil_hijo.enfermedad_diagnosticada}, " \
                                  f"Materia favorita: {perfil_hijo.materia_favorita}, "
            conversa.append({"role": "system", "content": mensaje_perfil_hijo})

        # Obtener los valores de los campos del formulario
        pregunta1 = request.POST.get('p1', '')
        pregunta2 = request.POST.get('p2', '')
        pregunta3 = request.POST.get('p3', '')
        pregunta4 = request.POST.get('p4', '')
        pregunta5 = request.POST.get('p5', '')
        pregunta6 = request.POST.get('p6', '')
        pregunta7 = request.POST.get('p7', '')
        pregunta8 = request.POST.get('p8', '')
        pregunta9 = request.POST.get('p9', '')
        pregunta10 = request.POST.get('p10', '')
        pregunta11 = request.POST.get('p11', '')
        
        #Crear el mensaje con los valores obtenidos
        conversa.append({"role": "system", "content": "Eres un experto en dar soluciones a los problemas de Bullying estudiantil, por lo tanto en base a las respuesta que recibas del usuario, brindaras soluciones a su problema. "})
        mensaje = f"Hola soy {request.user}, " \
                  f": Victima o Causante: {pregunta1}," \
                  f": Desprecipcion o detalles: {pregunta2}{pregunta7}," \
                  f": Detalles del incidente o circunstancias en las que ocurre: {pregunta3}{pregunta8}, " \
                  f": lugar y momento o cambios en la actitud o comportamiento: {pregunta4}{pregunta9}, " \
                  f": Agresores y testigos o comunicacion y empatía: {pregunta5}{pregunta10}, " \
                  f": Reacciones y consecuencias del comportamiento: {pregunta6}{pregunta11}, "
        conversa.append({"role": "user", "content": mensaje})
        # Enviar el mensaje a chatbot y obtener la respuesta

        response = ask_openai(conversa)
        print(response)

        # Guardar la respuesta en el perfil del hijo seleccionado
        if perfil_hijo_seleccionado:
            hijo_seleccionado = Hijo.objects.get(id=perfil_hijo_seleccionado)
            hijo_seleccionado.respuesta_api = response
            hijo_seleccionado.save()

        # Redirigir a otra vista después de enviar el formulario
        return render(request, 'respuestaAPI.html', {'response': response, 'hijos': hijos, 'perfil_hijo_seleccionado': perfil_hijo_seleccionado})
    return render(request, 'Bullying.html', {'hijos': hijos})

def C_Disruptiva(request):
    # Obtener el perfil del usuario actual
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)

    # Obtener la lista de hijos asociados al usuario actual
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)

    if request.method == 'POST':
        perfil_hijo_seleccionado = request.POST.get('perfil_hijo', '')
        conversa = []

        # Agregar los datos del perfil del hijo seleccionado al mensaje
        if perfil_hijo_seleccionado:
            perfil_hijo = Hijo.objects.get(id=perfil_hijo_seleccionado)
            mensaje_perfil_hijo = f"Perfil del hijo seleccionado:  " \
                                  f"Nombre: {perfil_hijo.nombre}, " \
                                  f"Fecha de nacimiento: {perfil_hijo.fecha_de_nacimiento}, " \
                                  f"Género: {perfil_hijo.genero}, " \
                                  f"Grado académico: {perfil_hijo.grado_academico}, " \
                                  f"Enfermedad diagnosticada: {perfil_hijo.enfermedad_diagnosticada}, " \
                                  f"Materia favorita: {perfil_hijo.materia_favorita}, "
            conversa.append({"role": "system", "content": mensaje_perfil_hijo})

        # Obtener los valores de los campos del formulario
        pregunta1 = request.POST.get('p1', '')
        pregunta2 = request.POST.get('p2', '')
        pregunta3 = request.POST.get('p3', '')
        pregunta4 = request.POST.get('p4', '')
        pregunta5 = request.POST.get('p5', '')
        
        #Crear el mensaje con los valores obtenidos
        conversa.append({"role": "system", "content": "Eres un experto en los problemas de conducta estudiantiles principalmente en la conducta disruptiva, por lo tanto en base a las respuesta que recibas del usuario, brindaras una solucion completa a su problema. "})
        mensaje = f"Hola soy {request.user}, " \
                  f": Cuales son los comportamientos especificos que tu hijo/hija a demostrado: {pregunta1}," \
                  f": En que contextos o situaciones suele mostrar estos comportamientos: {pregunta2}," \
                  f": Patron o desencadenante particular: {pregunta3}, " \
                  f": Como haz intentado abordar o manejar estos comportamientos: {pregunta4}, " \
                  f": Haz buscado alguna estrategia especifica: {pregunta5}" 
        conversa.append({"role": "user", "content": mensaje})
        # Enviar el mensaje a chatbot y obtener la respuesta
        response = ask_openai(conversa)
        print(response)

        # Guardar la respuesta en el perfil del hijo seleccionado
        if perfil_hijo_seleccionado:
            hijo_seleccionado = Hijo.objects.get(id=perfil_hijo_seleccionado)
            hijo_seleccionado.respuesta_api = response
            hijo_seleccionado.save()

        # Redirigir a otra vista después de enviar el formulario
        return render(request, 'respuestaAPI.html', {'response': response, 'hijos': hijos, 'perfil_hijo_seleccionado': perfil_hijo_seleccionado})
    return render(request, 'C_Disruptiva.html', {'hijos': hijos})

def D_Autoridad(request):
    # Obtener el perfil del usuario actual
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)

    # Obtener la lista de hijos asociados al usuario actual
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)

    if request.method == 'POST':
        perfil_hijo_seleccionado = request.POST.get('perfil_hijo', '')
        conversa = []

        # Agregar los datos del perfil del hijo seleccionado al mensaje
        if perfil_hijo_seleccionado:
            perfil_hijo = Hijo.objects.get(id=perfil_hijo_seleccionado)
            mensaje_perfil_hijo = f"Perfil del hijo seleccionado:  " \
                                  f"Nombre: {perfil_hijo.nombre}, " \
                                  f"Fecha de nacimiento: {perfil_hijo.fecha_de_nacimiento}, " \
                                  f"Género: {perfil_hijo.genero}, " \
                                  f"Grado académico: {perfil_hijo.grado_academico}, " \
                                  f"Enfermedad diagnosticada: {perfil_hijo.enfermedad_diagnosticada}, " \
                                  f"Materia favorita: {perfil_hijo.materia_favorita}, "
            conversa.append({"role": "system", "content": mensaje_perfil_hijo})

        # Obtener los valores de los campos del formulario
        pregunta1 = request.POST.get('p1', '')
        pregunta2 = request.POST.get('p2', '')
        pregunta3 = request.POST.get('p3', '')
        pregunta4 = request.POST.get('p4', '')
        pregunta5 = request.POST.get('p5', '')
        
        #Crear el mensaje con los valores obtenidos
        conversa.append({"role": "system", "content": "Eres un experto en los problemas de conducta estudiantiles principalmente en el desafio de la autoridad, por lo tanto en base a las respuesta que recibas del usuario, brindaras una solucion completa a su problema. "})
        mensaje = f"Hola soy {request.user}, " \
                  f": Con que frecuenca desafia a la autoridad: {pregunta1}," \
                  f": Cuales son los comportamientos que la persona demuestra: {pregunta2}," \
                  f": Patron o situacion especifica: {pregunta3}, " \
                  f": Como sueles comunicarte con tu hijo cuando se enfrenta a estas situaciones: {pregunta4}, " \
                  f": Haz buscado alguna estrategia especifica: {pregunta5}" 
        conversa.append({"role": "user", "content": mensaje})
        # Enviar el mensaje a chatbot y obtener la respuesta
        response = ask_openai(conversa)
        print(response)

        # Guardar la respuesta en el perfil del hijo seleccionado
        if perfil_hijo_seleccionado:
            hijo_seleccionado = Hijo.objects.get(id=perfil_hijo_seleccionado)
            hijo_seleccionado.respuesta_api = response
            hijo_seleccionado.save()

        # Redirigir a otra vista después de enviar el formulario
        return render(request, 'respuestaAPI.html', {'response': response, 'hijos': hijos, 'perfil_hijo_seleccionado': perfil_hijo_seleccionado})
    return render(request, 'D_Autoridad.html', {'hijos': hijos})

@login_required(login_url='/inicio/')
def chat_GESTION_DEL_TIEMPO(request):
    # Obtener el perfil del usuario actual
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)

    # Obtener la lista de hijos asociados al usuario actual
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)

    if request.method == 'POST':
        perfil_hijo_seleccionado = request.POST.get('perfil_hijo', '')
        conversa = []

        # Agregar los datos del perfil del hijo seleccionado al mensaje
        if perfil_hijo_seleccionado:
            perfil_hijo = Hijo.objects.get(id=perfil_hijo_seleccionado)
            mensaje_perfil_hijo = f"Perfil del hijo seleccionado:  " \
                                  f"Nombre: {perfil_hijo.nombre}, " \
                                  f"Fecha de nacimiento: {perfil_hijo.fecha_de_nacimiento}, " \
                                  f"Género: {perfil_hijo.genero}, " \
                                  f"Grado académico: {perfil_hijo.grado_academico}, " \
                                  f"Enfermedad diagnosticada: {perfil_hijo.enfermedad_diagnosticada}, " \
                                  f"Materia favorita: {perfil_hijo.materia_favorita}, "
            conversa.append({"role": "system", "content": mensaje_perfil_hijo})

        # Obtener los valores de los campos del formulario
        pregunta1 = request.POST.get('p1', '')
        pregunta2 = request.POST.get('p2', '')
        pregunta3 = request.POST.get('p3', '')
        pregunta4 = request.POST.get('p4', '')
        pregunta5 = request.POST.get('p5', '')
        pregunta6 = request.POST.get('p6', '')
        pregunta7 = request.POST.get('p7', '')
        pregunta8 = request.POST.get('p8', '')
        pregunta9 = request.POST.get('p9', '')
        pregunta10 = request.POST.get('p10', '')
        pregunta11 = request.POST.get('p11', '')
        #Crear el mensaje con los valores obtenidos
        conversa.append({"role": "system", "content": "Necesito que actues como un profesional en Gestion del tiempo, necesito que le brindes horarios para que pueda compartir con su hijo, y le brindes diferentes soluciones en relacion a la gestion del tiempo."})
        mensaje = f"Hola soy {request.user}, " \
                  f"Dias de la semana trabajados (padre): {pregunta1}, horario de entrada: {pregunta2}, horario de salida {pregunta3}, " \
                  f"Dias de la semana estudiados (hijo):  {pregunta4}, horario de entrada: {pregunta5}, horario de salida {pregunta6}, " \
                  f"Organizacion del tiempo: {pregunta7}, " \
                  f"Principales desafios: {pregunta8}, " \
                  f"Estrategia o metodo intentado: {pregunta9}, " \
                  f"Atividades prioritarias padre e hijo: {pregunta10}, " \
                  f"Que cambios estarias dispuesto a hacer: {pregunta11}"
        conversa.append({"role": "user", "content": mensaje})
        # Enviar el mensaje a chatbot y obtener la respuesta
        response = ask_openai(conversa)
        print(response)

        # Guardar la respuesta en el perfil del hijo seleccionado
        if perfil_hijo_seleccionado:
            hijo_seleccionado = Hijo.objects.get(id=perfil_hijo_seleccionado)
            hijo_seleccionado.respuesta_api = response
            hijo_seleccionado.save()

        # Redirigir a otra vista después de enviar el formulario
        return render(request, 'respuestaAPI.html', {'response': response, 'hijos': hijos, 'perfil_hijo_seleccionado': perfil_hijo_seleccionado})
    return render(request, 'GestiondelTiempo.html', {'hijos': hijos})

@login_required(login_url='/inicio/')
def chat_CONVERSACION_PERSONALIZADA(request):
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)
    perfil_hijo_seleccionado = None
    conversa = []  # Inicializa la variable conversa aquí
    nombre_hijo_seleccionado = None  # Inicializa la variable nombre_hijo_seleccionado aquí

    if request.method == 'POST':
        perfil_hijo_id = request.POST.get('perfil_hijo', '')

        if perfil_hijo_id:
            perfil_hijo_seleccionado = Hijo.objects.get(id=perfil_hijo_id)
            conversa = json.loads(perfil_hijo_seleccionado.conversacion_personalizada)
            nombre_hijo_seleccionado = perfil_hijo_seleccionado.nombre
        else:
            conversa = []

        message = request.POST.get('message')

        if message:
            conversa.append({"role": "user", "content": message})

        response = ask_openai(conversa)
        conversa.append({"role": "assistant", "content": response})

        # Guardar la conversación en el modelo Hijo
        if perfil_hijo_seleccionado:
            perfil_hijo_seleccionado.conversacion_personalizada = json.dumps(conversa)
            perfil_hijo_seleccionado.save()

    return render(request, 'ConversacionPersonalizada.html', {'hijos': hijos, 'perfil_hijo_seleccionado': perfil_hijo_seleccionado, 'nombre_hijo_seleccionado': nombre_hijo_seleccionado, 'session': conversa})

@login_required(login_url='/inicio/')
def chat_FALTA_DE_COMUNICACION(request):
    # Obtener el perfil del usuario actual
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)

    # Obtener la lista de hijos asociados al usuario actual
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)

    if request.method == 'POST':
        perfil_hijo_seleccionado = request.POST.get('perfil_hijo', '')
        conversa = []

        # Agregar los datos del perfil del hijo seleccionado al mensaje
        if perfil_hijo_seleccionado:
            perfil_hijo = Hijo.objects.get(id=perfil_hijo_seleccionado)
            mensaje_perfil_hijo = f"Perfil del hijo seleccionado:  " \
                                  f"Nombre: {perfil_hijo.nombre}, " \
                                  f"Fecha de nacimiento: {perfil_hijo.fecha_de_nacimiento}, " \
                                  f"Género: {perfil_hijo.genero}, " \
                                  f"Grado académico: {perfil_hijo.grado_academico}, " \
                                  f"Enfermedad diagnosticada: {perfil_hijo.enfermedad_diagnosticada}, " \
                                  f"Materia favorita: {perfil_hijo.materia_favorita}, "
            conversa.append({"role": "system", "content": mensaje_perfil_hijo})

        # Obtener los valores de los campos del formulario
        pregunta1 = request.POST.get('p1', '')
        pregunta2 = request.POST.get('p2', '')
        pregunta3 = request.POST.get('p3', '')
        pregunta4 = request.POST.get('p4', '')
        pregunta5 = request.POST.get('p5', '')
        pregunta6 = request.POST.get('p6', '')

        #Crear el mensaje con los valores obtenidos
        conversa.append({"role": "system", "content": "Eres un experto en la falta de comunicacion estudiantil, por lo tanto en base a las respuesta que recibas del usuario, brindaras una solucion completa a su problema de falta de comunicacion. "})
        mensaje = f"Hola soy {request.user}, " \
                  f": Sientes que hay dificultades para establecer una comunicación efectiva con tu hijo sobre sus problemas educativos: {pregunta1}," \
                  f": Has intentado alguna estrategia o recurso para mejorar la comunicación con tu hijo acerca de sus problemas educativos: {pregunta2}," \
                  f": Consideras que el entorno familiar influye en la comunicación con tu hijo sobre sus problemas educativos: {pregunta3}, " \
                  f": Tu hijo muestra resistencia o evita hablar sobre sus problemas educativos: {pregunta4}, " \
                  f": Has intentado establecer momentos específicos para conversar con tu hijo sobre sus problemas educativos: {pregunta5}, " \
                  f": Cuentanos las experiencias que hayas tenido (opcional): {pregunta6}"
        conversa.append({"role": "user", "content": mensaje})
        # Enviar el mensaje a chatbot y obtener la respuesta
        response = ask_openai(conversa)
        print(response)

        # Guardar la respuesta en el perfil del hijo seleccionado
        if perfil_hijo_seleccionado:
            hijo_seleccionado = Hijo.objects.get(id=perfil_hijo_seleccionado)
            hijo_seleccionado.respuesta_api = response
            hijo_seleccionado.save()

        # Redirigir a otra vista después de enviar el formulario
        return render(request, 'respuestaAPI.html', {'response': response, 'hijos': hijos, 'perfil_hijo_seleccionado': perfil_hijo_seleccionado})
    return render(request, 'FaltaComunicacion.html', {'hijos': hijos})

def historial_respuestas(request):
    perfil_usuario = PerfilUsuario.objects.get(user=request.user)
    hijos = Hijo.objects.filter(perfilusuario=perfil_usuario)
    return render(request, 'historial_respuestas.html', {'hijos': hijos})

@login_required(login_url='/inicio/')
def ver_historial_perfil(request, perfil_hijo_id):
    perfil_hijo = Hijo.objects.get(id=perfil_hijo_id)
    # Obtener el historial del perfil de hijo seleccionado desde el campo respuesta_api
    historial = perfil_hijo.respuesta_api
    return render(request, 'ver_historial_perfil.html', {'perfil_hijo': perfil_hijo, 'historial': historial})