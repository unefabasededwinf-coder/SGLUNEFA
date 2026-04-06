from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import mark_safe
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages

admin.site.unregister(Group)

# Importa tus modelos personalizados
from .models import Materia, Requerimiento, Reserva

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
        return obj.usuario.get_full_name() or obj.usuario.username
    nombre_usuario.short_description = 'Usuario'
    nombre_usuario.admin_order_field = 'usuario__first_name'


# ---------- RESERVAS CON BOTÓN DE REPORTE ----------
@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('materia', 'nombre_docente', 'fecha', 'hora_inicio', 'hora_fin', 'boton_reporte')
    list_filter = ('fecha', 'docente')
    search_fields = ('materia__nombre', 'docente__first_name', 'docente__last_name', 'docente__username')
    list_per_page = 20

    def nombre_docente(self, obj):
        return obj.docente.get_full_name() or obj.docente.username
    nombre_docente.short_description = 'Docente'
    nombre_docente.admin_order_field = 'docente__first_name'

    def boton_reporte(self, obj):
        from django.utils.html import format_html
        from datetime import timedelta
        fecha = obj.fecha
        lunes = fecha - timedelta(days=fecha.weekday())
        sabado = lunes + timedelta(days=5)
        url = f"/reporte-calendario/?fecha_inicio={lunes}&fecha_fin={sabado}"
        return format_html('<a class="button" href="{}" target="_blank">📅 Calendario semana</a>', url)
    boton_reporte.short_description = 'Reporte semanal'


