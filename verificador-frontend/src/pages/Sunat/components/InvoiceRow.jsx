import React from 'react';
import { formatCurrency } from '../utils/formatters';
import { INVOICE_STATUSES } from '../constants';

const InvoiceRow = React.memo(({
    invoice,
    isSelected,
    onToggleSelection,
    onStatusChange
}) => {
    const isZeroAmount = invoice.montoNeto === 0;
    const rowClassName = isZeroAmount
        ? "bg-gray-100 border-b opacity-60 cursor-not-allowed"
        : "bg-white border-b hover:bg-gray-50";

    return (
        <tr className={rowClassName}>
            <td className="px-4 py-4">
                <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => !isZeroAmount && onToggleSelection(invoice.key)}
                    disabled={isZeroAmount}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                />
            </td>

            <td className="px-4 py-4 text-sm text-gray-600">{invoice.usuario}</td>

            <td className="px-4 py-4 font-medium text-gray-800">{invoice.clientName}</td>

            <td className="px-4 py-4 font-medium text-gray-900">{invoice.id}</td>

            <td className="px-4 py-4">{invoice.debtor}</td>

            <td className="px-4 py-4">
                {invoice.tieneNotaCredito ? (
                    <div className="font-mono">
                        <div className={isZeroAmount ? 'text-gray-600' : 'text-gray-900'}>
                            {formatCurrency(invoice.montoNeto, invoice.currency)}
                            {isZeroAmount && <span className="ml-2 text-xs text-gray-500">(Anulada)</span>}
                        </div>
                        <div className="text-xs line-through text-red-500">
                            orig. {formatCurrency(invoice.amount, invoice.currency)}
                        </div>
                    </div>
                ) : (
                    <span className="font-mono">{formatCurrency(invoice.amount, invoice.currency)}</span>
                )}
            </td>

            <td className="px-4 py-4">{invoice.emissionDate}</td>

            <td className="px-4 py-4">
                <div>
                    <select
                        value={invoice.status}
                        onChange={(e) => !isZeroAmount && onStatusChange(invoice, e.target.value)}
                        disabled={isZeroAmount}
                        className="text-xs p-1 rounded-md border-gray-300 font-semibold focus:ring-1 w-full bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {INVOICE_STATUSES.map(s => <option key={s}>{s}</option>)}
                    </select>
                    {invoice.estado2 && (
                        <div className="text-xs text-gray-500 mt-1">
                            {invoice.estado2}
                        </div>
                    )}
                </div>
            </td>
        </tr>
    );
}, (prevProps, nextProps) => {
    // Solo re-render si cambian propiedades relevantes
    return (
        prevProps.invoice.key === nextProps.invoice.key &&
        prevProps.invoice.status === nextProps.invoice.status &&
        prevProps.invoice.montoNeto === nextProps.invoice.montoNeto &&
        prevProps.invoice.estado2 === nextProps.invoice.estado2 &&
        prevProps.isSelected === nextProps.isSelected
    );
});

InvoiceRow.displayName = 'InvoiceRow';

export default InvoiceRow;
