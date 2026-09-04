import html
from typing import List, Optional
from decimal import Decimal


def generar_plantilla_email_resolucion(
    paciente_nombre: str,
    nro_orden: str,
    mutual_nombre: str,
    observacion_resolucion: str,
    copago: Decimal,
    estudios_no_autorizados_valor: Decimal,
    valor_apb: Decimal,
    total_abonar: Decimal,
    indicaciones_texto: Optional[str] = None,
    sucursal_nombre: Optional[str] = None,
    contacto_telefono: Optional[str] = None,
    lista_estudios_autorizados: Optional[List[str]] = None,
    lista_estudios_no_autorizados: Optional[List[str]] = None,
    cuerpo_template_custom: Optional[str] = None,
) -> str:
    """Genera una plantilla HTML responsive y corporativa para notificar la resolución de auditoría."""
    safe_paciente = html.escape(paciente_nombre or "Estimado/a Paciente")
    safe_orden = html.escape(nro_orden or "")
    safe_mutual = html.escape(mutual_nombre or "")
    safe_resolucion = html.escape(observacion_resolucion or "").replace("\n", "<br>")
    safe_sucursal = html.escape(sucursal_nombre or "Sede Central")
    safe_indicaciones = html.escape(indicaciones_texto or "").replace("\n", "<br>") if indicaciones_texto else ""

    aut_list = [s.strip() for s in (lista_estudios_autorizados or []) if s.strip()]
    no_aut_list = [s.strip() for s in (lista_estudios_no_autorizados or []) if s.strip()]

    aut_str = ", ".join(aut_list) if aut_list else "Todas las prácticas de la prescripción médica"
    no_aut_str = ", ".join(no_aut_list) if no_aut_list else "Ninguno (100% autorizado)"

    # Bloque HTML para Estudios Autorizados y No Autorizados
    bloque_estudios_html = f"""
    <div style="margin-bottom: 24px; display: grid; gap: 12px;">
        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px 18px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #166534; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">
                ✓ Estudios Autorizados por la Mutual
            </div>
            <div style="font-size: 13.5px; color: #14532d; font-weight: 600;">
                {html.escape(aut_str)}
            </div>
        </div>

        <div style="background-color: {'#fff1f2' if no_aut_list else '#f8fafc'}; border: 1px solid {'#fecdd3' if no_aut_list else '#e2e8f0'}; border-radius: 8px; padding: 14px 18px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: {'#9f1239' if no_aut_list else '#64748b'}; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">
                {'✕ Estudios No Autorizados (a cargo del paciente)' if no_aut_list else '✓ Estudios No Autorizados'}
            </div>
            <div style="font-size: 13.5px; color: {'#881337' if no_aut_list else '#475569'}; font-weight: {'700' if no_aut_list else '400'};">
                {html.escape(no_aut_str)}
            </div>
        </div>
    </div>
    """

    indicaciones_html = ""
    if safe_indicaciones.strip():
        indicaciones_html = f"""
        <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 16px 20px; border-radius: 6px; margin: 24px 0;">
            <h3 style="margin: 0 0 8px 0; color: #92400e; font-size: 15px; font-weight: 700;">
                📋 Indicaciones de Preparación para sus Estudios
            </h3>
            <div style="font-size: 13.5px; color: #78350f; line-height: 1.6;">
                {safe_indicaciones}
            </div>
        </div>
        """

    # Si se proporcionó un cuerpo_template_custom, reemplazamos las variables estándar
    if cuerpo_template_custom and cuerpo_template_custom.strip():
        tpl = cuerpo_template_custom
        replacements = {
            "{{paciente_nombre}}": safe_paciente,
            "{{nro_orden}}": safe_orden,
            "{{mutual}}": safe_mutual,
            "{{observacion_resultado}}": safe_resolucion,
            "{{copago}}": f"${copago:,.2f}",
            "{{estudios_no_autorizados_valor}}": f"${estudios_no_autorizados_valor:,.2f}",
            "{{valor_apb}}": f"${valor_apb:,.2f}",
            "{{total_abonar}}": f"${total_abonar:,.2f}",
            "{{estudios_autorizados}}": html.escape(aut_str),
            "{{estudios_no_autorizados}}": html.escape(no_aut_str),
            "{{indicaciones}}": safe_indicaciones,
            "{{sucursal_nombre}}": safe_sucursal,
        }
        for k, v in replacements.items():
            tpl = tpl.replace(k, v)
        return tpl

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resolución de Auditoría Médica - {safe_orden}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px 12px; color: #1e293b;">
    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 620px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); overflow: hidden; border: 1px solid #e2e8f0;">
                    <!-- Header Corporativo -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); padding: 28px 24px; text-align: left; color: #ffffff;">
                            <div style="font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #bae6fd; margin-bottom: 4px;">
                                Laboratorio de Análisis Clínicos
                            </div>
                            <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #ffffff;">
                                Resolución de Auditoría Médica
                            </h1>
                            <div style="font-size: 13px; color: #e0f2fe; margin-top: 6px;">
                                Orden N°: <strong style="color: #ffffff;">{safe_orden}</strong> &bull; Obra Social: {safe_mutual}
                            </div>
                        </td>
                    </tr>

                    <!-- Cuerpo Principal -->
                    <tr>
                        <td style="padding: 28px 24px;">
                            <p style="font-size: 15px; line-height: 1.5; margin: 0 0 16px 0;">
                                Hola <strong>{safe_paciente}</strong>,
                            </p>
                            <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 20px 0;">
                                Le informamos que la auditoría médica correspondiente a su orden ha finalizado. A continuación detallamos las prácticas autorizadas, los estudios que no cuentan con cobertura y el desglose de importes a abonar:
                            </p>

                            <!-- Prácticas Autorizadas y No Autorizadas -->
                            {bloque_estudios_html}

                            <!-- Resolución Médica / Observación General -->
                            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; margin-bottom: 24px;">
                                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 4px;">
                                    Observación de Auditoría Médica
                                </div>
                                <div style="font-size: 13.5px; color: #1e293b; line-height: 1.6;">
                                    {safe_resolucion}
                                </div>
                            </div>

                            <!-- Desglose Económico -->
                            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin-bottom: 24px;">
                                <div style="background-color: #0f172a; color: #ffffff; padding: 10px 16px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                                    Desglose de Importes a Abonar
                                </div>
                                <table width="100%" cellpadding="10" cellspacing="0" style="font-size: 13.5px; border-collapse: collapse;">
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="color: #475569; padding-left: 16px;">Copago / Bono Mutual:</td>
                                        <td align="right" style="font-weight: 600; padding-right: 16px;">${copago:,.2f}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="color: #475569; padding-left: 16px;">Estudios No Autorizados:</td>
                                        <td align="right" style="font-weight: 600; padding-right: 16px; color: {'#b91c1c' if estudios_no_autorizados_valor > 0 else '#475569'};">${estudios_no_autorizados_valor:,.2f}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #cbd5e1;">
                                        <td style="color: #475569; padding-left: 16px;">Acto Profesional Bioquímico (APB):</td>
                                        <td align="right" style="font-weight: 600; padding-right: 16px;">${valor_apb:,.2f}</td>
                                    </tr>
                                    <tr style="background-color: #eff6ff;">
                                        <td style="color: #1e3a8a; font-weight: 700; font-size: 14.5px; padding-left: 16px;">TOTAL A ABONAR:</td>
                                        <td align="right" style="color: #1d4ed8; font-weight: 800; font-size: 17px; padding-right: 16px;">${total_abonar:,.2f}</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Indicaciones de Preparación (si existen) -->
                            {indicaciones_html}

                            <!-- Aviso de Comunicación Directa -->
                            <div style="background-color: #f1f5f9; border-radius: 8px; padding: 14px 18px; margin-top: 24px; font-size: 12.5px; color: #475569; line-height: 1.5;">
                                <strong>📞 Comunicación Directa:</strong> Personal de nuestro laboratorio se pondrá en contacto telefónico con usted para coordinar su turno de atención o resolver cualquier duda sobre su preparación.
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 24px; text-align: center; font-size: 11.5px; color: #64748b;">
                            <div>{safe_sucursal} &bull; Laboratorio Bioquímico de Análisis Clínicos</div>
                            <div style="margin-top: 4px;">Este es un mensaje informativo generado por el Sistema de Gestión de Órdenes Médicas.</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""



