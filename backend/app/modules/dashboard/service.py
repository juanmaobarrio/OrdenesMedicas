import csv
import io
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional
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
from backend.app.modules.ordenes.models import EstadoOrden


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

