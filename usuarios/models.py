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