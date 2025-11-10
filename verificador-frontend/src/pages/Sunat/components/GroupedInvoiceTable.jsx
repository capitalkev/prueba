import React, { useRef, useEffect, useState } from 'react';
import { formatCurrency } from '../utils/formatters';
import { INVOICE_STATUSES } from '../constants';
import LossReasonModal from './LossReasonModal';

/**
 * Fila de grupo expandible con facturas anidadas
 */
const GroupedTableRow = ({ group, isExpanded, onExpand, selectedInvoiceKeys, onGroupSelection, onInvoiceSelection, onStatusChange }) => {
    const [lossModalOpen, setLossModalOpen] = useState(false);
    const [pendingLossInvoice, setPendingLossInvoice] = useState(null);
    // Filtrar facturas con monto 0 para la selección
    const selectableInvoices = group.invoices.filter(i => i.montoNeto !== 0);
    const groupInvoiceKeys = selectableInvoices.map(i => i.key);
    const areAllSelected = groupInvoiceKeys.length > 0 && groupInvoiceKeys.every(k => selectedInvoiceKeys.includes(k));
    const areSomeSelected = groupInvoiceKeys.some(k => selectedInvoiceKeys.includes(k));
    const checkboxRef = useRef();

    useEffect(() => {
        if (checkboxRef.current) {
            checkboxRef.current.indeterminate = areSomeSelected && !areAllSelected;
        }
    }, [areSomeSelected, areAllSelected]);

    const handleStatusSelectChange = (invoice, newStatus) => {
        if (newStatus === 'Perdida') {
            setPendingLossInvoice(invoice);
            setLossModalOpen(true);
        } else {
            onStatusChange(invoice.ventaId, invoice.clientId, invoice.id, newStatus);
        }
    };

    const handleLossConfirm = (lossReason) => {
        if (pendingLossInvoice) {
            onStatusChange(
                pendingLossInvoice.ventaId,
                pendingLossInvoice.clientId,
                pendingLossInvoice.id,
                'Perdida',
                lossReason
            );
        }
        setLossModalOpen(false);
        setPendingLossInvoice(null);
    };

    const handleLossCancel = () => {
        setLossModalOpen(false);
        setPendingLossInvoice(null);
    };

    return (
        <React.Fragment>
            <LossReasonModal
                isOpen={lossModalOpen}
                onClose={handleLossCancel}
                onConfirm={handleLossConfirm}
                invoiceId={pendingLossInvoice?.id}
            />
            <tr className="bg-white border-b hover:bg-gray-50">
                <td className="px-4 py-3">
                    <input
                        type="checkbox"
                        ref={checkboxRef}
                        checked={areAllSelected}
                        onChange={onGroupSelection}
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                </td>
                <td className="px-4 py-4 text-center text-sm text-gray-600 cursor-pointer truncate" onClick={onExpand}>
                    {group.invoices[0]?.usuario || 'Sin asignar'}
                </td>
                <td className="px-4 py-4 font-medium text-gray-800 cursor-pointer truncate" onClick={onExpand} title={group.clientName}>
                    {group.clientName}
                </td>
                <td className="px-4 py-4 cursor-pointer truncate" onClick={onExpand} title={group.debtor}>
                    {group.debtor}
                </td>
                <td className="px-4 py-4 cursor-pointer text-center" onClick={onExpand}>
                    <span className="bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded-full inline-block">
                        {group.invoiceCount}
                    </span>
                </td>
                <td className="px-4 py-4 text-center font-mono font-bold text-gray-900 cursor-pointer truncate" onClick={onExpand}>
                    {formatCurrency(group.totalAmount, group.currency)}
                </td>
            </tr>
            {isExpanded && (
                <tr className="bg-slate-50">
                    <td colSpan="6" className="p-0">
                        <div className="p-4">
                            <table className="w-full text-xs">
                                <thead>
                                    <tr className="text-left text-gray-500">
                                        <th className="px-2 py-2 w-8"></th>
                                        <th className="px-2 py-2">Factura</th>
                                        <th className="px-2 py-2">Monto</th>
                                        <th className="px-2 py-2">Fecha Emisión</th>
                                        <th className="px-2 py-2">Estatus</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {group.invoices.map(invoice => {
                                        const isZeroAmount = invoice.montoNeto === 0;
                                        return (
                                            <tr key={invoice.id} className={`border-b border-slate-200 last:border-b-0 ${isZeroAmount ? 'opacity-60' : ''}`}>
                                                <td className="px-2 py-3">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedInvoiceKeys.includes(invoice.key)}
                                                        onChange={() => !isZeroAmount && onInvoiceSelection(invoice.key)}
                                                        disabled={isZeroAmount}
                                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                                    />
                                                </td>
                                                <td className="px-2 py-3 font-medium text-gray-800">{invoice.id}</td>
                                                <td className="px-2 py-3">
                                                    {invoice.tieneNotaCredito ? (
                                                        <div className="font-mono text-xs">
                                                            <div className={isZeroAmount ? 'text-gray-600' : 'text-gray-900'}>
                                                                {formatCurrency(invoice.montoNeto, invoice.currency)}
                                                                {isZeroAmount && <span className="ml-1 text-xs text-gray-500">(Anulada)</span>}
                                                            </div>
                                                            <div className="text-[10px] line-through text-red-500">
                                                                orig. {formatCurrency(invoice.amount, invoice.currency)}
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <span className="font-mono">{formatCurrency(invoice.amount, invoice.currency)}</span>
                                                    )}
                                                </td>
                                                <td className="px-2 py-3">{invoice.emissionDate}</td>
                                                <td className="px-2 py-3">
                                                    <div>
                                                        <select
                                                            value={invoice.status}
                                                            onChange={(e) => !isZeroAmount && handleStatusSelectChange(invoice, e.target.value)}
                                                            disabled={isZeroAmount}
                                                            className="text-xs p-1 rounded-md border-gray-300 font-semibold focus:ring-1 w-full bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                                                        >
                                                            {INVOICE_STATUSES.map(s => <option key={s}>{s}</option>)}
                                                        </select>
                                                        {invoice.estado2 && (
                                                            <div className="text-[10px] text-gray-500 mt-1">
                                                                {invoice.estado2}
                                                            </div>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </td>
                </tr>
            )}
        </React.Fragment>
    );
};

/**
 * Tabla de facturas agrupadas por cliente, deudor y moneda
 * Vista colapsable/expandible
 */
const GroupedInvoiceTable = ({
    groupedInvoices,
    expandedGroupKey,
    onExpandGroup,
    selectedInvoiceKeys,
    onGroupSelection,
    onInvoiceSelection,
    onStatusChange
}) => {
    return (
        <table className="w-full text-sm text-left text-gray-600 table-fixed">
            <thead className="bg-gray-50 text-xs text-gray-700 uppercase">
                <tr>
                    <th className="px-4 py-3 w-12"></th>
                    <th className="px-4 py-3 text-center w-[15%]">Usuario</th>
                    <th className="px-4 py-3 text-center w-[25%]">Cliente</th>
                    <th className="px-4 py-3 text-center w-[25%]">Deudor</th>
                    <th className="px-4 py-3 text-center w-[15%]"># Facturas</th>
                    <th className="px-4 py-3 text-center w-[20%]">Monto Total</th>
                </tr>
            </thead>
            <tbody>
                {groupedInvoices.map(group => (
                    <GroupedTableRow
                        key={group.key}
                        group={group}
                        isExpanded={expandedGroupKey === group.key}
                        onExpand={() => onExpandGroup(expandedGroupKey === group.key ? null : group.key)}
                        selectedInvoiceKeys={selectedInvoiceKeys}
                        onGroupSelection={() => {
                            const groupInvoiceKeys = group.invoices.map(i => i.key);
                            const areAllSelected = groupInvoiceKeys.every(k => selectedInvoiceKeys.includes(k));
                            const newKeys = areAllSelected
                                ? selectedInvoiceKeys.filter(k => !groupInvoiceKeys.includes(k))
                                : [...new Set([...selectedInvoiceKeys, ...groupInvoiceKeys])];
                            onGroupSelection(newKeys);
                        }}
                        onInvoiceSelection={onInvoiceSelection}
                        onStatusChange={onStatusChange}
                    />
                ))}
            </tbody>
        </table>
    );
};

export default GroupedInvoiceTable;
