// Em dev, fica vazio e as chamadas passam pelo proxy do Vite (vite.config.js) para localhost:8000.
// Em produção, VITE_API_URL aponta direto para a API hospedada (ex.: Render).
export const API_URL = import.meta.env.VITE_API_URL || ''
