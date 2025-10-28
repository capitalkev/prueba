// src/components/ProcessingModal.jsx

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Icon } from './Icon';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/Card';
import { Button } from './ui/Button';

// --- Subcomponentes para cada estado ---

const ChecklistItem = ({ text, status }) => {
    const statusMap = {
        pending: { icon: 'Clock', color: 'text-gray-400', animate: false },
        in_progress: { icon: 'Loader', color: 'text-blue-500', animate: true },
        success: { icon: 'CheckCircle', color: 'text-green-500', animate: false },
    };
    const current = statusMap[status] || statusMap.pending;
    return (
        <div className="flex items-center gap-3 text-sm">
            <Icon name={current.icon} className={`${current.color} ${current.animate ? 'animate-spin' : ''} w-5 h-5 flex-shrink-0`} />
            <span className={`${status === 'pending' ? 'text-gray-500' : 'text-gray-800'}`}>{text}</span>
        </div>
    );
};

const LoadingState = ({ steps }) => {
    const stepLabels = {
        submitted: "Subiendo y asegurando archivos",
        parsed: "Analizando facturas (XML) y Verificando con Cavali",
        drive_archived: "Creando carpeta de respaldo en Drive",
    };
    const getStatus = (key, index) => {
        if (steps[key]) return 'success';
        const prevKey = Object.keys(stepLabels)[index - 1];
        if (index === 0 || (prevKey && steps[prevKey])) return 'in_progress';
        return 'pending';
    };
    return (
        <div className="p-4">
            <div className="flex flex-col items-center text-center mb-6">
                <Icon name="Loader" className="animate-spin text-blue-500 h-10 w-10" />
                <p className="mt-4 font-semibold text-lg text-gray-700">Procesando tu operación...</p>
                <p className="text-sm text-gray-500">¡Estamos avanzando! Por favor, no cierres la ventana. "Tiempo aproximado 30 segundos"</p>
            </div>
            <div className="space-y-3 border-t border-gray-200 pt-4">
                {Object.keys(stepLabels).map((key, index) => (
                    <ChecklistItem key={key} text={stepLabels[key]} status={getStatus(key, index)} />
                ))}
            </div>
        </div>
    );
};

const SuccessState = ({ successData }) => (
    <div className="text-center p-4">
        <Icon name="PartyPopper" className="text-green-500 h-12 w-12 mx-auto" />
        <p className="mt-4 font-semibold text-lg text-green-800">¡Operación Exitosa!</p>
        <p className="text-sm text-gray-600 mt-1 mb-4">
        El Trello de seguimiento se creara en unos momentos.
        </p>
        
        {/* Lógica definitiva para mostrar el link o el ID */}
        {successData.drive_folder_url ? (
            <a
                href={successData.drive_folder_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
                <Icon name="FolderKanban" size={16} />
                Abrir Carpeta de Drive
            </a>
        ) : (
             <div className="mt-4 text-left text-sm bg-gray-100 p-3 rounded-md">
                <p><strong>ID de Seguimiento:</strong></p>
                <p className="font-mono bg-gray-200 px-1 rounded break-all">{successData.tracking_id}</p>
            </div>
        )}
    </div>
);
const ErrorState = ({ error }) => (
    <div className="text-center p-4">
        <Icon name="ShieldAlert" className="text-red-500 h-12 w-12 mx-auto" />
        <p className="mt-4 font-semibold text-lg text-red-700">Ocurrió un Error</p>
        <div className="mt-2 text-sm text-red-700 bg-red-50 p-3 rounded-md">
            <p className="font-semibold">Motivo:</p>
            <p>{error || "No se pudo completar el proceso."}</p>
        </div>
    </div>
);


export const ProcessingModal = ({ isOpen, processState, onReset, onClose }) => {
    if (!isOpen) return null;
    const { isLoading, error, successData, steps = {} } = processState;
    const renderContent = () => {
        if (isLoading) return <LoadingState steps={steps} />;
        if (error) return <ErrorState error={error} />;
        if (successData) return <SuccessState successData={successData} />;
        return null;
    };
    return (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }}>
                <Card className="w-full max-w-md shadow-2xl">
                    <CardHeader>
                        <CardTitle iconName="Zap">Estado de la Operación</CardTitle>
                        <CardDescription>{isLoading ? "Aguarde mientras procesamos todo." : "El proceso ha finalizado."}</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <AnimatePresence mode="wait">
                            <motion.div key={isLoading ? 'loading' : (error ? 'error' : 'success')} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                                {renderContent()}
                            </motion.div>
                        </AnimatePresence>
                    </CardContent>
                    <CardFooter className="flex flex-col sm:flex-row gap-2">
                        {successData ? (
                            <>
                                <Button onClick={onReset} className="w-full sm:w-auto flex-1"><Icon name="PlusCircle" className="mr-2"/>Registrar Otra Operación</Button>
                            </>
                        ) : ( <Button onClick={onClose} className="w-full" disabled={isLoading}>{isLoading ? "Procesando..." : "Cerrar y Corregir"}</Button> )}
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
};