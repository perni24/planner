const BASE_URL = '/api'; // Sfrutta il proxy configurato in vite.config.js

/**
 * Definizione delle opzioni per la chiamata
 */
interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: any;
  headers?: Record<string, string>;
}

/**
 * Funzione CORE per gestire tutte le chiamate HTTP.
 * <T> è il tipo di dato che ci aspettiamo dal server.
 */
export async function apiCore<T>(
  endpoint: string, 
  { method = 'GET', body, headers }: ApiOptions = {}
): Promise<T> {
  
  // Costruiamo l'URL completo (es. /api/projects)
  const url = `${BASE_URL}${endpoint}`;

  // Configuriamo gli header base (sempre JSON)
  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers, // Permette di sovrascrivere o aggiungere header specifici
    },
  };

  // Se è presente un body, lo trasformiamo automaticamente in stringa JSON
  if (body) {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, config);

    // Gestione centralizzata degli errori di rete/HTTP
    if (!response.ok) {
      // Proviamo a estrarre il messaggio di errore dal server se presente
      const errorBody = await response.json().catch(() => ({}));
      const errorMessage = errorBody.detail || errorBody.message || `Errore ${response.status}: ${response.statusText}`;
      throw new Error(errorMessage);
    }

    // Se la risposta è vuota (204 No Content), restituiamo un oggetto vuoto
    if (response.status === 204) {
      return {} as T;
    }

    // Trasformiamo la risposta in un oggetto tipizzato <T>
    return await response.json() as T;

  } catch (error) {
    // Logghiamo l'errore in console per il debug
    console.error(`[API Error] ${method} ${url}:`, error);
    
    // Rilanciamo l'errore in modo che il componente React possa gestirlo (es. mostrare un alert)
    throw error;
  }
}
