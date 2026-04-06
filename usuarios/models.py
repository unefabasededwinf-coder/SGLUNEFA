from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Perfil(models.Model):
    ROLES = (
        ('admin', 'Administrador'),
        ('docente', 'Docente'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=10, choices=ROLES, default='docente')
    nombre_docente = models.CharField(max_length=100)
    materia = models.CharField(max_length=100)
    seccion = models.CharField(max_length=20)
    semestre = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.user.username} - {self.materia}"


class Materia(models.Model):
    docente = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    seccion = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"

    def __str__(self):
        return f"{self.nombre} - {self.seccion}"


class Reserva(models.Model):
    docente = models.ForeignKey(User, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.materia.nombre} - {self.fecha}"


class Requerimiento(models.Model):
    TIPO_CHOICES = [
        ('software', 'Instalación de software'),
        ('eliminar', 'Eliminación de archivos'),
        ('falla', 'Falla de equipo'),
        ('otros', 'Otros'),
    ]
    ESTADO_CHOICES = [
        ('enviado', 'Enviado'),
        ('proceso', 'En proceso'),
        ('completado', 'Completado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requerimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='enviado')

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo} - {self.fecha_creacion.strftime('%d/%m/%Y')}"


        # ==========================================
# MODELOS PARA INVENTARIO Y MANTENIMIENTO
# ==========================================

class Equipo(models.Model):
    TIPO_EQUIPO_CHOICES = [
        ('laptop', 'Laptop'),
        ('regleta', 'Regleta eléctrica'),
        ('televisor', 'Televisor'),
        ('otro', 'Otro'),
    ]
    ESTADO_CHOICES = [
        ('operativo', 'Operativo'),
        ('reparacion', 'En reparación'),
        ('baja', 'Dado de baja'),
    ]

    tipo_equipo = models.CharField(max_length=20, choices=TIPO_EQUIPO_CHOICES, default='laptop')
    codigo_inventario = models.CharField(max_length=50, unique=True, verbose_name='Código de inventario')
    id_unefa = models.CharField(max_length=100, blank=True, verbose_name='ID UNEFA')
    marca_modelo = models.CharField(max_length=200, blank=True, verbose_name='Marca/Modelo')
    procesador = models.CharField(max_length=100, blank=True)
    ram = models.CharField(max_length=50, blank=True)
    almacenamiento = models.CharField(max_length=100, blank=True)
    sistema_operativo = models.CharField(max_length=100, blank=True, verbose_name='S.O.')
    serial = models.CharField(max_length=100, unique=True, blank=True, verbose_name='Número de serie')
    ubicacion = models.CharField(max_length=200, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='operativo')
    observaciones_generales = models.TextField(blank=True, verbose_name='Observaciones generales')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'
        ordering = ['tipo_equipo', 'codigo_inventario']

    def __str__(self):
        return f"{self.get_tipo_equipo_display()} - {self.codigo_inventario}"


class Mantenimiento(models.Model):
    TIPO_ACCION_CHOICES = [
        ('instalacion', 'Instalación de software'),
        ('limpieza', 'Limpieza'),
        ('reparacion', 'Reparación'),
        ('mantenimiento', 'Mantenimiento preventivo'),
        ('otros', 'Otros'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='mantenimientos')
    fecha = models.DateField()
    tipo_accion = models.CharField(max_length=50, choices=TIPO_ACCION_CHOICES, verbose_name='Tipo de acción')
    descripcion = models.TextField(verbose_name='Descripción')
    tecnico = models.CharField(max_length=100)
    piezas_cambiadas = models.CharField(max_length=200, blank=True, verbose_name='Piezas cambiadas')
    proxima_revision = models.DateField(null=True, blank=True, verbose_name='Próxima revisión')
    observacion = models.TextField(blank=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Mantenimiento'
        verbose_name_plural = 'Mantenimientos'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.equipo} - {self.fecha} - {self.get_tipo_accion_display()}"


class Prestamo(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='prestamos')
    fecha_salida = models.DateField(verbose_name='Fecha de salida')
    motivo = models.CharField(max_length=200, verbose_name='Motivo', help_text='Ej: Jornada de carnetización, Préstamo a otra aula')
    responsable_recibe = models.CharField(max_length=100, verbose_name='Persona o entidad que recibe')
    fecha_retorno = models.DateField(null=True, blank=True, verbose_name='Fecha de retorno')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'
        ordering = ['-fecha_salida']

    def __str__(self):
        return f"{self.equipo} - Salida: {self.fecha_salida} - {'Retornado' if self.fecha_retorno else 'Prestado'}"