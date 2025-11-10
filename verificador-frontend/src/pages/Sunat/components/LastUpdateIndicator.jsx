import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../constants';

/**
 * Componente que muestra la fecha y hora de la última actualización de las facturas
 */
export default function LastUpdateIndicator({ firebaseUser }) {
    const [lastUpdate, setLastUpdate] = useState(null);

    // Función para formatear la fecha en hora de Perú (UTC-5)
    const formatDate = (timestamp) => {
        if (!timestamp) return 'Cargando...';

        // TEST: Ver qué está llegando
        console.log('🕐 [LastUpdate] Timestamp recibido:', timestamp);

        const date = new Date(timestamp);
        console.log('🕐 [LastUpdate] Date object:', date);
        console.log('🕐 [LastUpdate] UTC String:', date.toUTCString());
        console.log('🕐 [LastUpdate] ISO String:', date.toISOString());

        // Opción 1: Intl.DateTimeFormat con timezone
        const formatter = new Intl.DateTimeFormat('es-PE', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            timeZone: 'America/Lima'
        });
        const formatted1 = formatter.format(date);
        console.log('🕐 [LastUpdate] Intl.DateTimeFormat:', formatted1);

        // Opción 2: toLocaleString con timezone
        const formatted2 = date.toLocaleString('es-PE', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            timeZone: 'America/Lima'
        });
        console.log('🕐 [LastUpdate] toLocaleString:', formatted2);

        // Opción 3: Manual (restar 5 horas)
        const peruDate = new Date(date.getTime());
        const formatted3 = peruDate.toLocaleString('es-PE', { hour12: false });
        console.log('🕐 [LastUpdate] Manual:', formatted3);

        return formatted2;
    };

    // Fetch última actualización
    useEffect(() => {
        const fetchLastUpdate = async () => {
            if (!firebaseUser) return;

            try {
                const token = await firebaseUser.getIdToken();
                const response = await fetch(`${API_BASE_URL}/api/ventas/ultima-actualizacion`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    const data = await response.json();
                    setLastUpdate(data.ultima_actualizacion);
                }
            } catch (err) {
                console.error('Error fetching last update:', err);
            }
        };

        fetchLastUpdate();
    }, [firebaseUser]);

    return (
        <span className="text-sm text-gray-600">
            Última actualización: {formatDate(lastUpdate)}
        </span>
    );
}
