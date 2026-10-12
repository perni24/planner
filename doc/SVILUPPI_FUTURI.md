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

- pubblicare gli eventi anche dalle route REST (con `event_service.publish()` dopo
  ogni modifica), cosi piu schede aperte restano allineate. Le route REST e i tool
  MCP restano separati: le prime lavorano su un elemento alla volta, i secondi in
  blocco, con validazioni e messaggi diversi;
- aggiungere eventi di eliminazione (`deleted`) e di cambio stato;
- includere negli eventi gli identificatori utili a ricaricare solo i dati
  interessati (per esempio `project_id` per le task);
- ricaricare i dati dopo una riconnessione SSE, perche gli eventi persi mentre la
  connessione era chiusa non vengono recuperati;
- gestire piu eventi ravvicinati nel frontend: `DataSyncContext` conserva solo
  l'ultimo evento ricevuto.

## Regole condivise tra REST e MCP

Con REST e MCP separati, le regole sui dati vanno scritte su entrambi i lati e
rischiano di divergere (oggi MCP impedisce le subtask di subtask, la REST no; il
controllo "la task ha subtask?" esiste sia in `task_repo` sia in `mcp_repo`).

Valutare di raccogliere queste regole in poche funzioni condivise, usate sia dalle
route sia da `mcp_service`, lasciando separati i flussi e i messaggi di errore.
