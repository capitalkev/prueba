import React, { useState } from 'react';
import { ChevronDownIcon, ArrowsUpDownIcon } from '../icons';
import LossReasonModal from './LossReasonModal';
import InvoiceRow from './InvoiceRow';

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
        <table className="w-full text-sm text-left text-gray-600 table-fixed">
            <thead className="bg-gray-50 text-xs text-gray-700 uppercase">
                <tr>
                    <th className="px-4 py-3 w-[5%]">
                        <input
                            type="checkbox"
                            onChange={(e) => onSelectAll(e.target.checked)}
                            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                    </th>
                    <th className="px-4 py-3 w-[15%]">Usuario</th>
                    <th className="px-4 py-3 w-[20%]">Cliente</th>
                    <th className="px-4 py-3 w-[12%]">Factura</th>
                    <th className="px-4 py-3 w-[20%]">Deudor</th>
                    <th className="px-4 py-3 w-[10%]">
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
                    <th className="px-4 py-3 w-[10%]">
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
                    <th className="px-4 py-3 w-[8%]">Estatus</th>
                </tr>
            </thead>
            <tbody>
                {invoices.map(invoice => (
                    <InvoiceRow
                        key={invoice.key}
                        invoice={invoice}
                        isSelected={selectedInvoiceKeys.includes(invoice.key)}
                        onToggleSelection={onToggleSelection}
                        onStatusChange={handleStatusSelectChange}
                    />
                ))}
            </tbody>
        </table>
        </>
    );
};

export default InvoiceTable;
