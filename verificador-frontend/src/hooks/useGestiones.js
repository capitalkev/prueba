import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../config/api';

export const useGestiones = () => {
    const { firebaseUser } = useAuth();
    
    const [operaciones, setOperaciones] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    const [activeFilter, setActiveFilter] = useState('En Proceso');
    const [activeGestionId, setActiveGestionId] = useState(null);
    const [showSuccessPopup, setShowSuccessPopup] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');
    
    const [isAdelantoModalOpen, setIsAdelantoModalOpen] = useState(false);
    const [selectedAdelantoOp, setSelectedAdelantoOp] = useState(null);
    const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
    const [selectedOpToAssign, setSelectedOpToAssign] = useState(null);
    const [analysts, setAnalysts] = useState([]);
    
    const [isRequestVerificationModalOpen, setIsRequestVerificationModalOpen] = useState(false);
    const [selectedVerificationOp, setSelectedVerificationOp] = useState(null);

    const fetchOperaciones = useCallback(async () => {
        if (!firebaseUser) {
            console.log("[useGestiones] No hay usuario de Firebase, deteniendo fetch.");
            setIsLoading(false);
            return;
        }
        
        setIsLoading(true);
        setError(null);
        console.log("[useGestiones] Iniciando fetch de operaciones...");

        try {
            const token = await firebaseUser.getIdToken(); 
            const response = await fetch(`${API_BASE_URL}/gestiones/operaciones`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            console.log(`[useGestiones] Respuesta del backend recibida con status: ${response.status}`);

            if (!response.ok) {
                const errData = await response.json();
                console.error("[useGestiones] Error en la respuesta del backend:", errData);
                throw new Error(errData.detail || 'No se pudo obtener la data de gestiones.');
            }

            const data = await response.json();
            console.log("[useGestiones] Datos recibidos del backend:", data);
            setOperaciones(data);

        } catch (err) {
            console.error("[useGestiones] Error capturado en el bloque catch:", err);
            setError(err.message);
        } finally {
            console.log("[useGestiones] Fetch finalizado. `isLoading` se establecerá en false.");
            setIsLoading(false);
        }
    }, [firebaseUser]);

    const fetchAnalysts = useCallback(async () => {
        if (!firebaseUser) return;
        try {
            const token = await firebaseUser.getIdToken();
            const response = await fetch(`${API_BASE_URL}/users/analysts`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudo cargar la lista de analistas.');
            const data = await response.json();
            setAnalysts(data);
        } catch (err) {
            console.error(err);
        }
    }, [firebaseUser]);

    useEffect(() => {
        fetchOperaciones();
        fetchAnalysts();
    }, [fetchOperaciones, fetchAnalysts]);

    const filteredData = useMemo(() => {
        if (!operaciones) return [];
        const enProceso = operaciones.filter(op => op.estadoOperacion !== 'Completada' && !op.adelantoExpress);
        const enAdelanto = operaciones.filter(op => op.estadoOperacion !== 'Completada' && op.adelantoExpress);
        if (activeFilter === 'En Proceso') return enProceso;
        if (activeFilter === 'Adelanto Express') return enAdelanto;
        return operaciones.filter(op => op.estadoOperacion !== 'Completada');
    }, [activeFilter, operaciones]);
    
    const showPopup = (message) => {
        setSuccessMessage(message);
        setShowSuccessPopup(true);
        setTimeout(() => setShowSuccessPopup(false), 3000);
    };

    // Función auxiliar para obtener el token de forma segura
    const withToken = useCallback(async (callback) => {
        if (!firebaseUser) {
            setError("Usuario no autenticado para realizar esta acción.");
            return;
        }
        try {
            const token = await firebaseUser.getIdToken();
            return await callback(token);
        } catch (error) {
            console.error("Error obteniendo token o ejecutando acción:", error);
            setError("Tu sesión puede haber expirado. Por favor, recarga la página.");
        }
    }, [firebaseUser]);

    const handleSaveGestion = useCallback(async (opId, gestionData) => {
        console.log('Guardando gestión:', gestionData);
        
        // Primero guardar en el servidor para obtener el ID real
        try {
            await withToken(async (token) => {
                const response = await fetch(`${API_BASE_URL}/operaciones/${opId}/gestiones`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify(gestionData),
                });
                
                if (!response.ok) throw new Error('La sincronización con el servidor falló.');
                
                const savedGestion = await response.json();
                console.log('Gestión guardada en servidor:', savedGestion);
                
                // Actualizar con los datos reales del servidor (incluyendo ID)
                const displayName = firebaseUser?.displayName || 'Usuario';
                const nuevaGestionLocal = {
                    id: savedGestion.id,
                    ...gestionData,
                    fecha: savedGestion.fecha_creacion || new Date().toISOString(),
                    analista: displayName.split(' ')[0] || 'Tú',
                };
                
                console.log('Agregando gestión local:', nuevaGestionLocal);

                setOperaciones(prevOps => prevOps.map(op =>
                    op.id === opId ? { ...op, gestiones: [...op.gestiones, nuevaGestionLocal] } : op
                ));
                
                showPopup("¡Gestión guardada con éxito!");
            });
        } catch (error) {
            console.error("Error al sincronizar la gestión:", error);
            setError("Falló al guardar la gestión. Por favor, recargue la página.");
        }
        
        setActiveGestionId(null);
    }, [withToken, firebaseUser]);
    
    const handleFacturaCheck = useCallback(async (opId, folio, nuevoEstado) => {
        setOperaciones(prevOps => prevOps.map(op => {
            if (op.id === opId) {
                const nuevasFacturas = op.facturas.map(f =>
                    f.folio === folio ? { ...f, estado: nuevoEstado } : f
                );
                const algunaRechazada = nuevasFacturas.some(f => f.estado === 'Rechazada');
                const todasVerificadas = nuevasFacturas.every(f => f.estado === 'Verificada');
                let nuevoEstadoOp = 'En Verificación';
                if (algunaRechazada) nuevoEstadoOp = 'Discrepancia';
                else if (todasVerificadas) nuevoEstadoOp = 'pendiente';
                
                return { ...op, facturas: nuevasFacturas, estadoOperacion: nuevoEstadoOp };
            }
            return op;
        }));

        withToken(async (token) => {
            await fetch(`${API_BASE_URL}/operaciones/${opId}/facturas/${folio}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ estado: nuevoEstado }),
            });
        }).catch(error => {
            console.error("Error al sincronizar el estado de la factura:", error);
            setError("Falló la actualización de la factura. Por favor, recargue la página.");
        });
    }, [withToken]);

    const handleOpenAdelantoModal = (operation) => {
        setSelectedAdelantoOp(operation);
        setIsAdelantoModalOpen(true);
    };

    const handleConfirmAdelanto = useCallback(async (justification) => {
        if (!selectedAdelantoOp) return;
        withToken(async (token) => {
            await fetch(`${API_BASE_URL}/operaciones/${selectedAdelantoOp.id}/adelanto-express`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ justificacion: justification }),
            });
            await fetchOperaciones();
            setIsAdelantoModalOpen(false);
        }).catch(() => setError("No se pudo mover la operación a Adelanto Express."));
    }, [withToken, selectedAdelantoOp, fetchOperaciones]);

    const handleCompleteOperation = useCallback(async (opId) => {
        const originalOperaciones = operaciones;
        setOperaciones(prevOps => prevOps.filter(op => op.id !== opId));

        withToken(async (token) => {
            const response = await fetch(`${API_BASE_URL}/operaciones/${opId}/completar`, {
                method: 'PATCH',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('La comunicación con el servidor falló.');
            showPopup("Operación completada y archivada.");
        }).catch(() => {
            setError("No se pudo completar la operación. La tarea ha sido restaurada.");
            setOperaciones(originalOperaciones);
        });
    }, [withToken, operaciones]);

    const handleDeleteGestion = useCallback(async (gestionId, opId) => {
        
        const originalOperaciones = operaciones;
        setOperaciones(prevOps => prevOps.map(op => {
            if (op.id === opId) {
                return {
                    ...op,
                    gestiones: op.gestiones.filter(g => g.id !== gestionId)
                };
            }
            return op;
        }));

        showPopup("Gestión eliminada con éxito!");

        // Llamada al backend
        withToken(async (token) => {
            const response = await fetch(`${API_BASE_URL}/gestiones/${gestionId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudo eliminar la gestión.');
        }).catch(error => {
            console.error("Error al eliminar la gestión:", error);
            setError("No se pudo eliminar la gestión. Se ha restaurado.");
            // Restaurar el estado original en caso de error
            setOperaciones(originalOperaciones);
        });
    }, [withToken, operaciones]);

    const handleOpenAssignModal = (operation) => {
        setSelectedOpToAssign(operation);
        setIsAssignModalOpen(true);
    };

    const handleConfirmAssignment = async (opId, analystEmail) => {
        withToken(async (token) => {
            await fetch(`${API_BASE_URL}/operaciones/${opId}/assign?assignee_email=${analystEmail}`, {
                method: 'PATCH',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setOperaciones(prevOps => prevOps.map(op => 
                op.id === opId 
                ? { ...op, analistaAsignado: analysts.find(a => a.email === analystEmail) }
                : op
            ));
            showPopup("Operación asignada correctamente.");
        }).catch(() => setError("No se pudo asignar la operación."));
    };

    const handleOpenRequestVerificationModal = (operation) => {
        console.log('🔥 handleOpenRequestVerificationModal called with:', operation);
        setSelectedVerificationOp(operation);
        setIsRequestVerificationModalOpen(true);
        console.log('Modal state should be open now');
    };

    const handleSendVerificationEmails = useCallback(async ({ operationId, emails, customMessage }) => {
        return await withToken(async (token) => {
            const response = await fetch(`${API_BASE_URL}/operaciones/${operationId}/send-verification`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'Authorization': `Bearer ${token}` 
                },
                body: JSON.stringify({ 
                    emails: emails,
                    customMessage: customMessage
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al enviar correos de verificación');
            }
            
            const result = await response.json();
            showPopup("Correos de verificación enviados exitosamente.");
            setIsRequestVerificationModalOpen(false);
            return result;
        });
    }, [withToken]);

    // Devolvemos el estado y las funciones que los componentes necesitan
    return {
        isLoading,
        error,
        filteredData,
        activeFilter,
        setActiveFilter,
        activeGestionId,
        setActiveGestionId,
        showSuccessPopup,
        successMessage,
        isAdelantoModalOpen,
        setIsAdelantoModalOpen,
        selectedAdelantoOp,
        analysts,
        isAssignModalOpen,
        setIsAssignModalOpen,
        selectedOpToAssign,
        isRequestVerificationModalOpen,
        setIsRequestVerificationModalOpen,
        selectedVerificationOp,
        handleSaveGestion,
        handleFacturaCheck,
        handleOpenAdelantoModal,
        handleConfirmAdelanto,
        handleCompleteOperation,
        handleOpenAssignModal,
        handleConfirmAssignment,
        handleDeleteGestion,
        handleOpenRequestVerificationModal,
        handleSendVerificationEmails
    };
};