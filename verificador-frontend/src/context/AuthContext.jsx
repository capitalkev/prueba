import React, { createContext, useState, useEffect, useContext } from 'react';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebase';
import { Icon } from '../components/Icon';

// 1. Creamos el Contexto
const AuthContext = createContext();

// 2. Creamos el Proveedor del Contexto (aquí vivirá toda la lógica)
export const AuthProvider = ({ children }) => {
    const [firebaseUser, setFirebaseUser] = useState(null); // Para el objeto de Firebase
    const [currentUser, setCurrentUser] = useState(null);   // Para nuestro usuario del backend
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (user) => {
            setLoading(true);
            if (user) {
                setFirebaseUser(user);
                try {
                    const token = await user.getIdToken();
                    const response = await fetch('https://orquestador-service-598125168090.southamerica-west1.run.app/api/users/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });

                    if (!response.ok) {
                        await signOut(auth);
                        throw new Error('Usuario no autorizado.');
                    }
                    const backendUser = await response.json();
                    setCurrentUser(backendUser);
                } catch (error) {
                    console.error("Fallo al sincronizar con el backend:", error);
                    await signOut(auth); // Desloguear si hay error
                    setCurrentUser(null);
                    setFirebaseUser(null);
                }
            } else {
                setFirebaseUser(null);
                setCurrentUser(null);
            }
            setLoading(false);
        });

        return () => unsubscribe();
    }, []);
    
    // Componente de Carga para evitar flashes de contenido
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-neutral">
              <Icon name="Loader" className="animate-spin text-blue-600" size={48} />
            </div>
        );
    }

    // 3. Pasamos los valores al resto de la aplicación
    const value = { firebaseUser, currentUser, loading };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

// 4. Creamos un hook personalizado para consumir el contexto fácilmente
export const useAuth = () => {
    return useContext(AuthContext);
};