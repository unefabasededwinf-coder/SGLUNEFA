from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Materia
from .models import Reserva, Materia
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import Requerimiento

class RegistroDocenteForm(forms.ModelForm):
    # Campo de identidad ajustado según tu requerimiento
    username = forms.CharField(
        label="Cédula o Nombre de Usuario", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12345678'})
    )
    
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="<ul style='color: white; list-style: disc; margin-left: 20px; text-align: left;'>"
                  "<li>Su contraseña no puede asemejarse tanto a su otra información personal.</li>"
                  "<li>Su contraseña debe contener por lo menos 8 caracteres.</li>"
                  "<li>Su contraseña no puede ser una clave utilizada comúnmente.</li>"
                  "<li>Su contraseña no puede ser completamente numérica.</li></ul>"
    )
    
    confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Esta cédula ya está registrada.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        nombre = cleaned_data.get('first_name', '').lower()
        apellido = cleaned_data.get('last_name', '').lower()

        if password:
            if password != confirm_password:
                self.add_error('confirm_password', "Las contraseñas no coinciden.")
            if password.isdigit():
                self.add_error('password', "Su contraseña no puede ser completamente numérica.")
            if nombre and nombre in password.lower():
                self.add_error('password', "Su contraseña no puede asemejarse tanto a su otra información personal (nombre).")
            if apellido and apellido in password.lower():
                self.add_error('password', "Su contraseña no puede asemejarse tanto a su otra información personal (apellido).")
            if len(password) < 8:
                self.add_error('password', "Su contraseña debe contener por lo menos 8 caracteres.")
        return cleaned_data

    def save(self, commit=True):
        # 1. Usamos create_user: esto encripta la clave y marca 'is_active=True' por defecto
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', '')
        )
        
        # 2. ACTIVACIÓN EXPLÍCITA: Para que Python lo reconozca como válido
        user.is_active = True 
        
        # 3. SEGURIDAD: Mantener el círculo rojo (Staff = False) 
        # para que el docente no entre a la parte administrativa.
        user.is_staff = False
        
        if commit:
            user.save()
        return user
    
class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['nombre', 'seccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Sistemas Operativos II'}),
            'seccion': forms.TextInput(attrs={'placeholder': 'Ej. D01'}),
        }
# reserva de laboratorio
class ReservaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['materia'].queryset = Materia.objects.filter(docente=user)

    class Meta:
        model = Reserva
        fields = ['materia', 'fecha', 'hora_inicio', 'hora_fin']

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        inicio = cleaned_data.get('hora_inicio')
        fin = cleaned_data.get('hora_fin')

        if fecha and inicio and fin:
            # 1. Validar que la hora de fin sea después de la de inicio
            if fin <= inicio:
                raise forms.ValidationError("La hora de finalización debe ser posterior a la de inicio.")

            # 2. Lógica de Colisión (El "corazón" del problema)
            # Buscamos reservas que coincidan en fecha Y que se solapen en el rango horario
            solapamientos = Reserva.objects.filter(
                fecha=fecha
            ).filter(
                Q(hora_inicio__lt=fin, hora_fin__gt=inicio)
            )

            if solapamientos.exists():
                reserva_conflicto = solapamientos.first()
                raise forms.ValidationError(
                    f"🚫 El laboratorio ya está ocupado en ese horario por la materia: {reserva_conflicto.materia.nombre}"
                )
        
        return cleaned_data

class RequerimientoForm(forms.ModelForm):
    class Meta:
        model = Requerimiento
        fields = ['tipo', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describa la solicitud en detalle...'}),
        }