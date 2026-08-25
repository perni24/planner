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

## Sincronizzazione frontend tramite Server-Sent Events

Valutare Server-Sent Events (SSE) per aggiornare il frontend quando i dati
vengono modificati dal server MCP o da altri client esterni.

Il frontend mantiene una connessione aperta verso un endpoint dedicato:

```text
GET /api/events
```

Dopo una modifica, il backend invia un evento con il tipo di operazione e gli
identificatori necessari:

```json
{
  "type": "task.updated",
  "project_id": 3,
  "task_id": 12
}
```

Il frontend riceve il segnale e ricarica soltanto i dati interessati, senza
eseguire un refresh completo della pagina.

Flusso ipotizzato:

```text
Tool MCP
  -> service condiviso
  -> repository
  -> SQLite
  -> pubblicazione evento SSE
  -> frontend React
  -> nuova chiamata API
  -> aggiornamento dello state
```

Le route REST e i tool MCP dovrebbero utilizzare gli stessi service, in modo
che ogni modifica produca la stessa notifica indipendentemente dal client che
l'ha richiesta.

Eventi iniziali da valutare:

- `area.created`, `area.updated` e `area.deleted`;
- `project.created`, `project.updated` e `project.deleted`;
- `task.created`, `task.updated` e `task.deleted`;
- `task.status_changed`.

Nel frontend la connessione puo essere gestita con `EventSource`. In base al
tipo di evento vengono richiamate funzioni come `reloadAreas()`,
`loadProjects()` o `loadTasks()`.

SSE e preferibile al polling perche invia richieste solo quando ci sono
modifiche, ed e piu semplice di WebSocket per una comunicazione principalmente
dal backend verso il frontend.
