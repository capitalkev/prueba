import React, { useState, useMemo, useEffect, useRef } from 'react';

// --- Iconos SVG ---
const BuildingOfficeIcon = ({ className = "w-6 h-6" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6h1.5m-1.5 3h1.5m-1.5 3h1.5M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M12.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21" /></svg>;
const ChevronDownIcon = ({ className = "w-5 h-5" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>;
const ChevronRightIcon = ({ className = "w-4 h-4" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>;
const CalendarDaysIcon = ({ className = "w-5 h-5" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0h18M-4.5 12h22.5" /></svg>;
const ViewListIcon = ({ className = "w-5 h-5" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" /></svg>;
const ViewGridIcon = ({ className = "w-5 h-5" }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 8.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25v2.25A2.25 2.25 0 018.25 21H6a2.25 2.25 0 01-2.25-2.25v-2.25zM13.5 6A2.25 2.25 0 0115.75 3.75h2.25A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25A2.25 2.25 0 0113.5 8.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25h2.25a2.25 2.25 0 012.25 2.25v2.25a2.25 2.25 0 01-2.25 2.25h-2.25a2.25 2.25 0 01-2.25-2.25v-2.25z" /></svg>;


// --- Datos de Ejemplo ---
const initialMockData = [
  { id: 1, name: 'GLOVIC INVERSIONES S.A.C.', ruc: '20601234567',
    availableInvoices: [
      { id: 'F001-1234', debtor: 'RIPLEY PERU S.A.', amount: 45000.00, currency: 'PEN', emissionDate: '2025-10-20', status: 'Tasa', log: [] },
      { id: 'F001-1235', debtor: 'SAGA FALABELLA S.A.', amount: 32500.50, currency: 'PEN', emissionDate: '2025-10-18', status: 'Ganada', log: [] },
      { id: 'F001-1236', debtor: 'RIPLEY PERU S.A.', amount: 12000.00, currency: 'PEN', emissionDate: '2025-10-19', status: 'Sin gestión', log: [] },
      { id: 'E001-456', debtor: 'PROMART S.A.', amount: 15000.00, currency: 'USD', emissionDate: '2025-10-16', status: 'Sin gestión', log: [] },
      { id: 'E001-457', debtor: 'SODIMAC PERU S.A.', amount: 22000.00, currency: 'USD', emissionDate: '2025-09-15', status: 'Riesgo', log: [] },
    ],
  },
  { id: 2, name: 'MORE S.R.L. CONTRATISTAS', ruc: '20509876543',
    availableInvoices: [
      { id: 'F002-887', debtor: 'CONSTRUCTORA OAS S.A.', amount: 125000.00, currency: 'PEN', emissionDate: '2025-10-17', status: 'Riesgo', log: [] },
      { id: 'F002-888', debtor: 'COSAPI S.A.', amount: 35000.00, currency: 'USD', emissionDate: '2025-10-18', status: 'Perdida sin gestión', log: [] },
      { id: 'F002-890', debtor: 'CONSTRUCTORA OAS S.A.', amount: 85000.00, currency: 'PEN', emissionDate: '2025-09-19', status: 'Sin gestión', log: [] },
    ],
  },
];

const INVOICE_STATUSES = ['Sin gestión', 'Tasa', 'Riesgo', 'Perdida sin gestión', 'Ganada', 'No califica'];

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


// --- Dashboard de KPIs ---
const KPICard = ({ title, mainValue, subValue, children }) => ( <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm h-full flex flex-col justify-between"> <div><h3 className="text-base font-semibold text-gray-600">{title}</h3><p className="text-3xl font-bold text-gray-900 mt-2">{mainValue}</p>{subValue && <p className="text-sm text-gray-500">{subValue}</p>}</div> {children} </div> );
const KPIDashboard = ({ metrics, periodLabel }) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {['PEN', 'USD'].map(currency => (
            <div key={currency} className="bg-slate-50 p-5 rounded-xl border-gray-200/80 border space-y-4">
                <h3 className="font-bold text-xl text-slate-800">Indicadores <span className="text-blue-600">{currency}</span> ({periodLabel})</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <KPICard title="Performance de Cierres" mainValue={`${metrics[currency].winPercentage.toFixed(1)}%`} subValue={`${metrics[currency].montoGanado} de ${metrics[currency].totalFacturado}`}>
                        <div className="w-full bg-gray-200 rounded-full h-2.5 mt-4"><div className="bg-gradient-to-r from-green-400 to-emerald-600 h-2.5 rounded-full" style={{ width: `${metrics[currency].winPercentage}%` }}></div></div>
                    </KPICard>
                    <KPICard title="Pipeline Activo" mainValue={metrics[currency].montoDisponible} subValue="Monto disponible para factorizar" />
                </div>
            </div>
        ))}
    </div>
);

// --- Barra de Acciones Masivas ---
const BulkActionToolbar = ({ selectedCount, onBulkUpdate, onClear }) => { const [newStatus, setNewStatus] = useState(INVOICE_STATUSES[0]); const handleApply = () => { onBulkUpdate(newStatus); }; return ( <div className="fixed bottom-4 left-1/2 -translate-x-1/2 w-auto bg-white border border-gray-300 shadow-2xl rounded-lg z-20 flex items-center gap-4 px-4 py-3"> <span className="text-sm font-semibold text-gray-800">{selectedCount} seleccionada(s)</span> <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)} className="text-sm p-2 rounded-md border-gray-300 font-semibold focus:ring-1"> {INVOICE_STATUSES.map(s => <option key={s}>{s}</option>)} </select> <button onClick={handleApply} className="text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 py-2 px-4 rounded-lg">Aplicar Estatus</button> <button onClick={onClear} className="text-sm text-gray-600 hover:underline">Limpiar</button> </div> ); };

// --- Componente para la Fila de Grupo ---
const GroupedTableRow = ({ group, isExpanded, onExpand, selectedInvoiceKeys, onGroupSelection, onInvoiceSelection, onStatusChange, formatCurrency }) => { const groupInvoiceKeys = group.invoices.map(i => i.key); const areAllSelected = groupInvoiceKeys.length > 0 && groupInvoiceKeys.every(k => selectedInvoiceKeys.includes(k)); const areSomeSelected = groupInvoiceKeys.some(k => selectedInvoiceKeys.includes(k)); const checkboxRef = useRef(); useEffect(() => { if (checkboxRef.current) { checkboxRef.current.indeterminate = areSomeSelected && !areAllSelected; } }, [areSomeSelected, areAllSelected]); return ( <React.Fragment> <tr className="bg-white border-b hover:bg-gray-50"> <td className="px-4 py-3"><input type="checkbox" ref={checkboxRef} checked={areAllSelected} onChange={onGroupSelection} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /></td> <td className="px-4 py-4 font-medium text-gray-800 cursor-pointer" onClick={onExpand}>{group.clientName}</td> <td className="px-4 py-4 cursor-pointer" onClick={onExpand}>{group.debtor}</td> <td className="px-4 py-4 cursor-pointer" onClick={onExpand}><span className="bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded-full">{group.invoiceCount}</span></td> <td className="px-4 py-4 font-mono font-bold text-gray-900 cursor-pointer" onClick={onExpand}>{formatCurrency(group.totalAmount, group.currency)}</td> </tr> {isExpanded && ( <tr className="bg-slate-50"><td colSpan="5" className="p-0"><div className="p-4"> <table className="w-full text-xs"> <thead><tr className="text-left text-gray-500"><th className="px-2 py-2 w-8"></th><th className="px-2 py-2">Factura</th><th className="px-2 py-2">Monto</th><th className="px-2 py-2">Fecha Emisión</th><th className="px-2 py-2">Estatus</th></tr></thead> <tbody> {group.invoices.map(invoice => ( <tr key={invoice.id} className="border-b border-slate-200 last:border-b-0"> <td className="px-2 py-3"><input type="checkbox" checked={selectedInvoiceKeys.includes(invoice.key)} onChange={() => onInvoiceSelection(invoice.key)} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /></td> <td className="px-2 py-3 font-medium text-gray-800">{invoice.id}</td> <td className="px-2 py-3 font-mono">{formatCurrency(invoice.amount, invoice.currency)}</td> <td className="px-2 py-3">{invoice.emissionDate}</td> <td className="px-2 py-3"><select value={invoice.status} onChange={(e) => onStatusChange(invoice.clientId, invoice.id, e.target.value)} className="text-xs p-1 rounded-md border-gray-300 font-semibold focus:ring-1 w-full bg-white">{INVOICE_STATUSES.map(s => <option key={s}>{s}</option>)}</select></td> </tr> ))} </tbody> </table> </div></td></tr> )} </React.Fragment> ); };

// --- Selector de Período ---
const PeriodSelector = ({ filter, onFilterChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [customStart, setCustomStart] = useState('');
    const [customEnd, setCustomEnd] = useState('');
    const dropdownRef = useRef(null);
    useEffect(() => { const handleClickOutside = (event) => { if (dropdownRef.current && !dropdownRef.current.contains(event.target)) setIsOpen(false); }; document.addEventListener("mousedown", handleClickOutside); return () => document.removeEventListener("mousedown", handleClickOutside); }, []);

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
                            <input type="date" value={customStart} onChange={e => setCustomStart(e.target.value)} className="w-full text-xs p-1 border-gray-300 rounded-md"/>
                             <input type="date" value={customEnd} onChange={e => setCustomEnd(e.target.value)} className="w-full text-xs p-1 border-gray-300 rounded-md"/>
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
  const [clients, setClients] = useState(initialMockData);
  const [selectedClientIds, setSelectedClientIds] = useState([]);
  const [expandedGroupKey, setExpandedGroupKey] = useState(null);
  const [dateFilter, setDateFilter] = useState({ type: 'thisMonth' });
  const [viewMode, setViewMode] = useState('grouped'); 
  const [selectedInvoiceKeys, setSelectedInvoiceKeys] = useState([]);

  const { monthlyMetrics, groupedInvoices, detailedInvoices, periodLabel } = useMemo(() => {
    const formatCurrency = (value, currency) => new Intl.NumberFormat('es-PE', { style: 'currency', currency, minimumFractionDigits: 2 }).format(value);
    
    // --- Lógica de Fecha Centralizada ---
    const today = new Date('2025-10-20T12:00:00Z');
    let startDate = new Date(today);
    let endDate = new Date(today);
    let tempLabel = '';

    switch (dateFilter.type) {
        case '5days': startDate.setDate(today.getDate() - 5); tempLabel = 'Últimos 5 días'; break;
        case '15days': startDate.setDate(today.getDate() - 15); tempLabel = 'Últimos 15 días'; break;
        case '30days': startDate.setDate(today.getDate() - 30); tempLabel = 'Últimos 30 días'; break;
        case 'custom':
            startDate = new Date(dateFilter.start.replace(/-/g, '/'));
            endDate = new Date(dateFilter.end.replace(/-/g, '/'));
            tempLabel = 'Personalizado';
            break;
        case 'thisMonth':
        default:
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            tempLabel = new Date(today.getFullYear(), today.getMonth()).toLocaleString('es-ES', { month: 'long', year: 'numeric' }).replace(/^\w/, c => c.toUpperCase());
    }
    
    const allInvoices = clients.flatMap(c => c.availableInvoices.map(inv => ({...inv, clientId: c.id, clientName: c.name, key: `${c.id}-${inv.id}`})));
    const invoicesInDateRange = allInvoices.filter(inv => {
        const emissionDate = new Date(inv.emissionDate.replace(/-/g, '/'));
        return emissionDate >= startDate && emissionDate <= endDate;
    });
    
    // --- Métricas ahora se basan en el rango seleccionado ---
    const metrics = { PEN: {}, USD: {} };
    ['PEN', 'USD'].forEach(currency => {
        const ccyInvoices = invoicesInDateRange.filter(inv => inv.currency === currency);
        const totalFacturado = ccyInvoices.reduce((s, i) => s + i.amount, 0);
        const montoGanado = ccyInvoices.filter(i => i.status === 'Ganada').reduce((s, i) => s + i.amount, 0);
        const lostStatuses = ['Tasa', 'Riesgo', 'Perdida sin gestión', 'No califica'];
        const montoDisponible = ccyInvoices.filter(i => !lostStatuses.includes(i.status) && i.status !== 'Ganada').reduce((s, i) => s + i.amount, 0);
        metrics[currency] = { totalFacturado: formatCurrency(totalFacturado, currency), montoGanado: formatCurrency(montoGanado, currency), montoDisponible: formatCurrency(montoDisponible, currency), winPercentage: totalFacturado > 0 ? (montoGanado / totalFacturado) * 100 : 0 };
    });

    const clientFilteredInvoices = invoicesInDateRange.filter(inv => selectedClientIds.length === 0 || selectedClientIds.includes(inv.clientId));
    const groups = clientFilteredInvoices.reduce((acc, inv) => {
        const key = `${inv.clientId}-${inv.debtor}-${inv.currency}`;
        if (!acc[key]) { acc[key] = { key, clientName: inv.clientName, debtor: inv.debtor, currency: inv.currency, invoiceCount: 0, totalAmount: 0, invoices: [] }; }
        acc[key].invoiceCount++;
        acc[key].totalAmount += inv.amount;
        acc[key].invoices.push(inv);
        return acc;
    }, {});

    return { monthlyMetrics: metrics, groupedInvoices: Object.values(groups), detailedInvoices: clientFilteredInvoices, periodLabel: tempLabel };
  }, [clients, selectedClientIds, dateFilter]);

  const handleStatusChange = (clientId, invoiceId, newStatus) => { setClients(prev => prev.map(c => c.id !== clientId ? c : {...c, availableInvoices: c.availableInvoices.map(i => i.id === invoiceId ? {...i, status: newStatus} : i)})); };
  const handleBulkStatusUpdate = (newStatus) => { setClients(prevClients => prevClients.map(client => ({ ...client, availableInvoices: client.availableInvoices.map(invoice => { const key = `${client.id}-${invoice.id}`; return selectedInvoiceKeys.includes(key) ? { ...invoice, status: newStatus } : invoice; }) }))); setSelectedInvoiceKeys([]); };
  const toggleInvoiceSelection = (key) => { setSelectedInvoiceKeys(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]); };
  
  const formatCurrency = (value, currency) => new Intl.NumberFormat('es-PE', { style: 'currency', currency, minimumFractionDigits: 2 }).format(value);
  const ViewModeButton = ({ label, value, icon }) => ( <button onClick={() => { setViewMode(value); setSelectedInvoiceKeys([]); }} className={`flex items-center gap-2 px-3 py-1 text-sm rounded-full ${viewMode === value ? 'bg-blue-600 text-white font-semibold' : 'bg-white text-gray-600 hover:bg-gray-200'}`}>{icon} {label}</button> );

  return (
    <div className="bg-gray-100 font-sans h-screen w-full flex flex-col p-4 gap-4">
        <header className="flex-shrink-0"><MultiClientSelector clients={clients} selectedClientIds={selectedClientIds} onSelectionChange={setSelectedClientIds}/></header>
        <div className="flex-shrink-0"><KPIDashboard metrics={monthlyMetrics} periodLabel={periodLabel} /></div>
        
        <main className="flex-grow bg-white rounded-lg border border-gray-200 shadow-sm overflow-y-auto flex flex-col relative">
            <div className="p-4 border-b flex flex-col md:flex-row justify-between items-center gap-4">
                <div className="flex items-center gap-2">
                    <ViewModeButton label="Agrupada" value="grouped" icon={<ViewGridIcon />} />
                    <ViewModeButton label="Detallada" value="detailed" icon={<ViewListIcon />} />
                </div>
                <PeriodSelector filter={dateFilter} onFilterChange={setDateFilter} />
            </div>
            <div className="overflow-x-auto">
                {viewMode === 'grouped' ? (
                    <table className="w-full text-sm text-left text-gray-600">
                        {/* Vista Agrupada */}
                        <thead className="bg-gray-50 text-xs text-gray-700 uppercase">
                           <tr><th className="px-4 py-3 w-8"></th> <th className="px-4 py-3">Cliente</th> <th className="px-4 py-3">Deudor</th> <th className="px-4 py-3"># Facturas</th> <th className="px-4 py-3">Monto Total</th></tr>
                        </thead>
                        <tbody>
                            {groupedInvoices.map(group => ( <GroupedTableRow key={group.key} group={group} isExpanded={expandedGroupKey === group.key} onExpand={() => setExpandedGroupKey(expandedGroupKey === group.key ? null : group.key)} selectedInvoiceKeys={selectedInvoiceKeys} onGroupSelection={() => { const groupInvoiceKeys = group.invoices.map(i => i.key); const areAllSelected = groupInvoiceKeys.every(k => selectedInvoiceKeys.includes(k)); const newKeys = areAllSelected ? selectedInvoiceKeys.filter(k => !groupInvoiceKeys.includes(k)) : [...new Set([...selectedInvoiceKeys, ...groupInvoiceKeys])]; setSelectedInvoiceKeys(newKeys); }} onInvoiceSelection={toggleInvoiceSelection} onStatusChange={handleStatusChange} formatCurrency={formatCurrency} /> ))}
                        </tbody>
                    </table>
                ) : (
                    <table className="w-full text-sm text-left text-gray-600">
                        {/* Vista Detallada */}
                        <thead className="bg-gray-50 text-xs text-gray-700 uppercase">
                            <tr><th className="px-4 py-3 w-8"><input type="checkbox" onChange={(e) => setSelectedInvoiceKeys(e.target.checked ? detailedInvoices.map(i => i.key) : [])} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"/></th> <th className="px-4 py-3">Cliente</th> <th className="px-4 py-3">Factura</th> <th className="px-4 py-3">Deudor</th> <th className="px-4 py-3">Monto</th> <th className="px-4 py-3">Fecha Emisión</th> <th className="px-4 py-3">Estatus</th></tr>
                        </thead>
                        <tbody>
                            {detailedInvoices.map(invoice => (
                                <tr key={invoice.key} className="bg-white border-b hover:bg-gray-50">
                                    <td className="px-4 py-4"><input type="checkbox" checked={selectedInvoiceKeys.includes(invoice.key)} onChange={() => toggleInvoiceSelection(invoice.key)} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"/></td>
                                    <td className="px-4 py-4 font-medium text-gray-800">{invoice.clientName}</td>
                                    <td className="px-4 py-4 font-medium text-gray-900">{invoice.id}</td>
                                    <td className="px-4 py-4">{invoice.debtor}</td>
                                    <td className="px-4 py-4 font-mono">{formatCurrency(invoice.amount, invoice.currency)}</td>
                                    <td className="px-4 py-4">{invoice.emissionDate}</td>
                                    <td className="px-4 py-4"><select value={invoice.status} onChange={(e) => handleStatusChange(invoice.clientId, invoice.id, e.target.value)} className="text-xs p-1 rounded-md border-gray-300 font-semibold focus:ring-1 w-full bg-white">{INVOICE_STATUSES.map(s => <option key={s}>{s}</option>)}</select></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
             {selectedInvoiceKeys.length > 0 && <BulkActionToolbar selectedCount={selectedInvoiceKeys.length} onBulkUpdate={handleBulkStatusUpdate} onClear={() => setSelectedInvoiceKeys([])} /> }
        </main>
    </div>
  );
}