# ---------- Modelos de inventario ----------
from .models import Equipo, Mantenimiento, Prestamo

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('codigo_inventario', 'tipo_equipo', 'marca_modelo', 'estado', 'ubicacion', 'ver_ficha')
    list_filter = ('tipo_equipo', 'estado')
    search_fields = ('codigo_inventario', 'serial', 'marca_modelo')
    list_editable = ('estado',)

    def ver_ficha(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:ficha_equipo_pdf', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">📄 Ver Ficha PDF</a>', url)
    ver_ficha.short_description = 'Ficha PDF'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('ficha_pdf/<int:equipo_id>/', self.admin_site.admin_view(self.ficha_pdf), name='ficha_equipo_pdf'),
        ]
        return custom_urls + urls

    def ficha_pdf(self, request, equipo_id):
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from .models import Equipo, Mantenimiento, Prestamo
        import os
        from django.conf import settings

        equipo = Equipo.objects.get(pk=equipo_id)
        mantenimientos = Mantenimiento.objects.filter(equipo=equipo).order_by('-fecha')
        prestamos = Prestamo.objects.filter(equipo=equipo).order_by('-fecha_salida')

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ficha_{equipo.codigo_inventario}.pdf"'

        doc = SimpleDocTemplate(response, pagesize=A4, topMargin=2*cm, bottomMargin=1*cm)
        elementos = []
        styles = getSampleStyleSheet()

        # ========== ENCABEZADO CON LOGO Y TEXTO ==========
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_unefa.png')
        if not os.path.exists(logo_path):
            logo_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'img', 'logo_unefa.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*cm, height=2*cm)
        else:
            logo = Paragraph("(logo no encontrado)", styles['Normal'])

        estilo_texto = ParagraphStyle(name='Institucional', parent=styles['Normal'], fontSize=8, alignment=0)
        texto1 = Paragraph("REPÚBLICA BOLIVARIANA DE VENEZUELA<br/>MINISTERIO DEL PODER POPULAR PARA LA DEFENSA<br/>UNIVERSIDAD NACIONAL EXPERIMENTAL POLITÉCNICA<br/>DE LA FUERZA ARMADA NACIONAL<br/>Extensión Punto Fijo", estilo_texto)
        texto2 = Paragraph("SISTEMA DE GESTIÓN DE LABORATORIO (SGLUNEFA)<br/>Ficha Técnica de Equipo", estilo_texto)

        tabla_encabezado = Table([[logo, texto1, texto2]], colWidths=[2.5*cm, 8*cm, 6*cm])
        tabla_encabezado.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'CENTER'),
            ('ALIGN', (1,0), (1,0), 'LEFT'),
            ('ALIGN', (2,0), (2,0), 'RIGHT'),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ]))
        elementos.append(tabla_encabezado)
        elementos.append(Spacer(1, 0.5*cm))

        # Título del equipo
        titulo_style = ParagraphStyle(name='Titulo', parent=styles['Title'], fontSize=14, alignment=1)
        elementos.append(Paragraph(f"Ficha Técnica del Equipo: {equipo.codigo_inventario}", titulo_style))
        elementos.append(Spacer(1, 0.5*cm))

        # Datos del equipo
        data_equipo = [
            ['Campo', 'Valor'],
            ['Tipo', equipo.get_tipo_equipo_display()],
            ['Código inventario', equipo.codigo_inventario],
            ['ID UNEFA', equipo.id_unefa or '---'],
            ['Marca/Modelo', equipo.marca_modelo or '---'],
            ['Procesador', equipo.procesador or '---'],
            ['RAM', equipo.ram or '---'],
            ['Almacenamiento', equipo.almacenamiento or '---'],
            ['S.O.', equipo.sistema_operativo or '---'],
            ['Serial', equipo.serial or '---'],
            ['Ubicación', equipo.ubicacion or '---'],
            ['Estado', equipo.get_estado_display()],
            ['Observaciones', equipo.observaciones_generales or '---'],
            ['Fecha registro', equipo.fecha_registro.strftime('%d/%m/%Y')],
        ]
        tabla_equipo = Table(data_equipo, colWidths=[4*cm, 10*cm])
        tabla_equipo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elementos.append(tabla_equipo)
        elementos.append(Spacer(1, 0.5*cm))

        # Historial de mantenimientos
        if mantenimientos:
            elementos.append(Paragraph("Historial de Mantenimientos", styles['Heading2']))
            data_mant = [['Fecha', 'Tipo', 'Descripción', 'Técnico', 'Próxima revisión']]
            for m in mantenimientos:
                data_mant.append([
                    m.fecha.strftime('%d/%m/%Y'),
                    m.get_tipo_accion_display(),
                    m.descripcion[:80],
                    m.tecnico,
                    m.proxima_revision.strftime('%d/%m/%Y') if m.proxima_revision else '---'
                ])
            tabla_mant = Table(data_mant, colWidths=[2.5*cm, 3*cm, 6*cm, 3*cm, 2.5*cm])
            tabla_mant.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
            elementos.append(tabla_mant)
            elementos.append(Spacer(1, 0.5*cm))

        # Préstamos
        if prestamos:
            elementos.append(Paragraph("Registro de Préstamos", styles['Heading2']))
            data_prest = [['Salida', 'Motivo', 'Responsable', 'Retorno', 'Observaciones']]
            for p in prestamos:
                data_prest.append([
                    p.fecha_salida.strftime('%d/%m/%Y'),
                    p.motivo[:40],
                    p.responsable_recibe,
                    p.fecha_retorno.strftime('%d/%m/%Y') if p.fecha_retorno else 'Pendiente',
                    p.observaciones[:60] or '---'
                ])
            tabla_prest = Table(data_prest, colWidths=[2.5*cm, 4*cm, 3*cm, 2.5*cm, 4*cm])
            tabla_prest.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
            elementos.append(tabla_prest)

        doc.build(elementos)
        return response


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'fecha', 'tipo_accion', 'tecnico', 'proxima_revision')
    list_filter = ('tipo_accion', 'fecha')
    search_fields = ('equipo__codigo_inventario', 'tecnico')


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'fecha_salida', 'motivo', 'responsable_recibe', 'fecha_retorno')
    list_filter = ('fecha_salida',)
    search_fields = ('equipo__codigo_inventario', 'responsable_recibe')