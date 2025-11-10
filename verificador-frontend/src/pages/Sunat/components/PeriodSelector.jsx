import React, { useState, useEffect, useRef } from 'react';
import { CalendarDaysIcon, ChevronDownIcon } from '../icons';

/**
 * Selector de período de tiempo
 * Soporta presets (últimos 5/15/30 días, mes actual) y rango personalizado
 */
const PeriodSelector = ({ filter, onFilterChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [customStart, setCustomStart] = useState('');
    const [customEnd, setCustomEnd] = useState('');
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

    const handlePreset = (preset) => {
        onFilterChange(preset);
        setIsOpen(false);
    };

    const handleCustomApply = () => {
        if (customStart && customEnd) {
            onFilterChange({ type: 'custom', start: customStart, end: customEnd });
            setIsOpen(false);
        }
    };

    const PRESETS = [
        { key: '5days', label: 'Últimos 5 días' },
        { key: '15days', label: 'Últimos 15 días' },
        { key: '30days', label: 'Últimos 30 días' },
        { key: 'thisMonth', label: 'Mes en curso' },
    ];

    const currentLabel = PRESETS.find(p => p.key === filter.type)?.label || `Del ${filter.start} al ${filter.end}`;

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-2 text-sm rounded-md bg-white border border-gray-300 font-semibold text-gray-700"
            >
                <CalendarDaysIcon />
                <span>{currentLabel}</span>
                <ChevronDownIcon className="w-4 h-4" />
            </button>
            {isOpen && (
                <div className="absolute z-20 mt-1 w-72 bg-white border border-gray-200 rounded-md shadow-lg right-0">
                    <div className="p-2 space-y-1">
                        {PRESETS.map(p => (
                            <button
                                key={p.key}
                                onClick={() => handlePreset({ type: p.key })}
                                className="w-full text-left text-sm px-3 py-1.5 rounded-md hover:bg-gray-100"
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                    <div className="border-t border-gray-200 p-2 space-y-2">
                        <p className="text-sm font-semibold px-1">Personalizado</p>
                        <div className="flex items-center gap-2">
                            <input
                                type="date"
                                value={customStart}
                                onChange={e => setCustomStart(e.target.value)}
                                className="w-full text-xs p-1 border-gray-300 rounded-md"
                            />
                            <input
                                type="date"
                                value={customEnd}
                                onChange={e => setCustomEnd(e.target.value)}
                                className="w-full text-xs p-1 border-gray-300 rounded-md"
                            />
                        </div>
                        <button
                            onClick={handleCustomApply}
                            className="w-full text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 py-1.5 px-4 rounded-md"
                        >
                            Aplicar
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PeriodSelector;
