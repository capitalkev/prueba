import React from 'react';

/**
 * Componente para mostrar una métrica con título, valor y subvalor opcional
 */
const MetricCard = ({ title, value, subValue, children }) => (
    <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        <p className="text-2xl font-bold text-gray-800 mt-1">{value}</p>
        {subValue && <p className="text-sm text-gray-500">{subValue}</p>}
        {children}
    </div>
);

export default MetricCard;
