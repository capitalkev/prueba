import React from 'react';
import { formatCurrency } from '../utils/formatters';

/**
 * Tarjeta individual de KPI
 */
const KPICard = ({ title, mainValue, subValue, children, isLast }) => (
    <div className={`flex-1 p-4 text-center flex flex-col justify-between ${!isLast ? 'border-r border-gray-300' : ''}`}>
        <div>
            <h3 className="text-sm font-semibold text-gray-600">{title}</h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">{mainValue}</p>
            {subValue && <p className="text-xs text-gray-500 mt-1">{subValue}</p>}
        </div>
        {children}
    </div>
);

/**
 * Dashboard de indicadores clave de rendimiento (KPIs)
 * Muestra métricas separadas por moneda (PEN/USD) en una línea horizontal
 */
const KPIDashboard = ({ metrics }) => (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="flex flex-col md:flex-row">
            {/* Performance de Cierres PEN */}
            <KPICard
                title={`Performance de Cierres (PEN)`}
                mainValue={`${metrics.PEN.winPercentage.toFixed(1)}%`}
                subValue={`${formatCurrency(metrics.PEN.montoGanado, 'PEN')} de ${formatCurrency(metrics.PEN.totalFacturado, 'PEN')}`}
            >
                <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                    <div
                        className="bg-gradient-to-r from-green-400 to-emerald-600 h-2 rounded-full"
                        style={{ width: `${metrics.PEN.winPercentage}%` }}
                    ></div>
                </div>
            </KPICard>

            {/* Pipeline Activo PEN */}
            <KPICard
                title={`Pipeline Activo (PEN)`}
                mainValue={formatCurrency(metrics.PEN.montoDisponible, 'PEN')}
                subValue="Monto disponible para factorizar"
            />

            {/* Performance de Cierres USD */}
            <KPICard
                title={`Performance de Cierres (USD)`}
                mainValue={`${metrics.USD.winPercentage.toFixed(1)}%`}
                subValue={`${formatCurrency(metrics.USD.montoGanado, 'USD')} de ${formatCurrency(metrics.USD.totalFacturado, 'USD')}`}
            >
                <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                    <div
                        className="bg-gradient-to-r from-green-400 to-emerald-600 h-2 rounded-full"
                        style={{ width: `${metrics.USD.winPercentage}%` }}
                    ></div>
                </div>
            </KPICard>

            {/* Pipeline Activo USD */}
            <KPICard
                title={`Pipeline Activo (USD)`}
                mainValue={formatCurrency(metrics.USD.montoDisponible, 'USD')}
                subValue="Monto disponible para factorizar"
                isLast={true}
            />
        </div>
    </div>
);

export default KPIDashboard;
