from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import mark_safe
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
admin.site.unregister(Group)
# Importa tus modelos personalizados
from .models import Materia, Requerimiento, Reserva   # Ajusta la ruta según tu app

# ---------- Personalización de Usuarios ----------
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'acciones')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_per_page = 20

    actions = ['activar_usuarios', 'desactivar_usuarios', 'hacer_administradores', 'quitar_administradores']

    def activar_usuarios(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} usuario(s) activado(s).")
    activar_usuarios.short_description = "Activar usuarios seleccionados"

    def desactivar_usuarios(self, request, queryset):
        if request.user in queryset:
            self.message_user(request, "No puedes desactivar tu propia cuenta.", level='ERROR')
            queryset = queryset.exclude(pk=request.user.pk)
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} usuario(s) desactivado(s).")
    desactivar_usuarios.short_description = "Desactivar usuarios seleccionados"

    def hacer_administradores(self, request, queryset):
        queryset.update(is_staff=True)
        self.message_user(request, f"{queryset.count()} usuario(s) ahora son administradores.")
    hacer_administradores.short_description = "Hacer administradores (staff)"

    def quitar_administradores(self, request, queryset):
        if request.user in queryset:
            self.message_user(request, "No puedes quitarte tus propios privilegios de administrador.", level='ERROR')
            queryset = queryset.exclude(pk=request.user.pk)
        queryset.update(is_staff=False)
        self.message_user(request, f"{queryset.count()} usuario(s) ya no son administradores.")
    quitar_administradores.short_description = "Quitar administradores"

    def acciones(self, obj):
        if obj.is_active:
            activar_btn = f'<a class="button" href="toggle-active/{obj.id}/" style="background:#dc3545; color:white;">Desactivar</a>'
        else:
            activar_btn = f'<a class="button" href="toggle-active/{obj.id}/" style="background:#28a745; color:white;">Activar</a>'

        if obj.is_staff:
            admin_btn = f'<a class="button" href="toggle-admin/{obj.id}/" style="background:#dc3545; color:white;">Quitar admin</a>'
        else:
            admin_btn = f'<a class="button" href="toggle-admin/{obj.id}/" style="background:#007bff; color:white;">Hacer admin</a>'

        return mark_safe(f'{activar_btn} {admin_btn}')
    acciones.short_description = 'Acciones'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('toggle-active/<int:user_id>/', self.admin_site.admin_view(self.toggle_active), name='toggle_active'),
            path('toggle-admin/<int:user_id>/', self.admin_site.admin_view(self.toggle_admin), name='toggle_admin'),
        ]
        return custom_urls + urls

    def toggle_active(self, request, user_id):
        user = User.objects.get(pk=user_id)
        if request.user == user:
            messages.error(request, "No puedes desactivar tu propia cuenta.")
        else:
            user.is_active = not user.is_active
            user.save()
            estado = "activado" if user.is_active else "desactivado"
            messages.success(request, f"Usuario {user.get_full_name()} {estado} correctamente.")
        return redirect('admin:auth_user_changelist')

    def toggle_admin(self, request, user_id):
        user = User.objects.get(pk=user_id)
        if request.user == user:
            messages.error(request, "No puedes cambiar tu propio rol de administrador.")
        else:
            user.is_staff = not user.is_staff
            user.save()
            rol = "administrador" if user.is_staff else "docente"
            messages.success(request, f"Rol de {user.get_full_name()} actualizado a {rol}.")
        return redirect('admin:auth_user_changelist')

# Desregistrar User original y registrar el personalizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# ---------- Registrar tus modelos personalizados ----------
# Aquí va el registro de Materia, Requerimiento y Reserva
# Si ya tenías alguna configuración personalizada para ellos, agrégala ahora

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'seccion', 'nombre_docente')
    search_fields = ('nombre', 'seccion')
    list_filter = ('docente',)
    
    def nombre_docente(self, obj):
        return obj.docente.get_full_name() or obj.docente.username
    nombre_docente.short_description = 'Docente'
    nombre_docente.admin_order_field = 'docente__first_name' 

@admin.register(Requerimiento)
class RequerimientoAdmin(admin.ModelAdmin):
    list_display = ('nombre_usuario', 'tipo', 'descripcion', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'tipo')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__username', 'descripcion')
    list_editable = ('estado',)
    list_per_page = 20
    
    def nombre_usuario(self, obj):
        """Retorna el nombre completo del usuario"""
        return obj.usuario.get_full_name() or obj.usuario.username
    nombre_usuario.short_description = 'Usuario'
    nombre_usuario.admin_order_field = 'usuario__first_name'

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('materia', 'nombre_docente', 'fecha', 'hora_inicio', 'hora_fin')
    list_filter = ('fecha', 'docente')
    search_fields = ('materia__nombre', 'docente__first_name', 'docente__last_name', 'docente__username')
    list_per_page = 20
    
    def nombre_docente(self, obj):
        """Retorna el nombre completo del docente"""
        return obj.docente.get_full_name() or obj.docente.username
    nombre_docente.short_description = 'Docente'
    nombre_docente.admin_order_field = 'docente__first_name'