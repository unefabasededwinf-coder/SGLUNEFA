from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import never_cache
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime
from .forms import RegistroDocenteForm, MateriaForm, ReservaForm
from .models import Perfil, Materia, Reserva
from .forms import RequerimientoForm  # asegúrate de crear este formulario en forms.py
from .models import Requerimiento

# ... (aquí van todas las funciones que ya tenías) ...

# ------------------- FUNCIONES EXISTENTES -------------------
def index(request):
    return render(request, 'index.html')

from django.utils import timezone
from .models import Reserva, Materia

@login_required
def inicio_docente(request):
    hoy = timezone.localtime()
    # Próximas reservas del docente (futuras o de hoy con hora_fin mayor a ahora)
    reservas_proximas = Reserva.objects.filter(
        docente=request.user,
        fecha__gte=hoy.date()
    ).exclude(
        fecha=hoy.date(),
        hora_fin__lt=hoy.time()
    ).order_by('fecha', 'hora_inicio')[:10]   # limitar a 10

    # Materias activas del docente
    materias_activas = Materia.objects.filter(docente=request.user).order_by('nombre')

    return render(request, 'usuarios/inicio.html', {
        'reservas_proximas': reservas_proximas,
        'materias_activas': materias_activas,
    })

@never_cache
def registro_view(request):
    if request.method == 'POST':
        form = RegistroDocenteForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            Perfil.objects.create(
                user=user,
                rol='docente',
                nombre_docente=f"{form.cleaned_data.get('first_name', '')} {form.cleaned_data.get('last_name', '')}".strip()
            )
            messages.success(request, f'¡Cuenta creada para {user.username}!')
            return redirect('login')
    else:
        form = RegistroDocenteForm()
    return render(request, 'registration/registration.html', {'form': form})

@login_required
def lista_requerimientos(request):
    if request.method == 'POST':
        form = RequerimientoForm(request.POST)
        if form.is_valid():
            requerimiento = form.save(commit=False)
            requerimiento.usuario = request.user
            requerimiento.save()
            messages.success(request, "✅ Solicitud enviada correctamente.")
            return redirect('mis_requerimientos')
        else:
            messages.error(request, "Error en el formulario. Verifica los datos.")
    else:
        form = RequerimientoForm()

    requerimientos = Requerimiento.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'admin/mis_requerimientos.html', {
        'form': form,
        'requerimientos': requerimientos,
    })

@login_required
def vista_usuarios_admin(request):
    if not request.user.is_staff:
        raise PermissionDenied
    return render(request, 'usuarios_lista.html')

@user_passes_test(lambda u: u.is_superuser)
def lista_usuarios(request):
    return render(request, 'admin_usuarios.html')

# ------------------- GESTIÓN DE MATERIAS (con edición y eliminación) -------------------
@method_decorator(login_required, name='dispatch')
class GestionMateriaView(ListView):
    model = Materia
    template_name = 'admin/gestion_materias.html'
    context_object_name = 'materias'

    def get_queryset(self):
        return Materia.objects.filter(docente=self.request.user).order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MateriaForm()
        return context

    def post(self, request, *args, **kwargs):
        materia_id = request.POST.get('materia_id')
        nombre = request.POST.get('nombre')
        seccion = request.POST.get('seccion')

        if not nombre or not seccion:
            messages.error(request, "Ambos campos son obligatorios.")
            return redirect('gestion_materias')

        # Verificar duplicados (excluyendo la propia materia en edición)
        qs = Materia.objects.filter(docente=request.user, nombre=nombre, seccion=seccion)
        if materia_id:
            qs = qs.exclude(id=materia_id)

        if qs.exists():
            messages.error(request, "Ya existe una materia con el mismo nombre y sección.")
            return redirect('gestion_materias')

        if materia_id:
            materia = get_object_or_404(Materia, id=materia_id, docente=request.user)
            materia.nombre = nombre
            materia.seccion = seccion
            materia.save()
            messages.success(request, "Materia actualizada correctamente.")
        else:
            materia = Materia(docente=request.user, nombre=nombre, seccion=seccion)
            materia.save()
            messages.success(request, "Materia agregada con éxito.")

        return redirect('gestion_materias')

@login_required
def eliminar_materia(request, materia_id):
    if request.method == 'POST':
        materia = get_object_or_404(Materia, id=materia_id, docente=request.user)
        if materia.reserva_set.exists():
            return JsonResponse({'success': False, 'error': 'No se puede eliminar la materia porque tiene reservas asociadas.'})
        materia.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

