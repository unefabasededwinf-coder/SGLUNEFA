from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from usuarios import views
from django.conf import settings
from django.conf.urls.static import static
from usuarios.reportes import calendario_reservas_pdf

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('inicio/', views.inicio_docente, name='inicio'),
    path('registro/', views.registro_view, name='registro'),
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="admin/password_reset.html"), name="reset_password"),
    path('restablecer_contrasena/enviado/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('restablecer_contrasena/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('restablecer_contrasena/completo/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('mis-materias/', views.GestionMateriaView.as_view(), name='gestion_materias'),
    path('reservar/', views.CrearReservaView.as_view(), name='crear_reserva'),
    path('mis-requerimientos/', views.lista_requerimientos, name='mis_requerimientos'),
    path('eliminar-materia/<int:materia_id>/', views.eliminar_materia, name='eliminar_materia'),
    path('reservar/editar/<int:reserva_id>/', views.editar_reserva, name='editar_reserva'),
    path('reporte-calendario/', calendario_reservas_pdf, name='calendario_reservas'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)