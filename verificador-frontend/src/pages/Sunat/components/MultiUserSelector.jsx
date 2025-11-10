import React, { useState, useEffect, useRef } from 'react';
import { ChevronDownIcon } from '../icons';

/**
 * Selector desplegable con múltiples opciones de usuarios
 * Filtra solo usuarios no-admin
 */
const MultiUserSelector = ({ users, selectedUserEmails, onSelectionChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleUserToggle = (email) => {
        const newSelection = selectedUserEmails.includes(email)
            ? selectedUserEmails.filter(e => e !== email)
            : [...selectedUserEmails, email];

        console.log('🎯 [MultiUserSelector] User toggle:', {
            email,
            was_selected: selectedUserEmails.includes(email),
            old_selection: selectedUserEmails,
            new_selection: newSelection
        });

        onSelectionChange(newSelection);
    };

    const getButtonLabel = () => {
        // Total de opciones incluye usuarios + "Sin asignar"
        const totalOptions = users.length + 1;

        if (selectedUserEmails.length === 0 || selectedUserEmails.length === totalOptions) {
            return "Todos los usuarios";
        }
        if (selectedUserEmails.length === 1) {
            if (selectedUserEmails[0] === "UNASSIGNED") {
                return "Sin asignar";
            }
            return users.find(u => u.email === selectedUserEmails[0])?.nombre;
        }
        return `${selectedUserEmails.length} usuarios seleccionados`;
    };

    return (
        <div className="relative w-full md:w-64" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center justify-between w-full p-2 bg-white border border-gray-300 rounded-md shadow-sm text-left"
            >
                <div className="flex items-center min-w-0">
                    <svg className="w-5 h-5 mr-3 text-purple-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <p className="text-sm font-semibold text-gray-800 truncate">{getButtonLabel()}</p>
                </div>
                <ChevronDownIcon className={`h-5 w-5 text-gray-500 transition-transform ${isOpen ? 'transform rotate-180' : ''}`} />
            </button>
            {isOpen && (
                <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg flex flex-col max-h-64 overflow-hidden">
                    <div className="p-2 border-b flex gap-2">
                        <button
                            onClick={() => onSelectionChange(['UNASSIGNED', ...users.map(u => u.email)])}
                            className="text-xs text-blue-600 hover:underline"
                        >
                            Todos
                        </button>
                        <button
                            onClick={() => onSelectionChange([])}
                            className="text-xs text-blue-600 hover:underline"
                        >
                            Ninguno
                        </button>
                    </div>
                    <div className="overflow-y-auto">
                        {/* Opción especial: Sin asignar */}
                        <div
                            className="p-3 hover:bg-purple-50 cursor-pointer flex items-center"
                            onClick={() => handleUserToggle('UNASSIGNED')}
                        >
                            <input
                                type="checkbox"
                                checked={selectedUserEmails.includes('UNASSIGNED')}
                                readOnly
                                className="h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500 mr-3"
                            />
                            <div>
                                <p className="text-sm font-medium text-gray-900">Sin asignar</p>
                                <p className="text-xs text-gray-500">Facturas sin usuario</p>
                            </div>
                        </div>
                        {/* Usuarios existentes */}
                        {users.map(user => (
                            <div
                                key={user.email}
                                className="p-3 hover:bg-purple-50 cursor-pointer flex items-center"
                                onClick={() => handleUserToggle(user.email)}
                            >
                                <input
                                    type="checkbox"
                                    checked={selectedUserEmails.includes(user.email)}
                                    readOnly
                                    className="h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500 mr-3"
                                />
                                <div>
                                    <p className="text-sm font-medium text-gray-900">{user.nombre}</p>
                                    <p className="text-xs text-gray-500">{user.email}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MultiUserSelector;
