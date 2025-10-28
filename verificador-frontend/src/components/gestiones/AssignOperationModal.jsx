import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Icon } from '../Icon';

export const AssignOperationModal = ({ isOpen, onClose, onConfirm, operation, analysts = [] }) => {
    const [selectedAnalyst, setSelectedAnalyst] = useState(operation?.analistaAsignado?.email || '');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async () => {
        if (!selectedAnalyst) return;
        setIsSubmitting(true);
        await onConfirm(operation.id, selectedAnalyst);
        setIsSubmitting(false);
        onClose();
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="md">
            <div className="p-4 border-b">
                <h3 className="text-xl font-semibold">Asignar Operación</h3>
                <p className="text-sm text-gray-500">Operación: {operation?.id}</p>
            </div>
            <div className="p-6 space-y-4">
                <p>Selecciona un analista para asignarle esta operación:</p>
                <select
                    value={selectedAnalyst}
                    onChange={(e) => setSelectedAnalyst(e.target.value)}
                    className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                    <option value="" disabled>-- Elige un analista --</option>
                    {analysts.map(analyst => (
                        <option key={analyst.email} value={analyst.email}>
                            {analyst.nombre}
                        </option>
                    ))}
                </select>
            </div>
            <div className="p-4 bg-gray-50 flex justify-end gap-3 rounded-b-xl">
                <Button variant="outline" onClick={onClose} disabled={isSubmitting}>Cancelar</Button>
                <Button
                    onClick={handleSubmit}
                    disabled={!selectedAnalyst || isSubmitting}
                    iconName={isSubmitting ? "LoaderCircle" : "UserCog"}
                >
                    {isSubmitting ? 'Asignando...' : 'Confirmar Asignación'}
                </Button>
            </div>
        </Modal>
    );
};