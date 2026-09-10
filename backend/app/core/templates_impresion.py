"""
Plantilla HTML y generador para la impresión de indicaciones clínicas de preparación para estudios.
"""
from datetime import datetime
from typing import Optional
import html


INDICACION_DEFAULT_HTML = (
    "<p><strong>• Recordatorio importante:</strong> Concurrir al laboratorio con documento de identidad vigente (DNI) "
    "y credencial física o digital de su Obra Social / Prepaga.</p>\n"
    "<p><strong>• Orden Médica en papel:</strong> Si cuenta con la receta u orden médica física emitida por su médico, "
    "recuerde presentarla indefectiblemente el día de la extracción.</p>\n"
    "<p><strong>• Horario habitual de atención y extracciones:</strong> Lunes a Viernes de 7:00 a 11:30 hs. "
    "Sábados de 7:30 a 10:30 hs (atención por orden de llegada).</p>"
)


def obtener_template_base_impresion_html() -> str:
    """Retorna el código HTML/CSS oficial de la plantilla de impresión de indicaciones."""
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Indicaciones para el Paciente - {{paciente_nombre}}</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      color: #1e293b;
      background: #ffffff;
      padding: 24px;
      font-size: 13.5px;
      line-height: 1.5;
    }
    .print-container {
      max-width: 800px;
      margin: 0 auto;
      border: 1px solid #cbd5e1;
      padding: 28px 32px;
      border-radius: 8px;
    }
    /* Membrete / Encabezado */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2px solid #0284c7;
      padding-bottom: 16px;
      margin-bottom: 20px;
    }
    .brand-title {
      font-size: 19px;
      font-weight: 800;
      color: #0369a1;
      letter-spacing: -0.3px;
      text-transform: uppercase;
    }
    .brand-subtitle {
      font-size: 12px;
      font-weight: 600;
      color: #64748b;
      margin-top: 2px;
    }
    .meta-date {
      text-align: right;
      font-size: 12px;
      color: #475569;
    }
    .meta-date strong {
      color: #0f172a;
    }

    /* Caja de Datos del Paciente */
    .patient-box {
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 12px 16px;
      margin-bottom: 22px;
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 10px;
    }
    .patient-field {
      font-size: 13px;
    }
    .patient-field span {
      font-weight: 700;
      color: #334155;
      text-transform: uppercase;
      font-size: 11px;
      display: block;
      margin-bottom: 2px;
    }
    .patient-value {
      font-size: 14.5px;
      font-weight: 700;
      color: #0f172a;
    }

    /* Sección de Indicaciones */
    .section-title {
      font-size: 13px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #0284c7;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .indicaciones-body {
      background-color: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 16px 20px;
      margin-bottom: 22px;
      font-size: 14px;
      color: #1e293b;
      line-height: 1.6;
    }
    .indicaciones-body p {
      margin-bottom: 8px;
    }
    .indicaciones-body p:last-child {
      margin-bottom: 0;
    }
    .indicaciones-body ul, .indicaciones-body ol {
      margin-left: 20px;
      margin-bottom: 8px;
    }
    .indicaciones-body li {
      margin-bottom: 4px;
    }
    .indicaciones-body mark {
      background-color: #fef08a;
      padding: 1px 4px;
      border-radius: 3px;
    }

    /* Caja de Indicación por Defecto / Requisitos Generales */
    .default-box {
      background-color: #fffbeb;
      border: 1px solid #fde68a;
      border-left: 4px solid #f59e0b;
      border-radius: 6px;
      padding: 14px 18px;
      margin-bottom: 24px;
      font-size: 12.5px;
      color: #78350f;
      line-height: 1.5;
    }
    .default-box .default-title {
      font-size: 11.5px;
      font-weight: 800;
      text-transform: uppercase;
      color: #b45309;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .default-box p {
      margin-bottom: 4px;
    }
    .default-box p:last-child {
      margin-bottom: 0;
    }

    /* Pie de Página */
    .footer {
      border-top: 1px dashed #cbd5e1;
      padding-top: 16px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      font-size: 11.5px;
      color: #64748b;
    }
    .footer-info p {
      margin-bottom: 2px;
    }
    .signature-area {
      text-align: center;
      width: 200px;
      border-top: 1px solid #94a3b8;
      padding-top: 4px;
      font-size: 11px;
      color: #475569;
    }

    /* Reglas para Impresión */
    @media print {
      body {
        padding: 0;
        background: #ffffff;
      }
      .print-container {
        border: none;
        padding: 0;
        max-width: 100%;
      }
      .no-print {
        display: none !important;
      }
    }
    @page {
      size: A4 portrait;
      margin: 15mm 15mm 15mm 15mm;
    }
  </style>
