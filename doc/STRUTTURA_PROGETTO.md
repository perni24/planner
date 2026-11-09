# Struttura del Progetto

Le cartelle e i file principali. Per i dettagli fa fede il codice.

## Root

- `backend/`: backend Python, API, server MCP, database, build portable.
- `frontend/`: interfaccia React/Vite.
- `doc/`: documentazione (`GUIDA_SVILUPPO.md` per iniziare, `TODO.md` per le
  attivita aperte, `SVILUPPI_FUTURI.md` per le idee).
- `.github/workflows/release-build.yml`: build Windows e Linux e GitHub Release sui tag `v*`.
- `AGENTS.md`: istruzioni per gli agenti AI.
- `THIRD_PARTY_NOTICES.md`: componenti di terze parti e loro licenze; copiato nella build.
- `LICENSE`: GNU GPL v3.

## Backend

| Percorso | Contenuto |
|---|---|
| `main.py` | entry point: prepara runtime e database, avvia Uvicorn in un thread e la finestra PyWebView |
| `config.py` | ambiente, percorsi (sviluppo o PyInstaller), host, porta, versione, renderer, timeout |
| `schema.sql` | schema SQLite, trigger, vista e dati iniziali |
| `db/db.py`, `db/migration_runner.py`, `db/migrations/` | connessioni, creazione del DB, migrazioni e backup |
| `db/repositories/` | SQL per entita (`area_repo`, `project_repo`, `task_repo`, `setting_repo`) e per MCP (`mcp_repo`) |
| `routes/` | endpoint REST; `api.py` li monta alla radice e sotto `/api` |
| `integration/mcp/` | server MCP, registrazione dei tool e modelli Pydantic |
| `services/mcp_service.py` | validazione e logica dei tool MCP |
| `services/event_service.py` | code degli eventi SSE |
| `services/operation_control.py`, `app_lifecycle.py`, `middleware/shutdown_guard.py` | arresto ordinato e scadenze delle operazioni |
| `services/desktop_error_service.py` | log rotanti e dialoghi di errore desktop |
| `services/locale_service.py`, `locales/` | dizionari lingua e fallback |
| `services/update_service.py` | controllo della release piu recente su GitHub |
| `validators/` | validazione di ID, testi e impostazioni |
| `middleware/origin_guard.py` | blocco delle scritture da altri siti (CSRF) |
| `build_portable.py` | build frontend + PyInstaller, riduzione del pacchetto Linux, verifica del contenuto |
| `build_licenses.py` | raccolta e verifica dei testi di licenza nella build |
| `qtwebengine_notices.py`, `qt_notices.py` | generazione degli avvisi Chromium e dei moduli Qt dai sorgenti ufficiali |
| `third_party_licenses/` | testi di licenza salvati nel repository (WebView2 SDK, Chromium, Qt, ICU) |
| `windows/PlannerApp.exe.config` | configurazione .NET copiata accanto all'eseguibile Windows |
| `requirements.txt`, `requirements-dev.txt` | dipendenze di runtime e strumenti di sviluppo/build |
| `test/` | test `unittest` (`test_*.py`) e richieste manuali (`*.http`) |

## Frontend (`frontend/src/`)

| Percorso | Contenuto |
|---|---|
| `main.jsx`, `App.jsx` | avvio e router (`/`, `/tasks/:projectId`, `/settings`, `/calendar`) |
| `api.ts`, `apiCore.ts`, `types/` | tutte le chiamate HTTP e i tipi delle risposte |
| `pages/` | `Project.jsx`, `Tasks.jsx`, `Setting.jsx`, `Calendar.jsx` (segnaposto) |
| `routes/` | le route di progetti e task usano una `key` per azzerare dati e modali al cambio di area o progetto |
| `hooks/useLatestRead.js`, `utils/latestRead.js` | letture annullabili: applicano solo la risposta dell'ultima richiesta per pagina o risorsa |
| `utils/areaState.js` | stato dell'elenco delle aree, selezione ed errori di ricaricamento |
| `components/` | layout, card, modali, toast, impostazioni MCP |
| `context/` | provider globali (aree, impostazioni, tema, lingua, toast, eventi SSE) composti in `AppProviders.jsx` |
| `index.css` | Tailwind e colori dei temi |
| `assets/icons/` | icone SVG |

Le scritture sono nelle pagine (`Project.jsx`, `Tasks.jsx`) e in `AreaProvider`;
modali e card ricevono callback (vedi `AGENTS.md`).

Caricamento iniziale, ricaricamento dopo un salvataggio ed eventi SSE condividono
lo stesso controllo delle letture. I dati del progetto e la lista delle task si
caricano indipendentemente; una risposta superata non sostituisce quella piu
recente. `npm test` da `frontend/` verifica i casi di risposta fuori ordine e
abbandono della pagina con il runner integrato di Node, senza dipendenze nuove.

`AreaSwitcher` conserva l'ultimo elenco se una lettura delle aree fallisce e
mostra un avviso localizzato con `Riprova`, anche se manca il primo elenco. Dopo
una scrittura riuscita, un errore di lettura non viene trattato come salvataggio
fallito. Un'area gia eliminata viene tolta subito dall'elenco locale; il prossimo
caricamento riuscito riallinea elenco e selezione e rimuove l'avviso.

## Cartelle generate (non tracciate)

- `frontend/node_modules/`, `frontend/dist/`
- `backend/.venv/`, `backend/build/`, `backend/dist/`
- `backend/db/`: in sviluppo `planner.db`, `migration_backups/`, `logs/`, `webview/`
