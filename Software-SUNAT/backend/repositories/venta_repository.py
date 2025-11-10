from sqlalchemy.orm import Session
from sqlalchemy import func, desc, String
from typing import List, Optional, Dict, Any, Tuple
from datetime import date

from models import VentaElectronica, Enrolado, Usuario
from repositories.base_repository import BaseRepository


class VentaRepository(BaseRepository[VentaElectronica]):
    """Repositorio especializado para consultas de ventas"""

    def __init__(self, db: Session):
        super().__init__(VentaElectronica, db)

    def _aplicar_filtros_base(self, query):
        """Aplica filtros base: excluye boletas, notas de crédito y registros sin deudor válido"""
        return query.filter(
            ~VentaElectronica.serie_cdp.like("B%"),
            VentaElectronica.apellidos_nombres_razon_social != "-",
            VentaElectronica.apellidos_nombres_razon_social.isnot(None),
            VentaElectronica.tipo_cp_doc != '7'  # Excluir notas de crédito
        )

    def get_ventas_paginadas(
        self,
        page: int = 1,
        page_size: int = 20,
        ruc: Optional[str] = None,
        rucs_empresa: Optional[List[str]] = None,
        periodo: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        sort_by: str = "fecha",
        moneda: Optional[str] = None,
        authorized_rucs: Optional[List[str]] = None,
        usuario_emails: Optional[List[str]] = None,
    ) -> Tuple[List[Tuple[VentaElectronica, Optional[str], Optional[str], Optional[float]]], int]:
        """
        Obtiene ventas paginadas con filtros optimizados

        Args:
            ruc: Filtrar por un solo RUC
            rucs_empresa: Filtrar por múltiples RUCs (lista)
            sort_by: Campo por el cual ordenar. Opciones: "fecha" (por defecto), "monto"
            moneda: Filtrar por moneda. Opciones: "PEN", "USD", o None para todas
            authorized_rucs: Lista de RUCs autorizados para el usuario (control de acceso)
            usuario_emails: Filtrar por lista de emails de usuario (opcional). Acepta "UNASSIGNED" para sin asignar.

        Returns:
            tuple: (list of (venta, usuario_nombre, usuario_email, nota_credito_monto), total_count)
        """
        from sqlalchemy import func as sql_func, case

        # Subquery para notas de crédito: agrupa por factura original y suma los montos
        # nota_credito_monto será NEGATIVO (porque las NC restan del monto original)
        # Las NC en SUNAT tienen total_cp positivo, así que negamos el valor
        nc_subquery = self.db.query(
            VentaElectronica.ruc.label('nc_ruc'),
            sql_func.regexp_replace(
                sql_func.cast(VentaElectronica.nro_cp_modificado, String),
                r'\.0$',
                ''
            ).label('nc_nro_modificado'),
            VentaElectronica.nro_doc_identidad.label('nc_nro_doc'),
            sql_func.sum(
                case(
                    (VentaElectronica.tipo_cambio > 0, VentaElectronica.total_cp / VentaElectronica.tipo_cambio),  # Negativo
                    else_=VentaElectronica.total_cp  # Negativo
                )
            ).label('nc_total')
        ).filter(
            VentaElectronica.tipo_cp_doc == '7'  # Solo notas de crédito
        ).group_by(
            'nc_ruc',
            'nc_nro_modificado',
            'nc_nro_doc'
        ).subquery()

        # Query principal con LEFT JOIN a Enrolado, Usuario y notas de crédito
        query = self.db.query(
            VentaElectronica,
            Usuario.nombre.label('usuario_nombre'),
            Usuario.email.label('usuario_email'),
            nc_subquery.c.nc_total.label('nota_credito_monto')
        ).outerjoin(
            Enrolado, VentaElectronica.ruc == Enrolado.ruc
        ).outerjoin(
            Usuario, Enrolado.email == Usuario.email
        ).outerjoin(
            nc_subquery,
            (VentaElectronica.ruc == nc_subquery.c.nc_ruc) &
            (VentaElectronica.nro_cp_inicial == nc_subquery.c.nc_nro_modificado) &
            (VentaElectronica.nro_doc_identidad == nc_subquery.c.nc_nro_doc)
        )

        # Aplicar filtros base solo a VentaElectronica
        query = query.filter(
            ~VentaElectronica.serie_cdp.like("B%"),
            VentaElectronica.apellidos_nombres_razon_social != "-",
            VentaElectronica.apellidos_nombres_razon_social.isnot(None),
            VentaElectronica.tipo_cp_doc != '7'  # Excluir notas de crédito
        )

        # CONTROL DE ACCESO: Filtrar por RUCs autorizados
        if authorized_rucs is not None:
            if len(authorized_rucs) == 0:
                # Usuario sin RUCs autorizados, retornar vacío
                return [], 0
            query = query.filter(VentaElectronica.ruc.in_(authorized_rucs))

        # Aplicar filtros
        if ruc:
            query = query.filter(VentaElectronica.ruc == ruc)
        elif rucs_empresa and len(rucs_empresa) > 0:
            query = query.filter(VentaElectronica.ruc.in_(rucs_empresa))

        if periodo:
            query = query.filter(VentaElectronica.periodo == periodo)

        if fecha_desde:
            query = query.filter(VentaElectronica.fecha_emision >= fecha_desde)

        if fecha_hasta:
            query = query.filter(VentaElectronica.fecha_emision <= fecha_hasta)

        if moneda:
            query = query.filter(VentaElectronica.moneda == moneda)

        # Filtrar por usuario_emails si se proporciona
        if usuario_emails and len(usuario_emails) > 0:
            from sqlalchemy import or_

            print(f"🔍 [BACKEND] Filtrando por usuario_emails: {usuario_emails}")

            # Separar "UNASSIGNED" de emails normales
            has_unassigned = "UNASSIGNED" in usuario_emails
            normal_emails = [email for email in usuario_emails if email != "UNASSIGNED"]

            print(f"🔍 [BACKEND] has_unassigned={has_unassigned}, normal_emails={normal_emails}")

            # Construir condiciones
            conditions = []
            if has_unassigned:
                # Agregar condición para facturas sin usuario asignado
                conditions.append(Usuario.email.is_(None))
                print("✅ [BACKEND] Agregada condición: Usuario.email IS NULL")
            if normal_emails:
                # Agregar condición para emails específicos
                conditions.append(Usuario.email.in_(normal_emails))
                print(f"✅ [BACKEND] Agregada condición: Usuario.email IN {normal_emails}")

            # Aplicar filtro con OR entre condiciones
            if conditions:
                print("🎯 [BACKEND] Aplicando {len(conditions)} condición(es) de usuario")
                query = query.filter(or_(*conditions))
            else:
                print("⚠️ [BACKEND] NO se construyeron condiciones de filtro")
        else:
            print("⚠️ [BACKEND] NO se recibieron usuario_emails o está vacío")

        # Aplicar ordenamiento según el parámetro
        if sort_by == "monto":
            query = query.order_by(desc(VentaElectronica.total_cp))
        else:  # Por defecto: fecha
            query = query.order_by(desc(VentaElectronica.fecha_emision))

        # Contar total
        total = query.count()
        print(f"📊 [BACKEND] Total de facturas encontradas (después de filtros): {total}")

        # Aplicar paginación
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()
        print(f"📊 [BACKEND] Facturas en esta página: {len(results)}")

        # Retornar tuplas (venta, usuario_nombre, usuario_email, nota_credito_monto)
        items = [(venta, usuario_nombre, usuario_email, nota_credito_monto)
                 for venta, usuario_nombre, usuario_email, nota_credito_monto in results]

        # DEBUG: Mostrar emails y notas de crédito de las primeras 3 facturas
        if len(items) > 0:
            sample = items[:3]
            print("🔍 [BACKEND] Muestra de emails y notas de crédito en resultados:")
            for venta, usuario_nombre, usuario_email, nc_monto in sample:
                print(f"  - {venta.ruc}: usuario_email={usuario_email}, usuario_nombre={usuario_nombre}, nc_monto={nc_monto}")

        return items, total

    def get_ventas_con_enrolados(
        self, periodo: Optional[str] = None, page: int = 1, page_size: int = 20
    ):
        """
        Obtiene ventas con información de enrolados usando JOIN optimizado
        Evita el problema N+1

        Returns:
            tuple: (results, total_count)
        """
        # Query optimizado con JOIN
        query = self.db.query(VentaElectronica, Enrolado).join(
            Enrolado, VentaElectronica.ruc == Enrolado.ruc
        )

        # Filtrar por periodo si se especifica
        if periodo:
            query = query.filter(VentaElectronica.periodo == periodo)

        # Ordenar por fecha de emisión descendente
        query = query.order_by(desc(VentaElectronica.fecha_emision))

        # Contar total
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        return results, total

    def get_metricas_periodo(
        self, periodo: str, ruc: Optional[str] = None, authorized_rucs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calcula métricas separadas por moneda usando agrupación SQL

        Args:
            periodo: Periodo a consultar (YYYYMM)
            ruc: RUC específico (opcional)
            authorized_rucs: Lista de RUCs autorizados para el usuario (control de acceso)
        """
        query = self.db.query(
            VentaElectronica.moneda,
            func.sum(VentaElectronica.total_cp).label("total"),
            func.count(VentaElectronica.id).label("cantidad"),
        ).filter(VentaElectronica.periodo == periodo)

        query = self._aplicar_filtros_base(query)

        # CONTROL DE ACCESO: Filtrar por RUCs autorizados
        if authorized_rucs is not None:
            if len(authorized_rucs) == 0:
                # Usuario sin RUCs autorizados, retornar métricas vacías
                return {
                    "periodo": periodo,
                    "total_pen": 0,
                    "facturas_pen": 0,
                    "total_usd": 0,
                    "facturas_usd": 0,
                }
            query = query.filter(VentaElectronica.ruc.in_(authorized_rucs))

        if ruc:
            query = query.filter(VentaElectronica.ruc == ruc)

        # Agrupar por moneda
        results = query.group_by(VentaElectronica.moneda).all()

        # Inicializar valores por defecto
        total_pen = 0
        facturas_pen = 0
        total_usd = 0
        facturas_usd = 0

        # Procesar resultados
        for moneda, total, cantidad in results:
            if moneda == "PEN":
                total_pen = float(total) if total else 0
                facturas_pen = int(cantidad) if cantidad else 0
            elif moneda == "USD":
                total_usd = float(total) if total else 0
                facturas_usd = int(cantidad) if cantidad else 0

        return {
            "periodo": periodo,
            "total_pen": total_pen,
            "facturas_pen": facturas_pen,
            "total_usd": total_usd,
            "facturas_usd": facturas_usd,
        }

    def get_ventas_por_enrolado(
        self,
        ruc_enrolado: str,
        periodo: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        """Obtiene ventas de un enrolado específico con paginación"""
        query = self.db.query(VentaElectronica).filter(
            VentaElectronica.ruc == ruc_enrolado
        )

        if periodo:
            query = query.filter(VentaElectronica.periodo == periodo)

        query = query.order_by(desc(VentaElectronica.fecha_emision))

        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_clientes_con_facturas_optimizado(
        self, periodo: Optional[str] = None, sort_by: str = "fecha", authorized_rucs: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Versión optimizada que usa una sola query con agrupación
        Agrupa ventas por enrolado de forma eficiente

        Args:
            sort_by: Campo por el cual ordenar. Opciones: "fecha" (por defecto), "monto"
            authorized_rucs: Lista de RUCs autorizados para el usuario (control de acceso)
        """

        # Query principal con joinedload para evitar N+1
        query = self.db.query(Enrolado)

        # CONTROL DE ACCESO: Filtrar enrolados por RUCs autorizados
        if authorized_rucs is not None:
            if len(authorized_rucs) == 0:
                # Usuario sin RUCs autorizados, retornar lista vacía
                return []
            query = query.filter(Enrolado.ruc.in_(authorized_rucs))

        enrolados = query.all()
        result = []

        for enrolado in enrolados:
            # Subquery optimizada para ventas del enrolado
            ventas_query = self.db.query(VentaElectronica).filter(
                VentaElectronica.ruc == enrolado.ruc
            )

            if periodo:
                ventas_query = ventas_query.filter(VentaElectronica.periodo == periodo)

            ventas_query = self._aplicar_filtros_base(ventas_query)

            # Aplicar ordenamiento
            if sort_by == "monto":
                ventas = ventas_query.order_by(
                    desc(VentaElectronica.total_cp)
                ).all()
            else:  # Por defecto: fecha
                ventas = ventas_query.order_by(
                    desc(VentaElectronica.fecha_emision)
                ).all()

            # Transformar al formato esperado
            facturas = []
            for venta in ventas:
                factura = {
                    "id": f"{venta.serie_cdp}-{venta.nro_cp_inicial}"
                    if venta.serie_cdp and venta.nro_cp_inicial
                    else f"V-{venta.id}",
                    "debtor": venta.apellidos_nombres_razon_social or "Sin nombre",
                    "amount": float(venta.total_cp)
                    if venta.total_cp
                    else 0.0,
                    "emissionDate": venta.fecha_emision.strftime("%Y-%m-%d")
                    if venta.fecha_emision
                    else None,
                    "dueDate": None,
                    "status": "Sin Gestión",
                    "log": [],
                    "ruc_cliente": venta.nro_doc_identidad,
                    "tipo_comprobante": venta.tipo_cp_doc,
                    "moneda": venta.moneda,
                    "car_sunat": venta.car_sunat,
                }
                facturas.append(factura)

            cliente = {
                "id": enrolado.id,
                "name": enrolado.ruc,
                "ruc": enrolado.ruc,
                "availableInvoices": facturas,
            }
            result.append(cliente)

        return result

    def get_empresas_unicas_por_periodo(
        self,
        periodo: Optional[str] = None,
        authorized_rucs: Optional[List[str]] = None,
        usuario_emails: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Obtiene lista de empresas únicas (RUC y razón social) de todos los períodos o uno específico
        Usado para llenar el selector de clientes en el frontend

        Args:
            periodo: Periodo a consultar (YYYYMM). Si es None, retorna todas las empresas de todos los períodos
            authorized_rucs: Lista de RUCs autorizados para el usuario (control de acceso)
            usuario_emails: Filtrar empresas por usuarios asignados (opcional). Acepta "UNASSIGNED" para empresas sin usuario.
        """
        from sqlalchemy import func as sql_func, or_

        # Si se filtran usuarios, hacer JOIN con Enrolado y Usuario
        if usuario_emails and len(usuario_emails) > 0:
            # Separar "UNASSIGNED" de emails normales
            has_unassigned = "UNASSIGNED" in usuario_emails
            normal_emails = [email for email in usuario_emails if email != "UNASSIGNED"]

            # Query con JOINs para filtrar por usuario
            query = self.db.query(
                VentaElectronica.ruc,
                sql_func.max(VentaElectronica.razon_social).label('razon_social')
            ).outerjoin(
                Enrolado, VentaElectronica.ruc == Enrolado.ruc
            ).outerjoin(
                Usuario, Enrolado.email == Usuario.email
            ).filter(
                VentaElectronica.razon_social.isnot(None),
                VentaElectronica.razon_social != '',
                VentaElectronica.razon_social != '-'
            )

            # Construir condiciones de filtro de usuario
            conditions = []
            if has_unassigned:
                conditions.append(Usuario.email.is_(None))
            if normal_emails:
                conditions.append(Usuario.email.in_(normal_emails))

            if conditions:
                query = query.filter(or_(*conditions))
        else:
            # Query simplificada sin JOIN (comportamiento original)
            query = self.db.query(
                VentaElectronica.ruc,
                sql_func.max(VentaElectronica.razon_social).label('razon_social')
            ).filter(
                VentaElectronica.razon_social.isnot(None),
                VentaElectronica.razon_social != '',
                VentaElectronica.razon_social != '-'
            )

        # Filtrar por período solo si se especifica
        if periodo:
            query = query.filter(VentaElectronica.periodo == periodo)

        # CONTROL DE ACCESO: Filtrar por RUCs autorizados
        if authorized_rucs is not None:
            if len(authorized_rucs) == 0:
                # Usuario sin RUCs autorizados, retornar lista vacía
                return []
            query = query.filter(VentaElectronica.ruc.in_(authorized_rucs))

        # Agrupar por RUC
        query = query.group_by(VentaElectronica.ruc)

        empresas = query.all()

        return [
            {"ruc": ruc, "razon_social": razon_social or ruc}
            for ruc, razon_social in empresas
        ]
