import React, { useState, useEffect, useRef } from 'react';
import { CurrencyDollarIcon, ChevronDownIcon } from '../icons';
import { CURRENCIES } from '../constants';

/**
 * Selector desplegable con múltiples opciones de monedas
 */
const MultiCurrencySelector = ({ selectedCurrencies, onSelectionChange }) => {
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

    const handleCurrencyToggle = (currencyCode) => {
        const newSelection = selectedCurrencies.includes(currencyCode)
            ? selectedCurrencies.filter(code => code !== currencyCode)
            : [...selectedCurrencies, currencyCode];
        onSelectionChange(newSelection);
    };

    const getButtonLabel = () => {
        if (selectedCurrencies.length === 0 || selectedCurrencies.length === CURRENCIES.length) {
            return "Todas las monedas";
        }
        if (selectedCurrencies.length === 1) {
            return CURRENCIES.find(c => c.code === selectedCurrencies[0])?.name;
        }
        return `${selectedCurrencies.length} monedas seleccionadas`;
    };

    return (
        <div className="relative w-full md:w-64" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center justify-between w-full p-2 bg-white border border-gray-300 rounded-md shadow-sm text-left"
            >
                <div className="flex items-center min-w-0">
                    <CurrencyDollarIcon className="w-5 h-5 mr-3 text-green-600 flex-shrink-0" />
                    <p className="text-sm font-semibold text-gray-800 truncate">{getButtonLabel()}</p>
                </div>
                <ChevronDownIcon className={`h-5 w-5 text-gray-500 transition-transform ${isOpen ? 'transform rotate-180' : ''}`} />
            </button>
            {isOpen && (
                <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg flex flex-col">
                    <div className="p-2 border-b flex gap-2">
                        <button
                            onClick={() => onSelectionChange(CURRENCIES.map(c => c.code))}
                            className="text-xs text-blue-600 hover:underline"
                        >
                            Todas
                        </button>
                        <button
                            onClick={() => onSelectionChange([])}
                            className="text-xs text-blue-600 hover:underline"
                        >
                            Ninguna
                        </button>
                    </div>
                    <div className="overflow-y-auto">
                        {CURRENCIES.map(currency => (
                            <div
                                key={currency.code}
                                className="p-3 hover:bg-green-50 cursor-pointer flex items-center"
                                onClick={() => handleCurrencyToggle(currency.code)}
                            >
                                <input
                                    type="checkbox"
                                    checked={selectedCurrencies.includes(currency.code)}
                                    readOnly
                                    className="h-4 w-4 rounded border-gray-300 text-green-600 focus:ring-green-500 mr-3"
                                />
                                <div>
                                    <p className="text-sm font-medium text-gray-900">{currency.name}</p>
                                    <p className="text-xs text-gray-500">{currency.symbol}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MultiCurrencySelector;
