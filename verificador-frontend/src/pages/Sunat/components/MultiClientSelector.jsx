import React, { useState, useEffect, useRef } from 'react';
import { BuildingOfficeIcon, ChevronDownIcon } from '../icons';

/**
 * Selector desplegable con múltiples opciones de clientes
 */
const MultiClientSelector = ({ clients, selectedClientIds, onSelectionChange }) => {
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

    const handleClientToggle = (clientId) => {
        const newSelection = selectedClientIds.includes(clientId)
            ? selectedClientIds.filter(id => id !== clientId)
            : [...selectedClientIds, clientId];
        onSelectionChange(newSelection);
    };

    const getButtonLabel = () => {
        if (selectedClientIds.length === 0 || selectedClientIds.length === clients.length) {
            return "Todos los clientes";
        }
        if (selectedClientIds.length === 1) {
            return clients.find(c => c.id === selectedClientIds[0])?.name;
        }
        return `${selectedClientIds.length} clientes seleccionados`;
    };

    return (
        <div className="relative w-full md:w-96" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center justify-between w-full p-2 bg-white border border-gray-300 rounded-md shadow-sm text-left"
            >
                <div className="flex items-center min-w-0">
                    <BuildingOfficeIcon className="w-5 h-5 mr-3 text-blue-600 flex-shrink-0" />
                    <p className="text-sm font-semibold text-gray-800 truncate">{getButtonLabel()}</p>
                </div>
                <ChevronDownIcon className={`h-5 w-5 text-gray-500 transition-transform ${isOpen ? 'transform rotate-180' : ''}`} />
            </button>
            {isOpen && (
                <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-80 flex flex-col">
                    <div className="p-2 border-b flex gap-2">
                        <button
                            onClick={() => onSelectionChange(clients.map(c => c.id))}
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
                        {clients.map(client => (
                            <div
                                key={client.id}
                                className="p-3 hover:bg-blue-50 cursor-pointer flex items-center"
                                onClick={() => handleClientToggle(client.id)}
                            >
                                <input
                                    type="checkbox"
                                    checked={selectedClientIds.includes(client.id)}
                                    readOnly
                                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3"
                                />
                                <div>
                                    <p className="text-sm font-medium text-gray-900">{client.name}</p>
                                    <p className="text-xs text-gray-500">{client.ruc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MultiClientSelector;
