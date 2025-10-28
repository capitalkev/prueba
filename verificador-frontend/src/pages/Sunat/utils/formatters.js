/**
 * Formatea un valor numérico como moneda
 * @param {number} value - Valor a formatear
 * @param {string} currency - Código de moneda ('PEN' o 'USD')
 * @returns {string} Valor formateado como moneda
 */
export const formatCurrency = (value, currency = 'PEN') => {
    const currencyCode = currency === 'USD' ? 'USD' : 'PEN';
    return new Intl.NumberFormat('es-PE', {
        style: 'currency',
        currency: currencyCode,
        currencyDisplay: 'narrowSymbol'
    }).format(value);
};

/**
 * Formatea un período YYYYMM a texto legible
 * @param {string} periodo - Período en formato YYYYMM
 * @returns {string} Período formateado (ej: "Octubre 2025")
 */
export const formatPeriodDisplay = (periodo) => {
    const year = periodo.substring(0, 4);
    const month = periodo.substring(4, 6);
    const monthNames = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
};
