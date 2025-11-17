// --- Configuración de la API ---
// URL del backend de SUNAT en Cloud Run (producción)
export const API_BASE_URL = 'https://crm-sunat-backend-598125168090.southamerica-west1.run.app';

// --- Estados de facturas ---
export const INVOICE_STATUSES = [
    'Sin gestión',
    'Gestionando',
    'Ganada',
    'Perdida'
];

// --- Motivos de pérdida (estado2) ---
export const LOSS_REASONS = [
    'Por Tasa',
    'Por Riesgo',
    'Deudor no califica',
    'Cliente no interesado',
    'Competencia',
    'Otro'
];

// --- Monedas disponibles ---
export const CURRENCIES = [
    { code: 'PEN', name: 'Soles (PEN)', symbol: 'S/' },
    { code: 'USD', name: 'Dólares (USD)', symbol: '$' }
];

// --- Colores por estado (Paleta profesional) ---
export const STATUS_COLORS = {
    'Sin gestión': 'text-slate-700',
    'Gestionando': 'text-amber-700',
    'Ganada': 'text-emerald-700',
    'Perdida': 'text-rose-700'
};