</head>
<body>
  <div class="print-container">
    <!-- Encabezado / Membrete -->
    <div class="header">
      <div>
        <div class="brand-title">Laboratorio de Análisis Clínicos</div>
        <div class="brand-subtitle">Indicaciones y Preparación Previa para Estudios Médicos</div>
      </div>
      <div class="meta-date">
        <div>Fecha: <strong>{{fecha}}</strong></div>
        <div>Sede: <strong>{{sucursal_nombre}}</strong></div>
      </div>
    </div>

    <!-- Ficha del Paciente -->
    <div class="patient-box">
      <div class="patient-field">
        <span>Paciente</span>
        <div class="patient-value">{{paciente_nombre}}</div>
      </div>
      <div class="patient-field" style="text-align: right;">
        <span>Cobertura Médica</span>
        <div style="font-weight: 600; color: #1e293b;">{{mutual}}</div>
      </div>
    </div>

    <!-- Indicaciones Clínicas Específicas -->
    <div class="section-title">
      📋 Instrucciones para sus Prácticas
    </div>
    <div class="indicaciones-body">
      {{indicaciones}}
    </div>

    <!-- Requisitos Generales de Recepción (Default) -->
    <div class="default-box">
      <div class="default-title">
        ℹ️ Requisitos Generales para su Atención
      </div>
      {{indicacion_default}}
    </div>

    <!-- Pie de Página -->
    <div class="footer">
      <div class="footer-info">
        <p><strong>{{sucursal_nombre}}</strong></p>
        <p>Consultas y recepción: {{contacto_telefono}}</p>
        <p style="font-size: 10px; color: #94a3b8; margin-top: 4px;">Por favor presente esta hoja al concurrir al laboratorio.</p>
      </div>
      <div class="signature-area">
        Firma y Sello de Recepción
      </div>
    </div>
  </div>
</body>
</html>"""


def generar_html_impresion_indicaciones(
    paciente_nombre: str,
    fecha: Optional[str] = None,
    sucursal_nombre: Optional[str] = None,
    contacto_telefono: Optional[str] = None,
    nro_orden: Optional[str] = None,
    mutual: Optional[str] = None,
    indicaciones_html: Optional[str] = None,
    indicacion_default_html: Optional[str] = None,
    template_custom: Optional[str] = None,
) -> str:
    """
    Ensambla el documento HTML completo para imprimir reemplazando los marcadores dinámicos.
    """
    tpl = template_custom.strip() if template_custom and template_custom.strip() else obtener_template_base_impresion_html()

    fecha_str = fecha or datetime.now().strftime("%d/%m/%Y")
    paciente_str = paciente_nombre.strip() if paciente_nombre and paciente_nombre.strip() else "Paciente"
    sucursal_str = sucursal_nombre.strip() if sucursal_nombre and sucursal_nombre.strip() else "Sede Central"
    telefono_str = contacto_telefono.strip() if contacto_telefono and contacto_telefono.strip() else "Recepción"
    orden_str = nro_orden.strip() if nro_orden and nro_orden.strip() else "S/N"
    mutual_str = mutual.strip() if mutual and mutual.strip() else "Particular / Sin especificar"

    ind_html = indicaciones_html.strip() if indicaciones_html and indicaciones_html.strip() else "<p><em>No se especificaron indicaciones adicionales.</em></p>"
    ind_def = indicacion_default_html.strip() if indicacion_default_html and indicacion_default_html.strip() else INDICACION_DEFAULT_HTML

    replacements = {
        "{{paciente_nombre}}": html.escape(paciente_str),
        "{{fecha}}": html.escape(fecha_str),
        "{{sucursal_nombre}}": html.escape(sucursal_str),
        "{{contacto_telefono}}": html.escape(telefono_str),
        "{{nro_orden}}": html.escape(orden_str),
        "{{mutual}}": html.escape(mutual_str),
        "{{indicaciones}}": ind_html,
        "{{indicacion_default}}": ind_def,
    }

    for key, val in replacements.items():
        tpl = tpl.replace(key, val)

    return tpl
