import csv
import io
import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.dashboard.repository import DashboardRepository
from backend.app.modules.dashboard.schemas import (
    DashboardChartsResponse,
    DistribucionEstado,
    DistribucionMutual,
    DistribucionSucursal,
    KpiMetricsResponse,
    TendenciaTemporalItem,
)
from backend.app.modules.ordenes.models import EstadoOrden, OrdenMedica


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DashboardRepository(db)

    async def get_kpis(self, sucursal_id: Optional[uuid.UUID] = None) -> KpiMetricsResponse:
        counts = await self.repo.get_counts_by_estado(sucursal_id=sucursal_id)
        calls_counts = await self.repo.get_pending_calls_counts(sucursal_id=sucursal_id)
        total_copago = await self.repo.get_total_copago(sucursal_id=sucursal_id)

        total = sum(counts.values())
        cerradas = counts.get(EstadoOrden.CERRADA.value, 0)
        canceladas = counts.get(EstadoOrden.CANCELADA.value, 0)
        dadas_de_baja = counts.get(EstadoOrden.DAR_DE_BAJA.value, 0)

        finalizadas_terminal = cerradas + canceladas + dadas_de_baja
        activas = total - finalizadas_terminal

        total_resueltas = cerradas + canceladas + dadas_de_baja
        tasa_aprobacion = (
            round((cerradas / total_resueltas) * 100, 2) if total_resueltas > 0 else 100.0
        )

        return KpiMetricsResponse(
            total_ordenes=total,
            ordenes_activas=activas,
            ordenes_ingreso=counts.get(EstadoOrden.INGRESO.value, 0),
            ordenes_en_auditoria=counts.get(EstadoOrden.EN_AUDITORIA.value, 0),
            ordenes_con_solicitudes=counts.get(EstadoOrden.SOLICITUDES_AUDITORIA.value, 0),
            ordenes_actualizadas=counts.get(EstadoOrden.ACTUALIZADA.value, 0),
            ordenes_auditoria_finalizada=counts.get(EstadoOrden.AUDITORIA_FINALIZADA.value, 0),
            ordenes_dadas_de_baja=dadas_de_baja,
            ordenes_cerradas=cerradas,
            ordenes_canceladas=canceladas,
            tasa_aprobacion_porcentaje=tasa_aprobacion,
            llamadas_pendientes_total=calls_counts["total"],
            llamadas_pendientes_solicitud=calls_counts["solicitud"],
            llamadas_pendientes_finalizada=calls_counts["finalizada"],
            total_copago_recaudado=total_copago,
        )

    async def get_charts_data(
        self, sucursal_id: Optional[uuid.UUID] = None
    ) -> DashboardChartsResponse:
        # 1. Estados
        counts = await self.repo.get_counts_by_estado(sucursal_id=sucursal_id)
        total = sum(counts.values()) or 1
        dist_estados = [
            DistribucionEstado(
                estado=estado,
                cantidad=cant,
                porcentaje=round((cant / total) * 100, 2),
            )
            for estado, cant in counts.items()
        ]

        # 2. Sucursales
        suc_data = await self.repo.get_distribution_by_sucursal()
        dist_sucursales = [
            DistribucionSucursal(
                sucursal_nombre=row[0],
                sucursal_id=row[1],
                ordenes_abiertas=int(row[2] or 0),
                ordenes_cerradas=int(row[3] or 0),
                total_ordenes=int(row[4] or 0),
            )
            for row in suc_data
        ]

        # 3. Mutuales Top
        mutuales_data = await self.repo.get_top_mutuales(limit=5, sucursal_id=sucursal_id)
        dist_mutuales = [
            DistribucionMutual(
                mutual=row[0],
                cantidad_ordenes=int(row[1]),
                total_copago=Decimal(str(row[2])),
            )
            for row in mutuales_data
        ]

        # 4. Tendencias Temporales
        tendencias_data = await self.repo.get_tendencias_temporales(
            days=14, sucursal_id=sucursal_id
        )
        dist_tendencias = [
            TendenciaTemporalItem(
                periodo=row[0].strftime("%Y-%m-%d"),
                ingresadas=int(row[1]),
                finalizadas=int(row[2] or 0),
            )
            for row in tendencias_data
        ]

        return DashboardChartsResponse(
            estados=dist_estados,
            sucursales=dist_sucursales,
            mutuales_top=dist_mutuales,
            tendencias=dist_tendencias,
        )

    async def generate_csv_report(
        self,
        sucursal_id: Optional[uuid.UUID] = None,
        estado: Optional[str] = None,
        mutual: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> io.StringIO:
        """Genera un archivo CSV codificado para compatibilidad universal con Excel."""
        orders = await self.repo.get_orders_for_export(
            sucursal_id=sucursal_id,
            estado=estado,
            mutual=mutual,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        output = io.StringIO()
        # UTF-8 BOM para apertura directa en Microsoft Excel en español
        output.write("\ufeff")
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        # Encabezados
        writer.writerow([
            "Nro Orden",
            "Estado",
            "Paciente DNI",
            "Paciente Nombre",
            "Mutual / Cobertura",
            "Copago",
            "Estudios No Autorizados",
            "Abona APB",
            "Valor APB",
            "Total a Abonar",
            "Cant Recetas Fisicas",

            "Fecha Prescripcion",
            "Fecha Ingreso",
            "Sucursal",
            "Operador Ingreso",
            "Auditor Asignado",
            "Numeros Auditoria",
            "Aviso Solicitud Realizado",
            "Aviso Finalizada Realizado",
        ])

        for o in orders:
            cop = o.valor_copago or Decimal("0.00")
            no_aut = getattr(o, "valor_estudios_no_autorizados", Decimal("0.00")) or Decimal("0.00")
            apb = getattr(o, "valor_apb", Decimal("0.00")) or Decimal("0.00")
            total = cop + no_aut + apb
            writer.writerow([
                o.nro_orden,
                o.estado.value,
                o.paciente.documento if o.paciente else "",
                o.paciente.nombre_completo if o.paciente else "",
                o.mutual,
                str(cop),
                str(no_aut),
                "SI" if getattr(o, "abona_apb", False) else "NO",
                str(apb),
                str(total),
                o.cantidad_ordenes_fisicas,

                o.fecha_prescripcion.strftime("%Y-%m-%d"),
                o.created_at.strftime("%Y-%m-%d %H:%M"),
                o.sucursal.nombre if o.sucursal else "",
                o.created_by_user.full_name if o.created_by_user else "",
                o.assigned_auditor.full_name if o.assigned_auditor else "Sin asignar",
                ", ".join(o.numeros_auditoria) if o.numeros_auditoria else "",
                "SI" if o.llamada_solicitud_completada else "NO",
                "SI" if o.llamada_finalizada_completada else "NO",
            ])

        output.seek(0)
        return output

    async def generar_reporte_personalizado(
        self,
        request_dto: "ReporteConfigurableRequest",
        current_user: Any,
    ) -> "ReporteConfigurableResponse":
        from datetime import datetime
        from collections import defaultdict
        from backend.app.modules.dashboard.schemas import ReporteConfigurableResponse, ReporteFilaItem

        # 1. Obtener datos de órdenes filtrados
        orders = await self.repo.get_ordenes_para_reporte_personalizado(
            fecha_desde=request_dto.fecha_desde,
            fecha_hasta=request_dto.fecha_hasta,
            mutuales=request_dto.mutuales,
            sucursal_id=request_dto.sucursal_id,
            estado=request_dto.estado,
            solo_con_reintegro=request_dto.solo_con_reintegro or False,
        )

        preset = request_dto.preset or ""
        titulo = "Reporte Estadístico Personalizado"
        subtitulo = "Análisis multidimensional de órdenes médicas"

        if preset == "ordenes_tiempo":
            titulo = "Volumen de Órdenes por Obra Social vs. Tiempo"
            subtitulo = f"Evolución temporal agrupada por {request_dto.agrupacion_tiempo.upper()}"
        elif preset == "motivos_cancelacion":
            titulo = "Distribución de Motivos de Cancelación"
            subtitulo = "Desglose de órdenes canceladas y motivos aplicados"
        elif preset == "tasa_rechazo":
            titulo = "Tasa de Rechazo de Estudios por Obra Social"
            subtitulo = "Análisis comparativo de prácticas autorizadas vs. no autorizadas"
        elif preset == "financiero_reintegros":
            titulo = "Liquidación Financiera y Reintegros a Pacientes"
            subtitulo = "Copagos, APB, aranceles particulares y saldos de reintegros"

        # 2. Agrupación dinámica
        def extraer_clave(o: OrdenMedica, dim: str) -> tuple[str, str]:
            if dim == "mutual":
                val = o.mutual or "S/D"
                return val, val
            elif dim == "tiempo":
                f = o.fecha_prescripcion
                if not f and o.created_at:
                    f = o.created_at.date()
                if not f:
                    return "S/F", "Sin Fecha"
                if request_dto.agrupacion_tiempo == "dia":
                    c = f.strftime("%Y-%m-%d")
                    return c, f.strftime("%d/%m/%Y")
                elif request_dto.agrupacion_tiempo == "semana":
                    c = f"{f.year}-S{f.isocalendar()[1]:02d}"
                    return c, f"Semana {f.isocalendar()[1]} - {f.year}"
                elif request_dto.agrupacion_tiempo == "anio":
                    c = str(f.year)
                    return c, str(f.year)
                else:  # mes por defecto
                    c = f.strftime("%Y-%m")
                    meses = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    return c, f"{meses[f.month]} {f.year}"
            elif dim == "motivo_cancelacion":
                val = o.motivo_cancelacion or "Sin motivo especificado"
                return val, val
            elif dim == "sucursal":
                val = o.sucursal.nombre if o.sucursal else "Sede Central"
                return val, val
            elif dim == "estado":
                val = o.estado.value if hasattr(o.estado, "value") else str(o.estado)
                return val, val
            return "GENERAL", "General"

        grupos = defaultdict(lambda: {
            "clave_primaria": "",
            "etiqueta_primaria": "",
            "clave_secundaria": None,
            "etiqueta_secundaria": None,
            "total_ordenes": 0,
            "ordenes_aprobadas": 0,
            "ordenes_canceladas": 0,
            "ordenes_en_proceso": 0,
            "total_estudios_autorizados": 0,
            "total_estudios_rechazados": 0,
            "total_copago": Decimal("0.00"),
            "total_no_autorizados": Decimal("0.00"),
            "total_apb": Decimal("0.00"),
            "total_facturado_auditoria": Decimal("0.00"),
            "total_abonado_atencion": Decimal("0.00"),
            "total_reintegros_a_favor": Decimal("0.00"),
            "cant_pacientes_reintegro": 0,
        })

        resumen = {
            "total_ordenes": len(orders),
            "total_copago": Decimal("0.00"),
            "total_no_autorizados": Decimal("0.00"),
            "total_apb": Decimal("0.00"),
            "total_reintegros": Decimal("0.00"),
            "total_estudios_evaluados": 0,
            "total_estudios_rechazados": 0,
            "promedio_tasa_rechazo": 0.0,
        }

        for o in orders:
            k1, etiq1 = extraer_clave(o, request_dto.dimension_primaria)
            k2, etiq2 = (None, None)
            group_key = k1
            if request_dto.dimension_secundaria:
                k2, etiq2 = extraer_clave(o, request_dto.dimension_secundaria)
                group_key = f"{k1}___{k2}"

            g = grupos[group_key]
            g["clave_primaria"] = k1
            g["etiqueta_primaria"] = etiq1
            g["clave_secundaria"] = k2
            g["etiqueta_secundaria"] = etiq2
            g["total_ordenes"] += 1

            est_val = o.estado.value if hasattr(o.estado, "value") else str(o.estado)
            if est_val in ["Auditoria Finalizada", "Cerrada ok", "Cerrada"]:
                g["ordenes_aprobadas"] += 1
            elif est_val in ["Cancelada", "Dar de baja"]:
                g["ordenes_canceladas"] += 1
            else:
                g["ordenes_en_proceso"] += 1

            cant_aut = len(o.estudios_autorizados or [])
            cant_no_aut = len(o.estudios_no_autorizados or [])
            if o.estudios_detalle and isinstance(o.estudios_detalle, list):
                cant_aut = len([e for e in o.estudios_detalle if e.get("autorizado", True)])
                cant_no_aut = len([e for e in o.estudios_detalle if not e.get("autorizado", True)])

            g["total_estudios_autorizados"] += cant_aut
            g["total_estudios_rechazados"] += cant_no_aut
            resumen["total_estudios_evaluados"] += (cant_aut + cant_no_aut)
            resumen["total_estudios_rechazados"] += cant_no_aut

            copago = Decimal(str(o.valor_copago or 0))
            no_aut = Decimal(str(getattr(o, "valor_estudios_no_autorizados", 0) or 0))
            apb = Decimal(str(o.valor_apb if getattr(o, "abona_apb", False) else 0))
            costo_audit = copago + no_aut + apb

            g["total_copago"] += copago
            g["total_no_autorizados"] += no_aut
            g["total_apb"] += apb
            g["total_facturado_auditoria"] += costo_audit

            resumen["total_copago"] += copago
            resumen["total_no_autorizados"] += no_aut
            resumen["total_apb"] += apb

            if getattr(o, "ya_se_atendio", False):
                abonado = Decimal(str(getattr(o, "monto_abonado_atencion", 0) or 0))
                reintegro = abonado - costo_audit
                g["total_abonado_atencion"] += abonado
                if reintegro > Decimal("0.00"):
                    g["total_reintegros_a_favor"] += reintegro
                    g["cant_pacientes_reintegro"] += 1
                    resumen["total_reintegros"] += reintegro

        filas = []
        for g in grupos.values():
            total_est = g["total_estudios_autorizados"] + g["total_estudios_rechazados"]
            pct_rech = round((g["total_estudios_rechazados"] / total_est * 100), 2) if total_est > 0 else 0.0
            filas.append(ReporteFilaItem(
                clave_primaria=g["clave_primaria"],
                etiqueta_primaria=g["etiqueta_primaria"],
                clave_secundaria=g["clave_secundaria"],
                etiqueta_secundaria=g["etiqueta_secundaria"],
                total_ordenes=g["total_ordenes"],
                ordenes_aprobadas=g["ordenes_aprobadas"],
                ordenes_canceladas=g["ordenes_canceladas"],
                ordenes_en_proceso=g["ordenes_en_proceso"],
                total_estudios_evaluados=total_est,
                total_estudios_autorizados=g["total_estudios_autorizados"],
                total_estudios_rechazados=g["total_estudios_rechazados"],
                porcentaje_rechazo_estudios=pct_rech,
                total_copago=g["total_copago"],
                total_no_autorizados=g["total_no_autorizados"],
                total_apb=g["total_apb"],
                total_facturado_auditoria=g["total_facturado_auditoria"],
                total_abonado_atencion=g["total_abonado_atencion"],
                total_reintegros_a_favor=g["total_reintegros_a_favor"],
                cant_pacientes_reintegro=g["cant_pacientes_reintegro"],
            ))

        if request_dto.dimension_primaria == "tiempo":
            filas.sort(key=lambda x: x.clave_primaria)
        else:
            filas.sort(key=lambda x: x.total_ordenes, reverse=True)

        if resumen["total_estudios_evaluados"] > 0:
            resumen["promedio_tasa_rechazo"] = round(
                (resumen["total_estudios_rechazados"] / resumen["total_estudios_evaluados"] * 100), 2
            )

        grafico_labels = [f.etiqueta_primaria for f in filas[:15]]
        if preset == "tasa_rechazo":
            grafico_datasets = [{
                "label": "% Rechazo de Estudios",
                "data": [f.porcentaje_rechazo_estudios for f in filas[:15]],
                "backgroundColor": "rgba(239, 68, 68, 0.7)",
                "borderColor": "#ef4444",
            }]
        elif preset == "financiero_reintegros":
            grafico_datasets = [
                {"label": "Copago ($)", "data": [float(f.total_copago) for f in filas[:15]], "backgroundColor": "rgba(59, 130, 246, 0.7)"},
                {"label": "No Autorizados ($)", "data": [float(f.total_no_autorizados) for f in filas[:15]], "backgroundColor": "rgba(245, 158, 11, 0.7)"},
                {"label": "Reintegros Paciente ($)", "data": [float(f.total_reintegros_a_favor) for f in filas[:15]], "backgroundColor": "rgba(16, 185, 129, 0.7)"},
            ]
        else:
            grafico_datasets = [
                {"label": "Aprobadas", "data": [f.ordenes_aprobadas for f in filas[:15]], "backgroundColor": "#10b981"},
                {"label": "Canceladas", "data": [f.ordenes_canceladas for f in filas[:15]], "backgroundColor": "#ef4444"},
                {"label": "En Proceso", "data": [f.ordenes_en_proceso for f in filas[:15]], "backgroundColor": "#3b82f6"},
            ]

        resumen_serializable = {
            k: float(v) if isinstance(v, Decimal) else v for k, v in resumen.items()
        }

        return ReporteConfigurableResponse(
            titulo_reporte=titulo,
            subtitulo=subtitulo,
            periodo_desde=request_dto.fecha_desde.strftime("%d/%m/%Y") if request_dto.fecha_desde else None,
            periodo_hasta=request_dto.fecha_hasta.strftime("%d/%m/%Y") if request_dto.fecha_hasta else None,
            fecha_generacion=datetime.now().strftime("%d/%m/%Y %H:%M"),
            generado_por=current_user.full_name if hasattr(current_user, "full_name") else "Administrador",
            resumen_global=resumen_serializable,
            filas=filas,
            grafico_labels=grafico_labels,
            grafico_datasets=grafico_datasets,
        )
