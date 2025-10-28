import React, { useState, useMemo, useEffect, useRef } from 'react';
import { API_BASE_URL, STATUS_COLORS, INVOICE_STATUSES } from './constants';
import { formatCurrency, formatPeriodDisplay } from './utils/formatters';

// --- Iconos SVG ---
const BuildingOfficeIcon = ({ className = "w-6 h-6" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6h1.5m-1.5 3h1.5m-1.5 3h1.5M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M12.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21" /></svg>;
const ChevronDownIcon = ({ className = "w-5 h-5" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>;
const ChevronRightIcon = ({ className = "w-4 h-4" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>;
const CalendarDaysIcon = ({ className = "w-5 h-5" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0h18M-4.5 12h22.5" /></svg>;
const ViewListIcon = ({ className = "w-5 h-5" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" /></svg>;
const ViewGridIcon = ({ className = "w-5 h-5" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 8.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25v2.25A2.25 2.25 0 018.25 21H6a2.25 2.25 0 01-2.25-2.25v-2.25zM13.5 6A2.25 2.25 0 0115.75 3.75h2.25A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25A2.25 2.25 0 0113.5 8.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25h2.25a2.25 2.25 0 012.25 2.25v2.25a2.25 2.25 0 01-2.25 2.25h-2.25a2.25 2.25 0 01-2.25-2.25v-2.25z" /></svg>;
const ArrowsUpDownIcon = ({ className = "w-4 h-4" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M3 7.5L7.5 3m0 0L12 7.5M7.5 3v13.5m13.5 0L16.5 21m0 0L12 16.5m4.5 4.5V7.5" /></svg>;

// --- Componente Desplegable Multi-Selección de Clientes ---
const MultiClientSelector = ({ clients, selectedClientIds, onSelectionChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);
    useEffect(() => { const handleClickOutside = (event) => { if (dropdownRef.current && !dropdownRef.current.contains(event.target)) setIsOpen(false); }; document.addEventListener("mousedown", handleClickOutside); return () => document.removeEventListener("mousedown", handleClickOutside); }, []);
    const handleClientToggle = (clientId) => { const newSelection = selectedClientIds.includes(clientId) ? selectedClientIds.filter(id => id !== clientId) : [...selectedClientIds, clientId]; onSelectionChange(newSelection); };
    const getButtonLabel = () => { if (selectedClientIds.length === 0 || selectedClientIds.length === clients.length) return "Todos los clientes"; if (selectedClientIds.length === 1) return clients.find(c => c.id === selectedClientIds[0])?.name; return `${selectedClientIds.length} clientes seleccionados`; };
    return (
      <div className="relative w-full md:w-96" ref={dropdownRef}>
          <button onClick={() => setIsOpen(!isOpen)} className="flex items-center justify-between w-full p-2 bg-white border border-gray-300 rounded-md shadow-sm text-left">
              <div className="flex items-center min-w-0"><BuildingOfficeIcon className="w-5 h-5 mr-3 text-blue-600 flex-shrink-0" /><p className="text-sm font-semibold text-gray-800 truncate">{getButtonLabel()}</p></div>
              <ChevronDownIcon className={`h-5 w-5 text-gray-500 transition-transform ${isOpen ? 'transform rotate-180' : ''}`} />
          </button>
          {isOpen && (
              <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-80 flex flex-col">
                  <div className="p-2 border-b flex gap-2"><button onClick={() => onSelectionChange(clients.map(c => c.id))} className="text-xs text-blue-600 hover:underline">Todos</button><button onClick={() => onSelectionChange([])} className="text-xs text-blue-600 hover:underline">Ninguno</button></div>
                  <div className="overflow-y-auto">{clients.map(client => (<div key={client.id} className="p-3 hover:bg-blue-50 cursor-pointer flex items-center" onClick={() => handleClientToggle(client.id)}><input type="checkbox" checked={selectedClientIds.includes(client.id)} readOnly className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3"/><div><p className="text-sm font-medium text-gray-900">{client.name}</p><p className="text-xs text-gray-500">{client.ruc}</p></div></div>))}</div>
              </div>
          )}
      </div>
    );
};

// --- Componente Desplegable Multi-Selección de Monedas ---
const MultiCurrencySelector = ({ selectedCurrencies, onSelectionChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    const currencies = [
        { id: 'PEN', name: 'Soles (PEN)', symbol: 'S/' },
        { id: 'USD', name: 'Dólares (USD)', symbol: '$' }
    ];

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) setIsOpen(false);
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleCurrencyToggle = (currencyId) => {
        const newSelection = selectedCurrencies.includes(currencyId)
            ? selectedCurrencies.filter(id => id !== currencyId)
            : [...selectedCurrencies, currencyId];
        onSelectionChange(newSelection);
    };

    const getButtonLabel = () => {
        if (selectedCurrencies.length === 0 || selectedCurrencies.length === currencies.length) return "Todas las monedas";
        if (selectedCurrencies.length === 1) return currencies.find(c => c.id === selectedCurrencies[0])?.name;
        return `${selectedCurrencies.length} monedas seleccionadas`;
    };

    return (
        <div className="relative w-full md:w-64" ref={dropdownRef}>
            <button onClick={() => setIsOpen(!isOpen)} className="flex items-center justify-between w-full p-2 bg-white border border-gray-300 rounded-md shadow-sm text-left">
                <div className="flex items-center min-w-0">
                    <span className="text-sm mr-3 text-green-500 font-bold"> $ </span>
                    <p className="text-sm font-semibold text-gray-800 truncate">{getButtonLabel()}</p>
                </div>
                <ChevronDownIcon className={`h-5 w-5 text-gray-500 transition-transform ${isOpen ? 'transform rotate-180' : ''}`} />
            </button>
            {isOpen && (
                <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg">
                    <div className="p-2 border-b flex gap-2">
                        <button onClick={() => onSelectionChange(currencies.map(c => c.id))} className="text-xs text-blue-600 hover:underline">Todas</button>
                        <button onClick={() => onSelectionChange([])} className="text-xs text-blue-600 hover:underline">Ninguna</button>
                    </div>
                    <div className="overflow-y-auto">
                        {currencies.map(currency => (
                            <div key={currency.id} className="p-3 hover:bg-blue-50 cursor-pointer flex items-center" onClick={() => handleCurrencyToggle(currency.id)}>
                                <input type="checkbox" checked={selectedCurrencies.includes(currency.id)} readOnly className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3"/>
                                <div>
                                    <p className="text-sm font-medium text-gray-900">{currency.name}</p>
                                    <p className="text-xs text-gray-500">Símbolo: {currency.symbol}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

// --- Dashboard de KPIs ---
const KPICard = ({ title, mainValue, subValue, children }) => ( <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm h-full flex flex-col justify-between"> <div><h3 className="text-base font-semibold text-gray-600">{title}</h3><p className="text-3xl font-bold text-gray-900 mt-2">{mainValue}</p>{subValue && <p className="text-sm text-gray-500">{subValue}</p>}</div> {children} </div> );
const KPIDashboard = ({ metrics, periodLabel }) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {['PEN', 'USD'].map(currency => (
            <div key={currency} className="bg-slate-50 p-5 rounded-xl border-gray-200/80 border space-y-4">
                <h3 className="font-bold text-xl text-slate-800">Indicadores <span className="text-blue-600">{currency}</span> ({periodLabel})</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <KPICard title="Performance de Cierres" mainValue={`${metrics[currency].winPercentage.toFixed(1)}%`} subValue={`${formatCurrency(metrics[currency].montoGanado, currency)} de ${formatCurrency(metrics[currency].totalFacturado, currency)}`}>
                        <div className="w-full bg-gray-200 rounded-full h-2.5 mt-4"><div className="bg-gradient-to-r from-green-400 to-emerald-600 h-2.5 rounded-full" style={{ width: `${metrics[currency].winPercentage}%` }}></div></div>
                    </KPICard>
                    <KPICard title="Pipeline Activo" mainValue={formatCurrency(metrics[currency].montoDisponible, currency)} subValue="Monto disponible para factorizar" />
                </div>
            </div>
        ))}
    </div>
);

// --- Barra de Acciones Masivas ---
const BulkActionToolbar = ({ selectedCount, onBulkUpdate, onClear }) => { const [newStatus, setNewStatus] = useState(INVOICE_STATUSES[0]); const handleApply = () => { onBulkUpdate(newStatus); }; return ( <div className="fixed bottom-4 left-1/2 -translate-x-1/2 w-auto bg-white border border-gray-300 shadow-2xl rounded-lg z-20 flex items-center gap-4 px-4 py-3"> <span className="text-sm font-semibold text-gray-800">{selectedCount} seleccionada(s)</span> <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)} className="text-sm p-2 rounded-md border-gray-300 font-semibold focus:ring-1"> {INVOICE_STATUSES.map(s => <option key={s}>{s}</option>)} </select> <button onClick={handleApply} className="text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 py-2 px-4 rounded-lg">Aplicar Estatus</button> <button onClick={onClear} className="text-sm text-gray-600 hover:underline">Limpiar</button> </div> ); };

// --- Componente para la Fila de Grupo ---
const GroupedTableRow = ({ group, isExpanded, onExpand, selectedInvoiceKeys, onGroupSelection, onInvoiceSelection, onStatusChange }) => {
    const groupInvoiceKeys = group.invoices.map(i => i.key);
    const areAllSelected = groupInvoiceKeys.length > 0 && groupInvoiceKeys.every(k => selectedInvoiceKeys.includes(k));
    const areSomeSelected = groupInvoiceKeys.some(k => selectedInvoiceKeys.includes(k));
    const checkboxRef = useRef();
    useEffect(() => { if (checkboxRef.current) { checkboxRef.current.indeterminate = areSomeSelected && !areAllSelected; } }, [areSomeSelected, areAllSelected]);

    return (
        <React.Fragment>
            <tr className="bg-white border-b hover:bg-gray-50">
                <td className="px-4 py-3"><input type="checkbox" ref={checkboxRef} checked={areAllSelected} onChange={onGroupSelection} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /></td>
                <td className="px-4 py-4 font-medium text-gray-800 cursor-pointer" onClick={onExpand}>{group.clientName}</td>
                <td className="px-4 py-4 cursor-pointer" onClick={onExpand}>{group.debtor}</td>
                <td className="px-4 py-4 cursor-pointer" onClick={onExpand}><span className="bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded-full">{group.invoiceCount}</span></td>
                <td className="px-4 py-4 font-mono font-bold text-gray-900 cursor-pointer" onClick={onExpand}>{formatCurrency(group.totalAmount, group.currency)}</td>
            </tr>
            {isExpanded && (
                <tr className="bg-slate-50"><td colSpan="5" className="p-0"><div className="p-4">
                    <table className="w-full text-xs">
                        <thead><tr className="text-left text-gray-500"><th className="px-2 py-2 w-8"></th><th className="px-2 py-2">Factura</th><th className="px-2 py-2">Monto</th><th className="px-2 py-2">Fecha Emisión</th><th className="px-2 py-2">Estatus</th></tr></thead>
                        <tbody>
                            {group.invoices.map(invoice => (
                                <tr key={invoice.id} className="border-b border-slate-200 last:border-b-0">
                                    <td className="px-2 py-3"><input type="checkbox" checked={selectedInvoiceKeys.includes(invoice.key)} onChange={() => onInvoiceSelection(invoice.key)} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /></td>
                                    <td className="px-2 py-3 font-medium text-gray-800">{invoice.id}</td>
                                    <td className="px-2 py-3 font-mono">{formatCurrency(invoice.amount, invoice.currency)}</td>
                                    <td className="px-2 py-3">{invoice.emissionDate}</td>
                                    <td className="px-2 py-3"><select value={invoice.status} onChange={(e) => onStatusChange(invoice.clientId, invoice.id, e.target.value)} className="text-xs p-1 rounded-md border-gray-300 font-semibold focus:ring-1 w-full bg-white">{INVOICE_STATUSES.map(s => <option key={s}>{s}</option>)}</select></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div></td></tr>
            )}
        </React.Fragment>
    );
};

// --- Selector de Período ---
const PeriodSelector = ({ filter, onFilterChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [customStart, setCustomStart] = useState('');
    const [customEnd, setCustomEnd] = useState('');
    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) setIsOpen(false);
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handlePreset = (preset) => {
        onFilterChange(preset);
        setIsOpen(false);
    };

    const handleCustomApply = () => {
        if(customStart && customEnd) {
            onFilterChange({ type: 'custom', start: customStart, end: customEnd });
            setIsOpen(false);
        }
    };

    const PRESETS = [
        { key: '5days', label: 'Últimos 5 días' },
        { key: '15days', label: 'Últimos 15 días' },
        { key: '30days', label: 'Últimos 30 días' },
        { key: 'thisMonth', label: 'Mes en curso' },
    ];

    const currentLabel = PRESETS.find(p => p.key === filter.type)?.label || `Del ${filter.start} al ${filter.end}`;

    return (
        <div className="relative" ref={dropdownRef}>
            <button onClick={() => setIsOpen(!isOpen)} className="flex items-center gap-2 px-3 py-2 text-sm rounded-md bg-white border border-gray-300 font-semibold text-gray-700">
                <CalendarDaysIcon />
                <span>{currentLabel}</span>
                <ChevronDownIcon className="w-4 h-4" />
            </button>
            {isOpen && (
                <div className="absolute z-20 mt-1 w-72 bg-white border border-gray-200 rounded-md shadow-lg right-0">
                    <div className="p-2 space-y-1">
                        {PRESETS.map(p => <button key={p.key} onClick={() => handlePreset({ type: p.key })} className="w-full text-left text-sm px-3 py-1.5 rounded-md hover:bg-gray-100">{p.label}</button>)}
                    </div>
                    <div className="border-t border-gray-200 p-2 space-y-2">
                        <p className="text-sm font-semibold px-1">Personalizado</p>
                        <div className="flex items-center gap-2">
                            <input
                                type="date"
                                value={customStart}
                                onChange={e => setCustomStart(e.target.value)}
                                className="w-full text-xs p-1 border-gray-300 rounded-md"
                            />
                            <input
                                type="date"
                                value={customEnd}
                                onChange={e => setCustomEnd(e.target.value)}
                                className="w-full text-xs p-1 border-gray-300 rounded-md"
                            />
                        </div>
                        <button onClick={handleCustomApply} className="w-full text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 py-1.5 px-4 rounded-md">Aplicar</button>
                    </div>
                </div>
            )}
        </div>
    );
};

// --- Componente Principal ---
export default function App() {
  const [clients, setClients] = useState([]);
  const [selectedClientIds, setSelectedClientIds] = useState([]);
  const [selectedCurrencies, setSelectedCurrencies] = useState([]); // Todas las monedas por defecto
  const [expandedGroupKey, setExpandedGroupKey] = useState(null);
  const [dateFilter, setDateFilter] = useState({ type: 'thisMonth' });
  const [viewMode, setViewMode] = useState('grouped');
  const [selectedInvoiceKeys, setSelectedInvoiceKeys] = useState([]);
  const [invoiceStatuses, setInvoiceStatuses] = useState({});
  const [sortBy, setSortBy] = useState('fecha'); // 'fecha' o 'monto'

  // Estado para datos paginados
  const [ventas, setVentas] = useState([]);
  const [allInvoicesForMetrics, setAllInvoicesForMetrics] = useState([]); // Todas las facturas del período para calcular métricas
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total_items: 0,
    total_pages: 0,
    has_next: false,
    has_previous: false
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Calcular fechas desde/hasta basado en el filtro
  const { startDate, endDate, periodLabel, currentPeriod } = useMemo(() => {
    const today = new Date(); // Fecha actual del sistema
    console.log('Today is:', today.toISOString()); // Debug
    let start = new Date(today);
    let end = new Date(today);
    let label = '';
    let periodo = '';

    switch (dateFilter.type) {
      case '5days':
        start.setDate(today.getDate() - 5);
        label = 'Últimos 5 días';
        break;
      case '15days':
        start.setDate(today.getDate() - 15);
        label = 'Últimos 15 días';
        break;
      case '30days':
        start.setDate(today.getDate() - 30);
        label = 'Últimos 30 días';
        break;
      case 'custom':
        start = new Date(dateFilter.start);
        end = new Date(dateFilter.end);
        label = `Del ${dateFilter.start} al ${dateFilter.end}`;
        break;
      case 'thisMonth':
      default:
        start = new Date(today.getFullYear(), today.getMonth(), 1);
        end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        label = new Date(today.getFullYear(), today.getMonth()).toLocaleString('es-ES', { month: 'long', year: 'numeric' }).replace(/^\w/, c => c.toUpperCase());
        break;
    }

    // Calcular período YYYYMM para el fetch de clientes (usar el mes del startDate)
    periodo = start.getFullYear() + String(start.getMonth() + 1).padStart(2, '0');

    // Formatear fechas para la API (YYYY-MM-DD)
    const formatDate = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    return {
      startDate: formatDate(start),
      endDate: formatDate(end),
      periodLabel: label,
      currentPeriod: periodo
    };
  }, [dateFilter]);

  // Fetch clientes del período
  useEffect(() => {
    const fetchClientes = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/ventas/empresas?periodo=${currentPeriod}`);
        if (!response.ok) throw new Error(`Error al obtener empresas: ${response.status}`);
        const data = await response.json();
        const clientsFormatted = data.map(empresa => ({
          id: empresa.ruc,
          name: empresa.razon_social,
          ruc: empresa.ruc
        }));
        setClients(clientsFormatted);
      } catch (err) {
        console.error('Error fetching clientes:', err);
      }
    };
    fetchClientes();
  }, [currentPeriod]);

  // Fetch TODAS las facturas del período para métricas (sin paginación)
  useEffect(() => {
    const fetchAllInvoicesForMetrics = async () => {
      try {
        // Verificar que tengamos fechas válidas
        if (!startDate || !endDate) return;

        // Construir URL sin paginación para obtener TODAS las facturas
        let url = `${API_BASE_URL}/api/ventas?page=1&page_size=10000&fecha_desde=${startDate}&fecha_hasta=${endDate}`;

        // Aplicar los mismos filtros que la vista paginada
        if (selectedCurrencies.length === 1) {
          url += `&moneda=${selectedCurrencies[0]}`;
        }

        if (selectedClientIds.length > 0 && selectedClientIds.length < clients.length) {
          selectedClientIds.forEach(ruc => {
            url += `&rucs_empresa=${ruc}`;
          });
        }

        console.log('Fetching metrics from:', url); // Debug

        const response = await fetch(url);
        if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);

        const data = await response.json();
        console.log('Metrics data received:', data.items.length, 'invoices'); // Debug
        setAllInvoicesForMetrics(data.items);
      } catch (err) {
        console.error('Error fetching metrics data:', err);
      }
    };

    fetchAllInvoicesForMetrics();
  }, [startDate, endDate, selectedClientIds, selectedCurrencies, clients.length]);

  // Fetch ventas paginadas
  useEffect(() => {
    const fetchVentas = async () => {
      try {
        setLoading(true);
        setError(null);

        let url = `${API_BASE_URL}/api/ventas?page=${currentPage}&page_size=20&fecha_desde=${startDate}&fecha_hasta=${endDate}&sort_by=${sortBy}`;

        // Agregar filtro de moneda si hay una selección específica
        if (selectedCurrencies.length === 1) {
          url += `&moneda=${selectedCurrencies[0]}`;
        }

        // Agregar filtro de clientes
        if (selectedClientIds.length > 0 && selectedClientIds.length < clients.length) {
          selectedClientIds.forEach(ruc => {
            url += `&rucs_empresa=${ruc}`;
          });
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);

        const data = await response.json();
        setVentas(data.items);
        setPagination(data.pagination);
      } catch (err) {
        console.error('Error fetching ventas:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchVentas();
  }, [startDate, endDate, currentPage, selectedClientIds, clients.length, sortBy, selectedCurrencies]);

  // Transformar ventas a invoices (para la tabla paginada)
  const invoices = useMemo(() => {
    return ventas.map(venta => {
      const invoiceId = `${venta.serie_cdp || ''}-${venta.numero_comprobante || venta.id}`;
      const clientId = venta.ruc_empresa;
      const statusKey = `${clientId}-${invoiceId}`;

      return {
        id: invoiceId,
        clientId: clientId,
        clientName: venta.razon_social_empresa || venta.ruc_empresa,
        debtor: venta.razon_social_cliente || 'Sin nombre',
        amount: parseFloat(venta.total_comprobante) || 0,
        emissionDate: venta.fecha_emision,
        currency: venta.moneda,
        status: invoiceStatuses[statusKey] || 'Sin Gestión',
        key: statusKey
      };
    });
  }, [ventas, invoiceStatuses]);

  // Transformar TODAS las facturas del período para métricas
  const allInvoicesTransformed = useMemo(() => {
    const transformed = allInvoicesForMetrics.map(venta => {
      const invoiceId = `${venta.serie_cdp || ''}-${venta.numero_comprobante || venta.id}`;
      const clientId = venta.ruc_empresa;
      const statusKey = `${clientId}-${invoiceId}`;

      return {
        amount: parseFloat(venta.total_comprobante) || 0,
        currency: venta.moneda,
        status: invoiceStatuses[statusKey] || 'Sin Gestión',
      };
    });
    console.log('Transformed invoices for metrics:', transformed.length); // Debug
    return transformed;
  }, [allInvoicesForMetrics, invoiceStatuses]);

  // Calcular métricas usando TODAS las facturas del período
  const monthlyMetrics = useMemo(() => {
    const metrics = { PEN: {}, USD: {} };
    ['PEN', 'USD'].forEach(currency => {
        const ccyInvoices = allInvoicesTransformed.filter(inv => inv.currency === currency);
        const totalFacturado = ccyInvoices.reduce((s, i) => s + i.amount, 0);
        const montoGanado = ccyInvoices.filter(i => i.status === 'Ganada').reduce((s, i) => s + i.amount, 0);
        const lostStatuses = ['Tasa', 'Riesgo', 'Perdida sin gestión', 'No califica'];
        const montoDisponible = ccyInvoices.filter(i => !lostStatuses.includes(i.status) && i.status !== 'Ganada').reduce((s, i) => s + i.amount, 0);
        metrics[currency] = {
            totalFacturado,
            montoGanado,
            montoDisponible,
            winPercentage: totalFacturado > 0 ? (montoGanado / totalFacturado) * 100 : 0
        };
        console.log(`Metrics ${currency}:`, metrics[currency]); // Debug
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
        acc[key].totalAmount += inv.amount;
        acc[key].invoices.push(inv);
        return acc;
    }, {});

    return Object.values(groups);
  }, [invoices]);

  const handleStatusChange = (clientId, invoiceId, newStatus) => {
    const statusKey = `${clientId}-${invoiceId}`;
    setInvoiceStatuses(prev => ({
      ...prev,
      [statusKey]: newStatus
    }));
  };

  const handleBulkStatusUpdate = (newStatus) => {
    setInvoiceStatuses(prev => {
      const updated = {...prev};
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
    setCurrentPage(1); // Reset a la primera página cuando cambia el ordenamiento
  };

  const handleCurrencyChange = (newCurrencies) => {
    setSelectedCurrencies(newCurrencies);
    setCurrentPage(1); // Reset a la primera página cuando cambia el filtro de moneda
  };

  const ViewModeButton = ({ label, value, icon }) => (
    <button
      onClick={() => { setViewMode(value); setSelectedInvoiceKeys([]); }}
      className={`flex items-center gap-2 px-3 py-1 text-sm rounded-full ${viewMode === value ? 'bg-blue-600 text-white font-semibold' : 'bg-white text-gray-600 hover:bg-gray-200'}`}
    >
      {icon} {label}
    </button>
  );

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
                <PeriodSelector filter={dateFilter} onFilterChange={(newFilter) => {
                    setDateFilter(newFilter);
                    setCurrentPage(1);
                }} />
            </div>

            <div className="flex-grow overflow-x-auto">
                {viewMode === 'grouped' ? (
                    <table className="w-full text-sm text-left text-gray-600">
                        <thead className="bg-gray-50 text-xs text-gray-700 uppercase">
                           <tr><th className="px-4 py-3 w-8"></th> <th className="px-4 py-3">Cliente</th> <th className="px-4 py-3">Deudor</th> <th className="px-4 py-3"># Facturas</th> <th className="px-4 py-3">Monto Total</th></tr>
                        </thead>
                        <tbody>
                            {groupedInvoices.map(group => (
                                <GroupedTableRow
                                    key={group.key}
                                    group={group}
                                    isExpanded={expandedGroupKey === group.key}
                                    onExpand={() => setExpandedGroupKey(expandedGroupKey === group.key ? null : group.key)}
                                    selectedInvoiceKeys={selectedInvoiceKeys}
                                    onGroupSelection={() => {
                                        const groupInvoiceKeys = group.invoices.map(i => i.key);
                                        const areAllSelected = groupInvoiceKeys.every(k => selectedInvoiceKeys.includes(k));
                                        const newKeys = areAllSelected ? selectedInvoiceKeys.filter(k => !groupInvoiceKeys.includes(k)) : [...new Set([...selectedInvoiceKeys, ...groupInvoiceKeys])];
                                        setSelectedInvoiceKeys(newKeys);
                                    }}
                                    onInvoiceSelection={toggleInvoiceSelection}
                                    onStatusChange={handleStatusChange}
                                />
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <table className="w-full text-sm text-left text-gray-600">
                        <thead className="bg-gray-50 text-xs text-gray-700 uppercase">
                            <tr>
                                <th className="px-4 py-3 w-8">
                                    <input
                                        type="checkbox"
                                        onChange={(e) => setSelectedInvoiceKeys(e.target.checked ? invoices.map(i => i.key) : [])}
                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    />
                                </th>
                                <th className="px-4 py-3">Cliente</th>
                                <th className="px-4 py-3">Factura</th>
                                <th className="px-4 py-3">Deudor</th>
                                <th className="px-4 py-3">
                                    <button
                                        onClick={() => handleSortChange('monto')}
                                        className="flex items-center gap-1 hover:text-blue-600 transition-colors"
                                    >
                                        Monto
                                        {sortBy === 'monto' ? (
                                            <ChevronDownIcon className="w-4 h-4 text-blue-600" />
                                        ) : (
                                            <ArrowsUpDownIcon className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                </th>
                                <th className="px-4 py-3">
                                    <button
                                        onClick={() => handleSortChange('fecha')}
                                        className="flex items-center gap-1 hover:text-blue-600 transition-colors"
                                    >
                                        Fecha Emisión
                                        {sortBy === 'fecha' ? (
                                            <ChevronDownIcon className="w-4 h-4 text-blue-600" />
                                        ) : (
                                            <ArrowsUpDownIcon className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                </th>
                                <th className="px-4 py-3">Estatus</th>
                            </tr>
                        </thead>
                        <tbody>
                            {invoices.map(invoice => (
                                <tr key={invoice.key} className="bg-white border-b hover:bg-gray-50">
                                    <td className="px-4 py-4">
                                        <input
                                            type="checkbox"
                                            checked={selectedInvoiceKeys.includes(invoice.key)}
                                            onChange={() => toggleInvoiceSelection(invoice.key)}
                                            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                    </td>
                                    <td className="px-4 py-4 font-medium text-gray-800">{invoice.clientName}</td>
                                    <td className="px-4 py-4 font-medium text-gray-900">{invoice.id}</td>
                                    <td className="px-4 py-4">{invoice.debtor}</td>
                                    <td className="px-4 py-4 font-mono">{formatCurrency(invoice.amount, invoice.currency)}</td>
                                    <td className="px-4 py-4">{invoice.emissionDate}</td>
                                    <td className="px-4 py-4">
                                        <select
                                            value={invoice.status}
                                            onChange={(e) => handleStatusChange(invoice.clientId, invoice.id, e.target.value)}
                                            className="text-xs p-1 rounded-md border-gray-300 font-semibold focus:ring-1 w-full bg-white"
                                        >
                                            {INVOICE_STATUSES.map(s => <option key={s}>{s}</option>)}
                                        </select>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
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
