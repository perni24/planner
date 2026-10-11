# Sviluppi Futuri

Questo documento raccoglie idee e possibili evoluzioni non ancora pianificate.
Le voci presenti non sono attivita confermate e richiedono una valutazione prima
dell'implementazione.

## Interfaccia desktop con PyWebView

Valutare PyWebView per mostrare il frontend React in una finestra desktop nativa,
senza aprire una scheda del browser.

Possibili vantaggi:

- esperienza piu simile a un'applicazione desktop;
- finestra dedicata senza barra degli indirizzi;
- mantenimento dell'attuale frontend React e backend Starlette;
- soluzione generalmente piu leggera rispetto a Electron.

Aspetti da verificare:

- compatibilita e dipendenze richieste su Windows, Linux e macOS;
- integrazione con PyInstaller e GitHub Actions;
- gestione dell'avvio e dello spegnimento del backend;
- comportamento dei download, come il backup SQLite;
- firma e notarizzazione delle build macOS;
- disponibilita del runtime WebView2 sui sistemi Windows supportati.

Flusso ipotizzato:

```text
PlannerApp
  -> avvia il backend Starlette locale
  -> apre una finestra PyWebView
  -> carica http://127.0.0.1:8000
  -> arresta il backend alla chiusura della finestra
```

Prima di adottarlo conviene creare una prova separata dalla build principale e
confrontare dimensioni, stabilita e comportamento sui tre sistemi operativi.

## Sincronizzazione completa tramite eventi SSE

La sincronizzazione tramite Server-Sent Events e gia attiva per le modifiche fatte
dai tool MCP (`GET /api/events`, vedi `API_BACKEND.md`). Restano da valutare:

- far passare anche le route REST da service condivisi con MCP, cosi ogni modifica
  pubblica lo stesso evento indipendentemente dal client e piu schede aperte restano
  allineate;
- aggiungere eventi di eliminazione (`deleted`) e di cambio stato;
- includere negli eventi gli identificatori utili a ricaricare solo i dati
  interessati (per esempio `project_id` per le task);
- ricaricare i dati dopo una riconnessione SSE, perche gli eventi persi mentre la
  connessione era chiusa non vengono recuperati;
- gestire piu eventi ravvicinati nel frontend: `DataSyncContext` conserva solo
  l'ultimo evento ricevuto.
