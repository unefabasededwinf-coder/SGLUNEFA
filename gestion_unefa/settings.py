import os
from pathlib import Path

# 1. RUTAS BASE 🏠
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. SEGURIDAD 🛡️
SECRET_KEY = 'django-insecure-_y-mgm%)wkaf3@=v$d2+v9chi7hx)w0f_4cis$^2&lf(4_l1=s'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# 3. APLICACIONES INSTALADAS (Fundamental para evitar el RuntimeError) 📦
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios', # Tu aplicación de gestión de usuarios
]

# 4. MIDDLEWARE (Control de sesiones y seguridad CSRF) 🔒
MIDDLEWARE = [
    'usuarios.middleware.NoCacheMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

# 5. EL "MAPA" DE RUTAS 📍
ROOT_URLCONF = 'gestion_unefa.urls'

# 6. CONFIGURACIÓN DE PLANTILLAS 📄
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Busca aquí tus archivos HTML
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_unefa.wsgi.application'

# 7. BASE DE DATOS 🗄️
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 8. INTERNACIONALIZACIÓN 🇻🇪
LANGUAGE_CODE = 'es-ve'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True

# 9. ARCHIVOS ESTÁTICOS 🖼️
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# 10. CONFIGURACIÓN DE CORREO 📧
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'unefa.based.edwinf@gmail.com'
EMAIL_HOST_PASSWORD = 'esie qgwr iqeb votn'
DEFAULT_FROM_EMAIL = 'Gestión de Laboratorio UNEFA <unefa.based.edwinf@gmail.com>'

# 11. REDIRECCIONES DE FLUJO 🔄
LOGIN_REDIRECT_URL = 'inicio'
LOGOUT_REDIRECT_URL = 'index'