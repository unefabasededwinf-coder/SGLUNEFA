from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from usuarios import views   # Importa correctamente la app

urlpatterns = [
    # 1. Selector de Perfil (Raíz)
    path('', views.index, name='index'),

    # 2. Rutas Administrativas
    path('admin/', admin.site.urls),

    # 3. Acceso Docente e Inicio
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('inicio/', views.inicio_docente, name='inicio'),
      

    # 4. Registro de Usuarios
    path('registro/', views.registro_view, name='registro'),

    # 5. Flujo de Recuperación de Contraseña
    path('reset_password/',
         auth_views.PasswordResetView.as_view(template_name="admin/password_reset.html"),
         name="reset_password"),
    path('restablecer_contrasena/enviado/',
         auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('restablecer_contrasena/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('restablecer_contrasena/completo/',
         auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),

    # 6. Módulos del Docente
    path('mis-materias/', views.GestionMateriaView.as_view(), name='gestion_materias'),
    path('reservar/', views.CrearReservaView.as_view(), name='crear_reserva'),
    path('mis-requerimientos/', views.lista_requerimientos, name='mis_requerimientos'),

    # 7. Eliminación de materias (AJAX)
    path('eliminar-materia/<int:materia_id>/', views.eliminar_materia, name='eliminar_materia'),
    
    path('mis-requerimientos/', views.lista_requerimientos, name='mis_requerimientos'),
    
    path('reservar/editar/<int:reserva_id>/', views.editar_reserva, name='editar_reserva'),
  
]