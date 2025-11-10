import React, { useState } from 'react';
import { LOSS_REASONS } from '../constants';

/**
 * Modal para seleccionar el motivo de pérdida de una factura
 * Se muestra cuando el usuario cambia el estado a "Perdida"
 */
const LossReasonModal = ({ isOpen, onClose, onConfirm, invoiceId }) => {
    const [selectedReason, setSelectedReason] = useState('Por Tasa');

    if (!isOpen) return null;

    const handleConfirm = () => {
        onConfirm(selectedReason);
        setSelectedReason('Por Tasa'); // Reset para próxima vez
    };

    const handleCancel = () => {
        setSelectedReason('Por Tasa'); // Reset
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">
                        Motivo de Pérdida
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                        Por favor, especifica por qué se perdió esta oportunidad:
                    </p>
                </div>

                {/* Body */}
                <div className="px-6 py-4">
                    <select
                        value={selectedReason}
                        onChange={(e) => setSelectedReason(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        {LOSS_REASONS.map(reason => (
                            <option key={reason} value={reason}>
                                {reason}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3 rounded-b-lg">
                    <button
                        onClick={handleCancel}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleConfirm}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Confirmar Pérdida
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LossReasonModal;
