from django.contrib import admin
from django.urls import path
from SmallParentingAPI.views import inicio, registro, ModificarHijo, chat_DIFICULTADES_DE_APRENDIZAJE, chat_PRESION_ACADEMICA, cerrar_sesion, P_D_C_SOCIAL, C_Disruptiva, D_Autoridad, Bullying, agregar_hijo
from SmallParentingAPI.views import chat_SALUD_MENTAL_ESTUDIANTIL, chat_FALTA_DE_COMUNICACION, chat_PROBLEMAS_DE_CONDUCTA, chat_GESTION_DEL_TIEMPO, chat_CONVERSACION_PERSONALIZADA, historial_respuestas, ver_historial_perfil
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('registro/', registro, name='registro'),
    path('inicio/', inicio, name='inicio'),
    path('login/', inicio, name='login'),
    path('ModificarHijo/', ModificarHijo, name='ModificarHijo'),
    path('cerrar-sesion/', cerrar_sesion, name='cerrar_sesion'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    path('agregar_hijo/', agregar_hijo, name='agregar_hijo'),  
    path('dificultadesAprendizaje/', chat_DIFICULTADES_DE_APRENDIZAJE, name='dificultadesAprendizaje'),
    path('PresionAcademica/', chat_PRESION_ACADEMICA, name='PresionAcademica'),
    path('SaludMentalEstudiantil/', chat_SALUD_MENTAL_ESTUDIANTIL, name='SaludMentalEstudiantil'),
    path('FaltaComunicacion/', chat_FALTA_DE_COMUNICACION, name='FaltaComunicacion'),
    path('ProblemasConducta/', chat_PROBLEMAS_DE_CONDUCTA, name='ProblemasConducta'),
    path('bullying/', Bullying, name='Bullying'),
    path('D_Autoridad/', D_Autoridad, name='D_Autoridad'),
    path('C_Disruptiva/', C_Disruptiva, name='C_Disruptiva'),
    path('P_D_C_SOCIAL/', P_D_C_SOCIAL, name='P_D_C_SOCIAL'),
    path('GestiondelTiempo/', chat_GESTION_DEL_TIEMPO, name='GestiondelTiempo'),
    path('ConversacionPersonalizada/', chat_CONVERSACION_PERSONALIZADA, name='ConversacionPersonalizada'),
    path('historial_respuestas/', historial_respuestas, name='historial_respuestas'),
    path('historial/<int:perfil_hijo_id>/', ver_historial_perfil, name='ver_historial_perfil'),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += [path('admin/', admin.site.urls)]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)