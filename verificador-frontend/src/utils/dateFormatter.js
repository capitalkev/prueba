// src/utils/dateFormatter.js

import { formatInTimeZone } from 'date-fns-tz';

// La zona horaria de Perú
const timeZone = 'America/Lima';

export const formatInPeruTimeZone = (dateString, formatString = 'dd/MM/yyyy, hh:mm a') => {
  if (!dateString) return '';
  try {
    // Esta función convierte y formatea la fecha UTC a la zona horaria de Lima en un solo paso.
    return formatInTimeZone(new Date(dateString), timeZone, formatString);
  } catch (error) {
    console.error("Error formatting date:", error);
    return "Fecha inválida";
  }
};