# ------------------- RESERVAS (con validaciones server-side) -------------------
@method_decorator(login_required, name='dispatch')
class CrearReservaView(ListView):
    model = Reserva
    template_name = 'admin/crear_reserva.html'
    context_object_name = 'mis_reservas'

    def get_queryset(self):
        return Reserva.objects.filter(docente=self.request.user).order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ahora = timezone.localtime()
        context['todas_las_reservas'] = (
            Reserva.objects.filter(fecha__gt=ahora.date()) |
            Reserva.objects.filter(fecha=ahora.date(), hora_fin__gt=ahora.time())
        ).order_by('fecha', 'hora_inicio')
        context['form'] = ReservaForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        form = ReservaForm(request.POST, user=request.user)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            hora_inicio = form.cleaned_data['hora_inicio']
            hora_fin = form.cleaned_data['hora_fin']
            now = timezone.localtime()

            # Validaciones server-side
            if fecha < now.date():
                messages.error(request, "No se puede reservar en fechas pasadas.")
                return self.get(request, *args, **kwargs)

            max_date = now.date() + timezone.timedelta(days=14)
            if fecha > max_date:
                messages.error(request, "No se puede reservar con más de 14 días de anticipación.")
                return self.get(request, *args, **kwargs)

            if fecha == now.date():
                inicio_dt = timezone.make_aware(
                    datetime.combine(fecha, hora_inicio),
                    timezone.get_current_timezone()
                )
                if inicio_dt < now:
                    messages.error(request, f"No se puede reservar para una hora que ya ha pasado (hora actual: {now.strftime('%H:%M')}).")
                    return self.get(request, *args, **kwargs)

            if hora_inicio >= hora_fin:
                messages.error(request, "La hora de fin debe ser posterior a la hora de inicio.")
                return self.get(request, *args, **kwargs)

            reserva = form.save(commit=False)
            reserva.docente = request.user
            reserva.save()
            messages.success(request, "✅ ¡Reserva realizada con éxito!")
            return redirect('crear_reserva')

                # Eliminar mensajes duplicados
        errores_unicos = set()
        for error in form.non_field_errors():
            errores_unicos.add(error)
        for field, errors in form.errors.items():
            for error in errors:
                # Evitar mostrar el mismo error dos veces si ya está en non_field_errors
                if error not in errores_unicos:
                    errores_unicos.add(f"{field}: {error}")
        for error in errores_unicos:
            messages.error(request, error)

        return self.get(request, *args, **kwargs)
    
    from django.utils import timezone
from .models import Reserva, Materia

from django.utils import timezone
from .models import Reserva, Materia

@login_required
def inicio_docente(request):
    hoy = timezone.localtime()
    # Todas las reservas futuras o de hoy con hora_fin > ahora (para mostrar a todos los docentes)
    reservas_proximas = Reserva.objects.filter(
        fecha__gte=hoy.date()
    ).exclude(
        fecha=hoy.date(),
        hora_fin__lt=hoy.time()
    ).order_by('fecha', 'hora_inicio')[:10]  # limitar a 10 para no saturar

    # Materias activas del docente actual
    materias_activas = Materia.objects.filter(docente=request.user).order_by('nombre')

    return render(request, 'usuarios/inicio.html', {
        'reservas_proximas': reservas_proximas,
        'materias_activas': materias_activas,
    })
    # ------------------- EDICIÓN DE RESERVAS -------------------
@login_required
def editar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, docente=request.user)

    # No permitir editar reservas pasadas
    if reserva.fecha < timezone.now().date():
        messages.error(request, "No se puede editar una reserva que ya pasó.")
        return redirect('crear_reserva')

    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva, user=request.user)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            hora_inicio = form.cleaned_data['hora_inicio']
            hora_fin = form.cleaned_data['hora_fin']
            now = timezone.localtime()

            # Validaciones server-side (copiadas de la creación)
            if fecha < now.date():
                messages.error(request, "No se puede reservar en fechas pasadas.")
                return redirect('crear_reserva')
            max_date = now.date() + timezone.timedelta(days=14)
            if fecha > max_date:
                messages.error(request, "No se puede reservar con más de 14 días de anticipación.")
                return redirect('crear_reserva')
            if fecha == now.date():
                inicio_dt = timezone.make_aware(
                    datetime.combine(fecha, hora_inicio),
                    timezone.get_current_timezone()
                )
                if inicio_dt < now:
                    messages.error(request, f"No se puede reservar para una hora que ya ha pasado (hora actual: {now.strftime('%H:%M')}).")
                    return redirect('crear_reserva')
            if hora_inicio >= hora_fin:
                messages.error(request, "La hora de fin debe ser posterior a la hora de inicio.")
                return redirect('crear_reserva')

            # Guardar cambios
            form.save()
            messages.success(request, "✅ Reserva actualizada correctamente.")
            return redirect('crear_reserva')
        else:
            errores_unicos = set()
            for error in form.non_field_errors():
                errores_unicos.add(error)
            for field, errors in form.errors.items():
                for error in errors:
                    if error not in errores_unicos:
                        errores_unicos.add(f"{field}: {error}")
            for error in errores_unicos:
                messages.error(request, error)
            return redirect('crear_reserva')
    else:
        form = ReservaForm(instance=reserva, user=request.user)
        return render(request, 'admin/editar_reserva.html', {'form': form, 'reserva': reserva})