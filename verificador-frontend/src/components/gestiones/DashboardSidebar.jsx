import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Icon } from '../Icon';
import { ProgressBar } from '../ui/ProgressBar'; // Necesitarás crear este componente

// Datos de ejemplo, idealmente vendrían del hook
const kpis = { verificadasSemana: 0, metaSemanal: 0 };
const logros = [
    { emoji: '🎯', titulo: 'Verificador Experto', descripcion: 'Completaste 20 verificaciones la semana pasada.' },
    { emoji: '⚡', titulo: 'Rápido y Eficaz', descripcion: 'Lograste un tiempo de respuesta promedio de 5h.' }
];

export const DashboardSidebar = () => (
    <>
        <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Icon name="CalendarCheck" className="text-red-500"/>Verificaciones de la Semana</CardTitle></CardHeader>
            <CardContent>
                <p className="text-3xl font-bold text-gray-900">{kpis.verificadasSemana}</p>
                <p className="text-sm text-gray-500">de {kpis.metaSemanal} operaciones</p>
                <ProgressBar value={kpis.verificadasSemana} max={kpis.metaSemanal} colorClass="bg-red-500" />
            </CardContent>
        </Card>
        <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Icon name="TrendingUp" className="text-green-600"/>Tu Rendimiento Histórico</CardTitle></CardHeader>
            <CardContent className="text-sm text-center">
                <p>Tiempo Prom. Verificación (este mes)</p>
                <p className="text-4xl font-bold text-green-600 my-1">0 Horas</p>
                <p className="font-semibold text-green-700">0% más rápido que el mes pasado.</p>
            </CardContent>
        </Card>
        {/* 
        <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Icon name="Award" className="text-yellow-500"/>Mis Logros Recientes</CardTitle></CardHeader>
            <CardContent className="space-y-3">
                {logros.map(logro => (
                    <div key={logro.titulo} className="flex items-center gap-3 text-sm">
                        <span className="text-2xl">{logro.emoji}</span>
                        <div>
                            <p className="font-semibold">{logro.titulo}</p>
                            <p className="text-xs text-gray-500">{logro.descripcion}</p>
                        </div>
                    </div>
                ))}
            </CardContent>
        </Card>
        */}
        
    </>
);