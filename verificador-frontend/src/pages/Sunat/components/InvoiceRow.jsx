import React from 'react';
import { formatCurrency } from '../utils/formatters';
import { STATUS_COLORS } from '../constants';

const InvoiceRow = React.memo(({
    invoice,
    isSelected,
    onToggleSelection,
    onStatusChange,
    onViewCompany,
    selectMode,
    showCheckboxes
}) => {
    const rowClassName = `
        border-b hover:bg-gray-50 transition-colors cursor-pointer
        ${isSelected ? 'bg-blue-50' : ''}
    `;

    const statusColor = STATUS_COLORS[invoice.status] || 'bg-gray-100 text-gray-600';

    return (
        <tr className={rowClassName}>
            {showCheckboxes && (
                <td className="py-3 px-2 text-center">
                    <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => onToggleSelection(invoice.key)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-2"
                    />
                </td>
            )}

            <td className="py-3 px-4">
                <button
                    onClick={() => onViewCompany(invoice.clientId)}
                    className="text-blue-600 hover:text-blue-800 hover:underline font-medium text-sm"
                >
                    {invoice.clientName}
                </button>
                <div className="text-xs text-gray-500">RUC: {invoice.clientId}</div>
            </td>

            <td className="py-3 px-4 text-sm">{invoice.id}</td>

            <td className="py-3 px-4 text-sm">
                <div>{invoice.debtor}</div>
                <div className="text-xs text-gray-500">RUC: {invoice.debtorRuc}</div>
            </td>

            <td className="py-3 px-4 text-sm text-right font-medium">
                <div>{formatCurrency(invoice.amount, invoice.currency)}</div>
                {invoice.amount !== invoice.netAmount && (
                    <div className="text-xs text-gray-500">
                        Neto: {formatCurrency(invoice.netAmount, invoice.currency)}
                    </div>
                )}
            </td>

            <td className="py-3 px-4 text-sm text-center">{invoice.currency}</td>

            <td className="py-3 px-4 text-sm">{invoice.emissionDate}</td>

            <td className="py-3 px-4">
                <select
                    value={invoice.status}
                    onChange={(e) => onStatusChange(invoice.ventaId, e.target.value, invoice.estado2)}
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColor}`}
                >
                    <option value="Nueva Oportunidad">Nueva Oportunidad</option>
                    <option value="Contactado">Contactado</option>
                    <option value="Negociación">Negociación</option>
                    <option value="Ganada">Ganada</option>
                    <option value="Perdida">Perdida</option>
                    <option value="Sin gestión">Sin gestión</option>
                </select>
            </td>

            <td className="py-3 px-4 text-sm">
                {invoice.usuarioNombre || invoice.usuarioEmail || '-'}
            </td>
        </tr>
    );
}, (prevProps, nextProps) => {
    // Custom comparison - solo re-render si cambian propiedades relevantes
    return (
        prevProps.invoice.ventaId === nextProps.invoice.ventaId &&
        prevProps.invoice.status === nextProps.invoice.status &&
        prevProps.invoice.amount === nextProps.invoice.amount &&
        prevProps.invoice.netAmount === nextProps.invoice.netAmount &&
        prevProps.isSelected === nextProps.isSelected &&
        prevProps.selectMode === nextProps.selectMode
    );
});

InvoiceRow.displayName = 'InvoiceRow';

export default InvoiceRow;
