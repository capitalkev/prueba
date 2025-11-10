import React, { useState } from 'react';
import { ChevronDownIcon, ArrowsUpDownIcon } from '../icons';
import { formatCurrency } from '../utils/formatters';
import { INVOICE_STATUSES } from '../constants';
import LossReasonModal from './LossReasonModal';

/**
 * Tabla de facturas en vista detallada
 * Muestra todas las facturas en una tabla plana con ordenamiento
 */
const InvoiceTable = ({
    invoices,
    selectedInvoiceKeys,
    onToggleSelection,
    onSelectAll,
    onStatusChange,
    sortBy,
    onSortChange
}) => {
    const [lossModalOpen, setLossModalOpen] = useState(false);
    const [pendingLossInvoice, setPendingLossInvoice] = useState(null);

    const handleStatusSelectChange = (invoice, newStatus) => {
        if (newStatus === 'Perdida') {
            // Abrir modal para seleccionar motivo
            setPendingLossInvoice(invoice);
            setLossModalOpen(true);
        } else {
            // Cambiar estado directamente
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
        <>
            <LossReasonModal
                isOpen={lossModalOpen}
                onClose={handleLossCancel}
                onConfirm={handleLossConfirm}
                invoiceId={pendingLossInvoice?.id}
            />
        <table className="w-full text-sm text-left text-gray-600">
            <thead className="bg-gray-50 text-xs text-gray-700 uppercase">
                <tr>
                    <th className="px-4 py-3 w-8">
                        <input
                            type="checkbox"
                            onChange={(e) => onSelectAll(e.target.checked)}
                            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                    </th>
                    <th className="px-4 py-3">Usuario</th>
                    <th className="px-4 py-3">Cliente</th>
                    <th className="px-4 py-3">Factura</th>
                    <th className="px-4 py-3">Deudor</th>
                    <th className="px-4 py-3">
                        <button
                            onClick={() => onSortChange('monto')}
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
                            onClick={() => onSortChange('fecha')}
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
                {invoices.map(invoice => {
                    const isZeroAmount = invoice.montoNeto === 0;
                    const rowClassName = isZeroAmount
                        ? "bg-gray-100 border-b opacity-60 cursor-not-allowed"
                        : "bg-white border-b hover:bg-gray-50";

                    return (
                        <tr key={invoice.key} className={rowClassName}>
                            <td className="px-4 py-4">
                                <input
                                    type="checkbox"
                                    checked={selectedInvoiceKeys.includes(invoice.key)}
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
                                        onChange={(e) => !isZeroAmount && handleStatusSelectChange(invoice, e.target.value)}
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
                })}
            </tbody>
        </table>
        </>
    );
};

export default InvoiceTable;
