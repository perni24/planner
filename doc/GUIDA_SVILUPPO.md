# Guida allo Sviluppo - Planner App

## 1. Primo avvio

Serve Python 3.14 (la stessa serie usata dalla CI). Un venv creato con un'altra
versione va ricreato.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Usa il nome `.venv`: `build_portable.py` cerca PyInstaller li. `requirements.txt`
contiene le dipendenze di runtime con versioni fissate (su Windows anche
Python.NET, su Linux Qt/QtWebEngine, circa 500 MB); `requirements-dev.txt` aggiunge
packaging, PyInstaller e Ruff. Dopo un `git pull` rilancia l'installazione.

Compila il frontend, poi avvia l'app:

```bash
cd frontend
npm ci
npm run build
cd ../backend
python main.py
```

Si apre la finestra Planner; il backend risponde su `http://127.0.0.1:8000`.

- `frontend/dist/` non e versionato: dopo ogni modifica o `git pull` del frontend
  rifai `npm run build` (e `npm ci` se e cambiato `package-lock.json`) e riavvia.
- Non c'e reload: le modifiche Python richiedono un riavvio.
- Chiudere la finestra ferma il backend; minimizzarla no.
- DB di sviluppo: `backend/db/planner.db`. Log: `backend/db/logs/planner.log`.
  Profilo della finestra: `backend/db/webview/`.
- Su Windows serve WebView2 Runtime (preinstallato in Windows 11).

## 2. Sviluppo del frontend

Con Planner aperto (per avere il backend attivo), in un altro terminale:

```bash
cd frontend
npm run dev
```

Apri `http://localhost:5173`: Vite aggiorna la pagina a ogni modifica e inoltra
`/api` al backend. La finestra Planner continua a usare la build.

## 3. Provare API e MCP

- API singole: file `backend/test/*.http` (REST Client di VS Code o simili).
  `GET /api/health` restituisce `{"status": "online"}`.
- MCP: collega un client compatibile (trasporto Streamable HTTP) a
  `http://127.0.0.1:8000/mcp/`, con Planner aperto.

## 4. Controlli

```bash
cd frontend
npm run lint
npm run typecheck      # tsc --noEmit sui file .ts/.tsx; eseguito anche da npm run build

cd backend
ruff check .
python -m unittest discover -s test -p test_*.py -v
```

I test usano database e cartelle temporanei e simulano finestra e build: non
toccano `backend/db/planner.db` e non sostituiscono le prove manuali. Le API senza
test automatici si provano con i file `.http`. Per modificare lo schema segui
`DATABASE.md`.

### Prove manuali nella finestra

1. Scarica un backup dalle Impostazioni, poi ripeti annullando il dialogo.
2. Apri un link esterno (es. aggiornamento disponibile): deve aprirsi nel browser.
3. Copia l'indirizzo MCP e verifica il toast.
4. Cambia tema e lingua e riavvia; verifica gli aggiornamenti MCP/SSE anche con la
   finestra minimizzata.

## 5. Build portable

```bash
cd backend
python build_portable.py                     # output in backend/dist/PlannerApp
python build_portable.py --dist-dir dist/x   # cartella alternativa
```

Lo script esegue `npm run build`, PyInstaller (`--onedir`), copia `LICENSE`,
`THIRD_PARTY_NOTICES.md` e le licenze (sezione 6) e verifica il pacchetto: se manca
qualcosa la build fallisce. Va distribuita l'intera cartella `PlannerApp`. Se la
destinazione contiene `data/`, `locales/` o database, la build si ferma senza
cancellarli: non compilare sopra una portable gia usata.

### Windows

Mantiene la console, esclude i renderer di altri sistemi e copia accanto
all'eseguibile `backend/windows/PlannerApp.exe.config`, che attiva
`loadFromRemoteSources` in .NET Framework: senza, da uno ZIP scaricato e non
sbloccato pythonnet non carica le sue DLL.

### Linux

