import { test } from "./types/test";

export async function getTest(): Promise<test | null> {
  try {
    const response = await fetch(`/api/`);

    // 1. Controlliamo se la risposta è valida (status 200-299)
    if (!response.ok) {
      // Se è un 404 o 500, forziamo l'uscita verso il catch
      throw new Error(`Errore del server: ${response.status}`);
    }

    const data: test = await response.json();
    return data;

  } catch (error) {
    // 2. Gestiamo qui sia gli errori di rete che quelli forzati da noi
    console.error("Si è verificato un problema:", error);
    return null; 
  }
}