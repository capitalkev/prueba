import React, { useState } from 'react';
import { INVOICE_STATUSES } from '../constants';

/**
 * Barra de herramientas para acciones masivas sobre facturas seleccionadas
 * Aparece en la parte inferior cuando hay facturas seleccionadas
 */
const BulkActionToolbar = ({ selectedCount, onBulkUpdate, onClear }) => {
    const [newStatus, setNewStatus] = useState(INVOICE_STATUSES[0]);

    const handleApply = () => {
        onBulkUpdate(newStatus);
    };

    return (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 w-auto bg-white border border-gray-300 shadow-2xl rounded-lg z-20 flex items-center gap-4 px-4 py-3">
            <span className="text-sm font-semibold text-gray-800">
                {selectedCount} seleccionada(s)
            </span>
            <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="text-sm p-2 rounded-md border-gray-300 font-semibold focus:ring-1"
            >
                {INVOICE_STATUSES.map(s => <option key={s}>{s}</option>)}
            </select>
            <button
                onClick={handleApply}
                className="text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 py-2 px-4 rounded-lg"
            >
                Aplicar Estatus
            </button>
            <button
                onClick={onClear}
                className="text-sm text-gray-600 hover:underline"
            >
                Limpiar
            </button>
        </div>
    );
};

export default BulkActionToolbar;
