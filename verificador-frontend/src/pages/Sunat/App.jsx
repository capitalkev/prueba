import React, { useState, useMemo, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { signOut } from 'firebase/auth';
import { auth } from '../../firebase';
import LoginPage from '../LoginPage';

// Componentes
import MultiClientSelector from './components/MultiClientSelector';
import MultiCurrencySelector from './components/MultiCurrencySelector';
import MultiUserSelector from './components/MultiUserSelector';
import KPIDashboard from './components/KPIDashboard';
import PeriodSelector from './components/PeriodSelector';
import BulkActionToolbar from './components/BulkActionToolbar';
import InvoiceTable from './components/InvoiceTable';
import GroupedInvoiceTable from './components/GroupedInvoiceTable';
import LastUpdateIndicator from './components/LastUpdateIndicator';

// Hooks personalizados
import { useClients } from './hooks/useClients';
import { useUsers } from './hooks/useUsers';
import { useSunatData } from './hooks/useSunatData';

// Iconos
import { ViewListIcon, ViewGridIcon } from './icons';

// Constantes
import { API_BASE_URL } from './constants';

/**
 * Aplicación principal del módulo SUNAT
 * Gestiona la visualización de facturas de ventas con filtros y métricas
 */
export default function App() {
    const { firebaseUser, loading: authLoading, authError } = useAuth();

    // Estados de UI
    const [selectedClientIds, setSelectedClientIds] = useState([]);
    const [selectedCurrencies, setSelectedCurrencies] = useState([]);
    const [selectedUserEmails, setSelectedUserEmails] = useState([]);
    const [expandedGroupKey, setExpandedGroupKey] = useState(null);
    const [dateFilter, setDateFilter] = useState({ type: 'thisMonth' });
    const [viewMode, setViewMode] = useState('grouped');
    const [selectedInvoiceKeys, setSelectedInvoiceKeys] = useState([]);
    const [invoiceStatuses, setInvoiceStatuses] = useState({});
    const [sortBy, setSortBy] = useState('fecha');
    const [currentPage, setCurrentPage] = useState(1);

    // Cargar usuarios (no-admin) - debe ir primero
    const { users, errorData: usersError } = useUsers(firebaseUser);

    // Cargar clientes (de todos los períodos, filtrado por usuarios seleccionados)
    const { clients, errorData: clientsError } = useClients(firebaseUser, selectedUserEmails, users);

    // DEBUG: Rastrear cambios en selectedUserEmails
    useEffect(() => {
        console.log('🔍 [App DEBUG] selectedUserEmails cambió:', {
            selectedUserEmails,
            count: selectedUserEmails.length,
            is_array: Array.isArray(selectedUserEmails)
        });
    }, [selectedUserEmails]);

    // Limpiar clientes seleccionados si ya no están en la lista de clientes disponibles
    // Solo se ejecuta cuando cambia la lista de clientes (no cuando cambian los seleccionados)
    useEffect(() => {
        if (clients.length > 0 && selectedClientIds.length > 0) {
            const availableClientIds = new Set(clients.map(c => c.ruc));
            const validSelectedIds = selectedClientIds.filter(id => availableClientIds.has(id));

            // Si algún cliente seleccionado ya no está disponible, actualizar la selección
            if (validSelectedIds.length !== selectedClientIds.length) {
                setSelectedClientIds(validSelectedIds);
            }
        }
    }, [clients]); // Removido selectedClientIds de dependencias para evitar loop infinito

    // Cargar datos de ventas y métricas
    const {
        ventas,
        allInvoicesForMetrics,
        pagination,
        loading,
        error,
        errorData,
        periodLabel
    } = useSunatData(
        firebaseUser,
        dateFilter,
        selectedClientIds,
        selectedCurrencies,
        selectedUserEmails,
        currentPage,
        sortBy,
        clients,
        users,
        viewMode
    );

    // Función para formatear fecha de YYYY-MM-DD a DD-MM-YYYY
    const formatDateToDMY = (dateString) => {
        if (!dateString) return '';
        const parts = dateString.split('-');
        if (parts.length === 3) {
            return `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
        return dateString;
    };

    // Transformar ventas a invoices (para la tabla paginada)
    const invoices = useMemo(() => {
        const transformed = ventas.map(venta => {
            const invoiceId = `${venta.serie_cdp || ''}-${venta.nro_cp_inicial || venta.id}`;
            const clientId = venta.ruc;
            const statusKey = `${clientId}-${invoiceId}`;

            let amount = 0;
            if (venta.monto_original !== undefined && venta.monto_original !== null) {
                amount = parseFloat(venta.monto_original);
            } else if (venta.total_cp && venta.tipo_cambio && venta.tipo_cambio > 0) {
                amount = parseFloat(venta.total_cp) / parseFloat(venta.tipo_cambio);
            } else {
                amount = parseFloat(venta.total_cp) || 0;
            }

            // Información de notas de crédito
            const notaCreditoMonto = venta.nota_credito_monto ? parseFloat(venta.nota_credito_monto) : null;
            const montoNeto = venta.monto_neto !== undefined && venta.monto_neto !== null ? parseFloat(venta.monto_neto) : amount;
            const tieneNotaCredito = venta.tiene_nota_credito || false;

            return {
                id: invoiceId,
                ventaId: venta.id, // ID de la base de datos para actualizar estado
                clientId: clientId,
                clientName: venta.razon_social || venta.ruc,
                debtor: venta.apellidos_nombres_razon_social || 'Sin nombre',
                amount: amount,
                emissionDate: formatDateToDMY(venta.fecha_emision),
                currency: venta.moneda,
                status: invoiceStatuses[statusKey] || venta.estado1 || 'Sin gestión',
                estado2: venta.estado2 || null,
                key: statusKey,
                usuario: venta.usuario_nombre || 'Sin asignar',
                // Información de notas de crédito
                notaCreditoMonto: notaCreditoMonto,
                montoNeto: montoNeto,
                tieneNotaCredito: tieneNotaCredito
            };
        });
        console.log('🔄 [App] Transformed invoices:', transformed.length);
        return transformed;
    }, [ventas, invoiceStatuses]);

    // Transformar TODAS las facturas del período para métricas
    const allInvoicesTransformed = useMemo(() => {
        return allInvoicesForMetrics.map(venta => {
            const invoiceId = `${venta.serie_cdp || ''}-${venta.nro_cp_inicial || venta.id}`;
            const clientId = venta.ruc;
            const statusKey = `${clientId}-${invoiceId}`;

            let amount = 0;
            if (venta.monto_original !== undefined && venta.monto_original !== null) {
                amount = parseFloat(venta.monto_original);
            } else if (venta.total_cp && venta.tipo_cambio && venta.tipo_cambio > 0) {
                amount = parseFloat(venta.total_cp) / parseFloat(venta.tipo_cambio);
            } else {
                amount = parseFloat(venta.total_cp) || 0;
            }

            // Usar montoNeto si está disponible (para métricas correctas con notas de crédito)
            const montoNeto = venta.monto_neto !== undefined && venta.monto_neto !== null ? parseFloat(venta.monto_neto) : amount;

            return {
                amount: montoNeto, // Usar monto neto para métricas
                currency: venta.moneda,
                status: invoiceStatuses[statusKey] || venta.estado1 || 'Sin gestión',
            };
        });
    }, [allInvoicesForMetrics, invoiceStatuses]);

    // Calcular métricas usando TODAS las facturas del período
    const monthlyMetrics = useMemo(() => {
        const metrics = { PEN: {}, USD: {} };
        ['PEN', 'USD'].forEach(currency => {
            const ccyInvoices = allInvoicesTransformed.filter(inv => inv.currency === currency);
            const totalFacturado = ccyInvoices.reduce((s, i) => s + i.amount, 0);
            const montoGanado = ccyInvoices.filter(i => i.status === 'Ganada').reduce((s, i) => s + i.amount, 0);
            // Monto disponible excluye "Ganada" y "Perdida"
            const montoDisponible = ccyInvoices.filter(i => i.status !== 'Perdida' && i.status !== 'Ganada').reduce((s, i) => s + i.amount, 0);
            metrics[currency] = {
                totalFacturado,
                montoGanado,
                montoDisponible,
                winPercentage: totalFacturado > 0 ? (montoGanado / totalFacturado) * 100 : 0
            };
        });
        return metrics;
    }, [allInvoicesTransformed]);

    // Agrupar facturas (solo las de la página actual)
    const groupedInvoices = useMemo(() => {
        const groups = invoices.reduce((acc, inv) => {
            const key = `${inv.clientId}-${inv.debtor}-${inv.currency}`;
            if (!acc[key]) {
                acc[key] = {
                    key,
                    clientName: inv.clientName,
                    debtor: inv.debtor,
                    currency: inv.currency,
                    invoiceCount: 0,
                    totalAmount: 0,
                    invoices: []
                };
            }
            acc[key].invoiceCount++;
            // Usar montoNeto en lugar de amount para el total
            acc[key].totalAmount += inv.montoNeto;
            acc[key].invoices.push(inv);
            return acc;
        }, {});

        const groupedArray = Object.values(groups);
        console.log('📦 [App] Grouping:', {
            invoices_count: invoices.length,
            groups_count: groupedArray.length,
            groups: groupedArray.map(g => ({ key: g.key, invoiceCount: g.invoiceCount }))
        });
        return groupedArray;
    }, [invoices]);

    // Handlers
    const handleStatusChange = async (ventaId, clientId, invoiceId, newStatus, lossReason = null) => {
        const statusKey = `${clientId}-${invoiceId}`;

        try {
            // Obtener token de Firebase
            const token = await firebaseUser.getIdToken();

            // Si el estado es "Perdida" y se proporciona un motivo, usar el endpoint especial
            if (newStatus === 'Perdida' && lossReason) {
                const response = await fetch(`${API_BASE_URL}/api/ventas/${ventaId}/perdida`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ estado2: lossReason })
                });

                if (!response.ok) {
                    throw new Error(`Error al actualizar estado: ${response.status}`);
                }
            } else {
                // Para otros estados, usar el endpoint general
                const response = await fetch(`${API_BASE_URL}/api/ventas/${ventaId}/estado`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ estado1: newStatus })
                });

                if (!response.ok) {
                    throw new Error(`Error al actualizar estado: ${response.status}`);
                }
            }

            // Actualizar estado local si la petición fue exitosa
            setInvoiceStatuses(prev => ({
                ...prev,
                [statusKey]: newStatus
            }));
        } catch (error) {
            console.error('Error al actualizar estado:', error);
            alert(`Error al actualizar estado: ${error.message}`);
        }
    };

    const handleBulkStatusUpdate = (newStatus) => {
        setInvoiceStatuses(prev => {
            const updated = { ...prev };
            selectedInvoiceKeys.forEach(key => {
                updated[key] = newStatus;
            });
            return updated;
        });
        setSelectedInvoiceKeys([]);
    };

    const toggleInvoiceSelection = (key) => {
        setSelectedInvoiceKeys(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
    };

    const handleSortChange = (newSortBy) => {
        setSortBy(newSortBy);
        setCurrentPage(1);
    };

    const handleCurrencyChange = (newCurrencies) => {
        setSelectedCurrencies(newCurrencies);
        setCurrentPage(1);
    };

    const ViewModeButton = ({ label, value, icon }) => (
        <button
            onClick={() => { setViewMode(value); setSelectedInvoiceKeys([]); }}
            className={`flex items-center gap-2 px-3 py-1 text-sm rounded-full ${viewMode === value ? 'bg-blue-600 text-white font-semibold' : 'bg-white text-gray-600 hover:bg-gray-200'}`}
        >
            {icon} {label}
        </button>
    );

    // Loading y error states
    if (authLoading) {
        return (
            <div className="bg-gray-100 font-sans h-screen w-full flex items-center justify-center">
                <p>Verificando sesión...</p>
            </div>
        );
    }

    if (!firebaseUser) {
        return <LoginPage />;
    }

    if (authError) {
        return (
            <div className="bg-gray-100 font-sans h-screen w-full flex items-center justify-center">
                <div className="text-center bg-white p-8 rounded-lg shadow-md">
                    <h2 className="text-xl font-bold text-red-600 mb-2">Error de Autenticación</h2>
                    <p className="text-gray-600 mb-4">{authError}</p>
                    <button onClick={async () => await signOut(auth)} className="mt-4 bg-red-600 text-white px-6 py-2 rounded-md hover:bg-red-700">Cerrar Sesión</button>
                </div>
            </div>
        );
    }

    if ((errorData || clientsError) && ventas.length === 0) {
        return (
            <div className="bg-gray-100 font-sans h-screen w-full flex items-center justify-center">
                <div className="text-center bg-white p-8 rounded-lg shadow-md">
                    <h2 className="text-xl font-bold text-red-600 mb-2">Error al Cargar Datos</h2>
                    <p className="text-gray-600 mb-4">{errorData || clientsError}</p>
                    <button onClick={() => window.location.reload()} className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700">Reintentar</button>
                    <button onClick={async () => await signOut(auth)} className="mt-2 ml-2 text-sm text-gray-600 hover:underline">Cerrar Sesión</button>
                </div>
            </div>
        );
    }

    if (loading && ventas.length === 0) {
        return (
            <div className="bg-gray-100 font-sans h-screen w-full flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Cargando datos...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-gray-100 font-sans h-screen w-full flex items-center justify-center">
                <div className="text-center bg-white p-8 rounded-lg shadow-md">
                    <div className="text-red-500 text-5xl mb-4">⚠️</div>
                    <h2 className="text-xl font-bold text-gray-800 mb-2">Error al cargar datos</h2>
                    <p className="text-gray-600 mb-4">{error}</p>
                    <button onClick={() => window.location.reload()} className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700">Reintentar</button>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gray-100 font-sans h-screen w-full flex flex-col p-4 gap-4">
            <header className="flex-shrink-0 flex flex-col md:flex-row gap-3">
                <MultiClientSelector
                    clients={clients}
                    selectedClientIds={selectedClientIds}
                    onSelectionChange={(newIds) => {
                        setSelectedClientIds(newIds);
                        setCurrentPage(1);
                    }}
                />
                <MultiCurrencySelector
                    selectedCurrencies={selectedCurrencies}
                    onSelectionChange={handleCurrencyChange}
                />
                <MultiUserSelector
                    users={users}
                    selectedUserEmails={selectedUserEmails}
                    onSelectionChange={(newEmails) => {
                        console.log('👤 [App] Usuario seleccionado:', {
                            newEmails,
                            count: newEmails.length,
                            users_loaded: users.length
                        });
                        setSelectedUserEmails(newEmails);
                        setCurrentPage(1);
                    }}
                />
            </header>

            <div className="flex-shrink-0">
                <KPIDashboard metrics={monthlyMetrics} periodLabel={periodLabel} />
            </div>

            <main className="flex-grow bg-white rounded-lg border border-gray-200 shadow-sm overflow-y-auto flex flex-col relative">
                <div className="p-4 border-b flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                        <ViewModeButton label="Agrupada" value="grouped" icon={<ViewGridIcon />} />
                        <ViewModeButton label="Detallada" value="detailed" icon={<ViewListIcon />} />
                    </div>
                    <div className="flex items-center gap-3">
                        <LastUpdateIndicator firebaseUser={firebaseUser} />
                        <PeriodSelector filter={dateFilter} onFilterChange={(newFilter) => {
                            setDateFilter(newFilter);
                            setCurrentPage(1);
                        }} />
                    </div>
                </div>

                <div className="flex-grow overflow-x-auto">
                    {viewMode === 'grouped' ? (
                        <GroupedInvoiceTable
                            groupedInvoices={groupedInvoices}
                            expandedGroupKey={expandedGroupKey}
                            onExpandGroup={setExpandedGroupKey}
                            selectedInvoiceKeys={selectedInvoiceKeys}
                            onGroupSelection={setSelectedInvoiceKeys}
                            onInvoiceSelection={toggleInvoiceSelection}
                            onStatusChange={handleStatusChange}
                        />
                    ) : (
                        <InvoiceTable
                            invoices={invoices}
                            selectedInvoiceKeys={selectedInvoiceKeys}
                            onToggleSelection={toggleInvoiceSelection}
                            onSelectAll={(checked) => setSelectedInvoiceKeys(checked ? invoices.map(i => i.key) : [])}
                            onStatusChange={handleStatusChange}
                            sortBy={sortBy}
                            onSortChange={handleSortChange}
                        />
                    )}
                </div>

                {/* Paginación */}
                <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                        Página {pagination.page} de {pagination.total_pages} ({pagination.total_items} facturas)
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                            disabled={!pagination.has_previous}
                            className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Anterior
                        </button>
                        <button
                            onClick={() => setCurrentPage(prev => prev + 1)}
                            disabled={!pagination.has_next}
                            className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Siguiente
                        </button>
                    </div>
                </div>

                {selectedInvoiceKeys.length > 0 && (
                    <BulkActionToolbar
                        selectedCount={selectedInvoiceKeys.length}
                        onBulkUpdate={handleBulkStatusUpdate}
                        onClear={() => setSelectedInvoiceKeys([])}
                    />
                )}
            </main>
        </div>
    );
}
