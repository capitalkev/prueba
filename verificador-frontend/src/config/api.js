// API configuration
export const API_BASE_URL = import.meta.env.PROD 
  ? 'https://orquestador-service-598125168090.southamerica-west1.run.app/api'
  : '/api';

export const API_SUBMIT_URL = import.meta.env.PROD
  ? 'https://orquestador-service-598125168090.southamerica-west1.run.app'
  : '';