import React from 'react';
import { Button } from '../ui/Button';
import { Icon } from '../Icon';
import { useAuth } from '../../context/AuthContext';

export const Header = ({ handleLogout }) => {
    const { firebaseUser } = useAuth();

    return (
        <header className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-8">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Centro de Verificaciones</h1>
                <p className="text-lg text-gray-500">Bienvenido de vuelta, {firebaseUser?.displayName?.split(' ')[0] || 'Usuario'} 👋</p>
            </div>
            <div className="flex items-center gap-3">
                <Button variant="outline" size="sm" iconName="LogOut" onClick={handleLogout}>Cerrar Sesión</Button>
            </div>
        </header>
    );
};