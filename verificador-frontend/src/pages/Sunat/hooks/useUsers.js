import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../constants';
import { signOut } from 'firebase/auth';
import { auth } from '../../../firebase';

/**
 * Hook para cargar la lista de usuarios no-admin
 * Usado para el selector de filtro por usuario
 */
export const useUsers = (firebaseUser) => {
    const [users, setUsers] = useState([]);
    const [errorData, setErrorData] = useState(null);

    useEffect(() => {
        if (!firebaseUser) return;

        const fetchUsers = async () => {
            setErrorData(null);
            try {
                const token = await firebaseUser.getIdToken();
                const response = await fetch(`${API_BASE_URL}/api/usuarios/no-admin`, {
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
                const usersFormatted = data.map(u => ({
                    email: u.email,
                    nombre: u.nombre,
                    rol: u.rol
                }));
                setUsers(usersFormatted);
            } catch (err) {
                console.error('Error fetching users:', err);
                setErrorData(err.message);
            }
        };

        fetchUsers();
    }, [firebaseUser]);

    return { users, errorData };
};
