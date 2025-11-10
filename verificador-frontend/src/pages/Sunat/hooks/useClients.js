import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../constants';
import { signOut } from 'firebase/auth';
import { auth } from '../../../firebase';

/**
 * Hook para cargar la lista de clientes/empresas (de todos los períodos)
 * Acepta filtro opcional de usuarios para mostrar solo clientes de esos usuarios
 */
export const useClients = (firebaseUser, selectedUserEmails = [], users = []) => {
    const [clients, setClients] = useState([]);
    const [errorData, setErrorData] = useState(null);

    useEffect(() => {
        if (!firebaseUser) return;

        const fetchClientes = async () => {
            setErrorData(null);

            // Calcular si debemos filtrar por usuarios
            const totalUserOptions = users.length + 1; // +1 por "Sin asignar"
            const shouldFilterUsers = selectedUserEmails.length > 0 &&
                                     (users.length === 0 || selectedUserEmails.length < totalUserOptions);

            try {
                const token = await firebaseUser.getIdToken();

                // Construir URL con filtro de usuarios si aplica
                let url = `${API_BASE_URL}/api/ventas/empresas`;

                if (shouldFilterUsers) {
                    const params = selectedUserEmails.map(email => `usuario_emails=${email}`).join('&');
                    url += `?${params}`;
                }

                const response = await fetch(url, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.status === 401 || response.status === 403) {
                    console.error("Error 401/403 - Forzando logout.");
                    await signOut(auth);
                    throw new Error(`Error ${response.status}: No autorizado.`);
                }

                if (!response.ok) {
                    throw new Error(`Error ${response.status} del servidor.`);
                }

                const data = await response.json();
                const clientsFormatted = data.map(e => ({ id: e.ruc, name: e.razon_social, ruc: e.ruc }));
                console.log('🏢 [useClients] Loaded clients:', {
                    count: clientsFormatted.length,
                    filtered_by_users: shouldFilterUsers,
                    selected_users: selectedUserEmails.length,
                    url
                });
                setClients(clientsFormatted);
            } catch (err) {
                console.error('Error fetching clientes:', err);
                setErrorData(err.message);
            }
        };

        fetchClientes();
    }, [firebaseUser, selectedUserEmails, users.length]);

    return { clients, errorData };
};
