import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { Icon } from '../Icon';
import { Textarea } from '../ui/Textarea';
import { Modal } from '../ui/Modal';

export const AdelantoExpressModal = ({ isOpen, onClose, onConfirm, operation }) => {
    const [justification, setJustification] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    useEffect(() => {
        if (!isOpen) {
            setTimeout(() => {
                setJustification('');
                setIsSubmitting(false);
                setIsSuccess(false);
            }, 300);
        }
    }, [isOpen]);

    const handleSubmit = async () => {
        if (!justification.trim()) return;
        setIsSubmitting(true);
        
        await onConfirm(justification);
        
        setIsSuccess(true);
        setTimeout(() => {
            onClose();
        }, 1500);
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="md">
            <div className="flex justify-between items-center p-4 border-b border-gray-200">
                <h3 className="text-xl font-semibold text-gray-900">Avanzar a Post-Verificado</h3>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}><Icon name="X" size={20}/></Button>
            </div>
            <div className="p-6">
                <AnimatePresence mode="wait">
                    {isSuccess ? (
                        <motion.div
                            key="success"
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            className="text-center py-10"
                        >
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1, transition: { type: 'spring', stiffness: 260, damping: 20 } }}
                                className="w-20 h-20 bg-green-100 rounded-full mx-auto flex items-center justify-center"
                            >
                                <Icon name="Check" size={48} className="text-green-600" />
                            </motion.div>
                            <h4 className="text-lg font-semibold text-gray-800 mt-4">¡Operación Avanzada!</h4>
                            <p className="text-gray-500">La operación {operation?.id} se ha movido a "Adelanto Express".</p>
                        </motion.div>
                    ) : (
                        <motion.div key="form" exit={{ opacity: 0 }}>
                            <p className="text-sm text-gray-600 mb-4">
                                Estás a punto de mover la operación <strong className="text-gray-800">{operation?.id}</strong> a la cola de "Adelanto Express". Ingresa una justificación.
                            </p>
                            <Textarea 
                                value={justification}
                                onChange={(e) => setJustification(e.target.value)}
                                placeholder="Ej: Contacto con Gerente de Finanzas confirmó la operación por teléfono..."
                                rows={4}
                            />
                            <div className="flex justify-end gap-3 mt-6">
                                <Button variant="outline" onClick={onClose} disabled={isSubmitting}>Cancelar</Button>
                                <Button 
                                    variant="primary" 
                                    onClick={handleSubmit} 
                                    disabled={!justification.trim() || isSubmitting}
                                    iconName={isSubmitting ? "LoaderCircle" : "Zap"}
                                >
                                    {isSubmitting ? 'Procesando...' : 'Confirmar Avance'}
                                </Button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </Modal>
    );
};