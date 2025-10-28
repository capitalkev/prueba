// --- Configuración de la API ---
// URL del backend de SUNAT en Cloud Run (producción)
export const API_BASE_URL = 'https://sunat-backend-598125168090.southamerica-west1.run.app';

// --- Estados de facturas ---
export const INVOICE_STATUSES = [
    'Sin Gestión',
    'Tasa',
    'Riesgo',
    'No Califica',
    'Ganada',
    'Perdida sin Gestión'
];

// --- Monedas disponibles ---
export const CURRENCIES = [
    { code: 'PEN', name: 'Soles (PEN)', symbol: 'S/' },
    { code: 'USD', name: 'Dólares (USD)', symbol: '$' }
];

// --- Colores por estado (Paleta profesional) ---
export const STATUS_COLORS = {
    'Sin Gestión': 'text-slate-700',
    'Tasa': 'text-blue-700',
    'Riesgo': 'text-amber-700',
    'No Califica': 'text-stone-700',
    'Ganada': 'text-emerald-700',
    'Perdida sin Gestión': 'text-rose-700'
};