Si compila su Linux (Debian o Ubuntu, per l'inventario `dpkg-query` delle licenze).
La CI usa Ubuntu 22.04 con le librerie elencate nello step `Install Linux desktop
dependencies`; per la distribuzione si usa quella build, perche PyInstaller copia
le librerie del sistema su cui compila. La CI installa `libpcre2-8-0` senza fissare
la versione e si ferma se quella installata e inferiore a `10.39-3ubuntu0.2`.

Dopo PyInstaller, `prune_linux_bundle()` rimuove `qml/`, il tema GTK3 e la stampa
CUPS (Planner usa QtWebEngine Widgets) e, confrontando con `readelf` le
dipendenze prima e dopo, solo le librerie usate esclusivamente da quei file. Toglie
anche `libstdc++`/`libgcc_s` di Ubuntu 22.04: sono piu vecchi di quelli richiesti
dai driver grafici delle distribuzioni recenti e l'app si chiudeva con
`GLIBCXX_3.4.31 not found`. Il pacchetto risultante occupa circa 510 MB (circa
200 MB sono Chromium) e richiede glibc 2.34 o successiva.

Per provare una build locale come la CI, avvia una copia estratta (la portable
crea `data/` accanto all'eseguibile e la build successiva si fermerebbe):

```bash
tar -czf PlannerApp-linux.tar.gz -C dist PlannerApp
mkdir -p ~/prova-planner && tar -xzf PlannerApp-linux.tar.gz -C ~/prova-planner
~/prova-planner/PlannerApp/PlannerApp        # prova anche QT_QPA_PLATFORM=xcb
```

## 6. Licenze nella build

`build_licenses.py` copia in `licenses/` i testi di licenza, con versioni e hash in
file manifest, e la build si ferma se manca qualcosa:

| Contenuto | Origine |
|---|---|
| `python/` + `runtime-manifest.json` | pacchetti di runtime (da `requirements.txt` e dipendenze) e Python |
| `frontend/` | `dist/.vite/license.md` generato da Vite e licenza di Tailwind |
| `microsoft-webview2/` (Windows) | `backend/third_party_licenses/microsoft-webview2/` |
| pacchetti Qt + `manifest.json` (Linux) | metadati delle wheel Qt nel bundle |
| `qtwebengine/`, `qt/` (Linux) | `backend/third_party_licenses/` (Chromium, moduli Qt, ICU) |
| `system/` + `system-manifest.json` (Linux) | copyright dei pacchetti Debian/Ubuntu delle librerie di sistema |

Manutenzione:

- **Nuova dipendenza Python o npm**: aggiorna le tabelle di `THIRD_PARTY_NOTICES.md`.
  Un pacchetto senza file di licenza va in `DISTRIBUTIONS_WITHOUT_LICENSE_FILES`.
- **Aggiornamento di cryptography, pydantic-core o rpds-py** (o nuovo pacchetto con
  estensioni in Rust): controlla su crates.io le licenze dei crate nel `Cargo.lock`
  del loro sorgente su PyPI e aggiorna "Rust Libraries in Compiled Extensions" in
  `THIRD_PARTY_NOTICES.md` se compare una licenza non elencata.
- **Aggiornamento di pywebview** con un WebView2 SDK diverso: la build fallisce;
  scarica `LICENSE.txt` e `NOTICE.txt` da
  `https://www.nuget.org/api/v2/package/Microsoft.Web.WebView2/<versione>` e
  aggiorna `WEBVIEW2_SDK_VERSION`.
- **Aggiornamento di Qt**: la build fallisce finche non rigeneri gli avvisi dai
  sorgenti ufficiali (`https://download.qt.io/official_releases/qt/<x.y>/<x.y.z>/submodules/`),
  verificando ogni archivio con il suo `.sha256`. Gli script leggono i file come
  dati, senza eseguire codice dei sorgenti:

  ```bash
  python qtwebengine_notices.py qtwebengine-everywhere-src-6.11.2 \
    third_party_licenses/qtwebengine/CHROMIUM_NOTICES.txt --sha256 <hash>
  cat *.sha256 > checksums.txt     # archivi di qtbase, qtdeclarative, qtimageformats,
                                   # qtpositioning, qtserialport, qtsvg, qtwayland, qtwebchannel
  python qt_notices.py third_party_licenses/qt/QT_NOTICES.txt --checksums checksums.txt \
    qt*-everywhere-src-6.11.2
  ```

  Poi aggiorna `QT_NOTICES_VERSION`, eventualmente `QT_ICU_MAJOR` e
  `ICU_LICENSE.txt`, `QT_LIBRARY_MODULES` se compaiono nuove librerie Qt, e le
  versioni in `THIRD_PARTY_NOTICES.md`.

## 7. Release

Il workflow `.github/workflows/release-build.yml` compila Windows (ZIP) e Linux
(TAR.GZ) a ogni tag `v*` o con l'avvio manuale, che produce solo artifact.

1. Aggiorna `APP_VERSION` in `backend/config.py` (la versione in
   `frontend/package.json` non e usata). Verifica che i manifest del pacchetto
   Linux di prova coincidano con le versioni in `SOURCES.md` e che le note della
   release contengano il link al documento fissato al tag. Pubblica le modifiche
   su `main`.
2. Crea e pubblica il tag corrispondente, senza la `v` in `APP_VERSION`:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

Il workflow verifica che tag e `APP_VERSION` coincidano. Il job di release
allega `PlannerApp-windows.zip` e `PlannerApp-linux.tar.gz` alla GitHub Release e
fallisce se manca uno dei due file. Se esiste una bozza per lo stesso tag, il
workflow ne conserva le note. L'avvio manuale da `main` non pubblica la release.

Un tag sbagliato e mai distribuito si puo eliminare e ricreare
(`git tag -d v0.2.0 && git push origin --delete v0.2.0`); se e gia stato
distribuito, pubblica una nuova versione.
