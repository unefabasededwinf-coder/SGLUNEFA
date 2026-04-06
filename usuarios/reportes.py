import os
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from datetime import datetime, timedelta
from calendar import day_name
from .models import Reserva

# Diccionario para nombres de días en español
DIAS_ESP = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miércoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sábado',
    6: 'Domingo'
}

def generar_intervalos_45min(inicio_hora=7, fin_hora=22):
    """Genera intervalos de 45 minutos desde inicio_hora hasta fin_hora (sin incluir el último si excede)."""
    intervalos = []
    start = datetime(1,1,1, inicio_hora, 0)
    end = datetime(1,1,1, fin_hora, 0)
    while start < end:
        end_interval = start + timedelta(minutes=45)
        if end_interval > end:
            break
        intervalos.append((start.strftime('%H:%M'), end_interval.strftime('%H:%M')))
        start = end_interval
    return intervalos

def calendario_reservas_pdf(request):
    # Obtener fechas (lunes a sábado de la semana actual o por GET)
    hoy = datetime.now().date()
    lunes = hoy - timedelta(days=hoy.weekday())
    sabado = lunes + timedelta(days=5)

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    if fecha_inicio and fecha_fin:
        try:
            lunes = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            sabado = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except:
            pass

    # Obtener reservas en el rango
    reservas = Reserva.objects.filter(
        fecha__gte=lunes,
        fecha__lte=sabado
    ).select_related('materia', 'docente')

    # Agrupar por fecha
    from collections import defaultdict
    horario = defaultdict(list)
    for r in reservas:
        horario[r.fecha].append({
            'materia': r.materia.nombre,
            'docente': r.docente.get_full_name() or r.docente.username,
            'hora_inicio': r.hora_inicio,
            'hora_fin': r.hora_fin
        })

    # Construir cabecera de días en español
    dias = []
    fecha = lunes
    while fecha <= sabado:
        nombre_dia = DIAS_ESP[fecha.weekday()]
        dias.append(f"{nombre_dia}\n{fecha.strftime('%d/%m')}")
        fecha += timedelta(days=1)

    # Generar intervalos de 45 minutos desde 7:00 a 22:00
    intervalos = generar_intervalos_45min(7, 22)
    
    # Construir datos de la tabla
    data = [['Hora / Día'] + dias]
    for inicio, fin in intervalos:
        fila = [f"{inicio}-{fin}"]
        for idx, _ in enumerate(dias):
            fecha_actual = lunes + timedelta(days=idx)
            reservas_dia = horario.get(fecha_actual, [])
            texto = ""
            for r in reservas_dia:
                hora_inicio_str = r['hora_inicio'].strftime('%H:%M')
                hora_fin_str = r['hora_fin'].strftime('%H:%M')
                # Verificar solapamiento con el intervalo [inicio, fin)
                if hora_inicio_str < fin and hora_fin_str > inicio:
                    texto += f"{r['materia']} ({r['docente']}) {hora_inicio_str}-{hora_fin_str}\n"
            fila.append(texto.strip() if texto else '—')
        data.append(fila)

    # Crear PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="calendario_reservas_{lunes}_{sabado}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), topMargin=2*cm, bottomMargin=1*cm, leftMargin=0.5*cm, rightMargin=0.5*cm)
    elementos = []
    styles = getSampleStyleSheet()

    # Encabezado con logo y texto institucional
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_unefa.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'img', 'logo_unefa.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*cm, height=2*cm)
    else:
        logo = Paragraph("(logo)", styles['Normal'])

    estilo_texto = ParagraphStyle(name='Institucional', parent=styles['Normal'], fontSize=8, alignment=0)
    texto1 = Paragraph("REPÚBLICA BOLIVARIANA DE VENEZUELA<br/>MINISTERIO DEL PODER POPULAR PARA LA DEFENSA<br/>UNIVERSIDAD NACIONAL EXPERIMENTAL POLITÉCNICA<br/>DE LA FUERZA ARMADA NACIONAL<br/>Extensión Punto Fijo", estilo_texto)
    texto2 = Paragraph("SISTEMA DE GESTIÓN DE LABORATORIO (SGLUNEFA)<br/>Calendario de Reservas", estilo_texto)

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

    # Título
    titulo = Paragraph(f"Calendario de Reservas del {lunes.strftime('%d/%m/%Y')} al {sabado.strftime('%d/%m/%Y')}", styles['Title'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 0.5*cm))

    # Tabla de horarios con ajustes de tamaño
    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498db')),  # Azul
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),                 # Texto blanco (corregido)
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),                # Líneas en toda la tabla
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTSIZE', (0,0), (-1,-1), 5),                            # Letra pequeña para que quepan todas las filas
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elementos.append(tabla)

    doc.build(elementos)
    return response