def obtener_plantilla_base_html() -> str:
    """Devuelve el código HTML inicial de la plantilla predeterminada con todas las variables."""
    return """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resolución de Auditoría Médica - {{nro_orden}}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px 12px; color: #1e293b;">
    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 620px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); overflow: hidden; border: 1px solid #e2e8f0;">
                    <!-- Header Corporativo -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); padding: 28px 24px; text-align: left; color: #ffffff;">
                            <div style="font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #bae6fd; margin-bottom: 4px;">
                                Laboratorio de Análisis Clínicos
                            </div>
                            <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #ffffff;">
                                Resolución de Auditoría Médica
                            </h1>
                            <div style="font-size: 13px; color: #e0f2fe; margin-top: 6px;">
                                Orden N°: <strong style="color: #ffffff;">{{nro_orden}}</strong> &bull; Obra Social: {{mutual}}
                            </div>
                        </td>
                    </tr>

                    <!-- Cuerpo Principal -->
                    <tr>
                        <td style="padding: 28px 24px;">
                            <p style="font-size: 15px; line-height: 1.5; margin: 0 0 16px 0;">
                                Hola <strong>{{paciente_nombre}}</strong>,
                            </p>
                            <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 20px 0;">
                                Le informamos que la auditoría médica correspondiente a su orden ha finalizado. A continuación detallamos las prácticas autorizadas, los estudios que no cuentan con cobertura y el desglose de importes a abonar:
                            </p>

                            <!-- Estudios Autorizados -->
                            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;">
                                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #166534; margin-bottom: 4px;">
                                    ✓ Estudios Autorizados por la Mutual
                                </div>
                                <div style="font-size: 13.5px; color: #14532d; font-weight: 600;">
                                    {{estudios_autorizados}}
                                </div>
                            </div>

                            <!-- Estudios No Autorizados -->
                            <div style="background-color: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; padding: 14px 18px; margin-bottom: 24px;">
                                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #9f1239; margin-bottom: 4px;">
                                    ✕ Estudios No Autorizados (a cargo del paciente)
                                </div>
                                <div style="font-size: 13.5px; color: #881337; font-weight: 700;">
                                    {{estudios_no_autorizados}}
                                </div>
                            </div>

                            <!-- Observación Médica -->
                            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; margin-bottom: 24px;">
                                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 4px;">
                                    Observación de Auditoría Médica
                                </div>
                                <div style="font-size: 13.5px; color: #1e293b; line-height: 1.6;">
                                    {{observacion_resultado}}
                                </div>
                            </div>

                            <!-- Desglose Económico -->
                            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin-bottom: 24px;">
                                <div style="background-color: #0f172a; color: #ffffff; padding: 10px 16px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                                    Desglose de Importes a Abonar
                                </div>
                                <table width="100%" cellpadding="10" cellspacing="0" style="font-size: 13.5px; border-collapse: collapse;">
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="color: #475569; padding-left: 16px;">Copago / Bono Mutual:</td>
                                        <td align="right" style="font-weight: 600; padding-right: 16px;">{{copago}}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="color: #475569; padding-left: 16px;">Estudios No Autorizados:</td>
                                        <td align="right" style="font-weight: 600; padding-right: 16px; color: #b91c1c;">{{estudios_no_autorizados_valor}}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #cbd5e1;">
                                        <td style="color: #475569; padding-left: 16px;">Acto Profesional Bioquímico (APB):</td>
                                        <td align="right" style="font-weight: 600; padding-right: 16px;">{{valor_apb}}</td>
                                    </tr>
                                    <tr style="background-color: #eff6ff;">
                                        <td style="color: #1e3a8a; font-weight: 700; font-size: 14.5px; padding-left: 16px;">TOTAL A ABONAR:</td>
                                        <td align="right" style="color: #1d4ed8; font-weight: 800; font-size: 17px; padding-right: 16px;">{{total_abonar}}</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Indicaciones de Preparación -->
                            <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 16px 20px; border-radius: 6px; margin: 24px 0;">
                                <h3 style="margin: 0 0 8px 0; color: #92400e; font-size: 15px; font-weight: 700;">
                                    📋 Indicaciones de Preparación para sus Estudios
                                </h3>
                                <div style="font-size: 13.5px; color: #78350f; line-height: 1.6;">
                                    {{indicaciones}}
                                </div>
                            </div>

                            <!-- Aviso de Comunicación Directa -->
                            <div style="background-color: #f1f5f9; border-radius: 8px; padding: 14px 18px; margin-top: 24px; font-size: 12.5px; color: #475569; line-height: 1.5;">
                                <strong>📞 Comunicación Directa:</strong> Personal de nuestro laboratorio se pondrá en contacto telefónico con usted para coordinar su turno de atención o resolver cualquier duda sobre su preparación.
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 24px; text-align: center; font-size: 11.5px; color: #64748b;">
                            <div>{{sucursal_nombre}} &bull; Laboratorio Bioquímico de Análisis Clínicos</div>
                            <div style="margin-top: 4px;">Este es un mensaje informativo generado por el Sistema de Gestión de Órdenes Médicas.</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
