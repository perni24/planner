# To Do - Context e LocalStorage

## SettingsContext

- [x] `SettingsContext.jsx` chiama `loadSettings()` dentro `useEffect`.
- [ ] Aggiungere stato `isLoadingSettings` per sapere quando le settings sono state caricate.
- [ ] Rinominare `error` in `settingsError` ed esporlo nel value del context.
- [ ] Gestire il fallback `response[0] ?? null` quando si salvano le settings.
- [x] `SettingsProvider` e montato dentro `AppProviders.jsx`, sopra `ThemeProvider`.
- [ ] Inizializzare `settings` a `null` invece che `[]`, per coerenza con l'uso come singolo oggetto.
- [ ] Esporre nel value anche `isLoadingSettings` e `settingsError`.

## ThemeContext

- [ ] Leggere i valori iniziali da `localStorage` per `theme` e `customColors`.
- [x] `ThemeContext` legge le settings dal `SettingsContext` tramite `useSettings()`.
- [ ] Quando arrivano le settings dal DB, aggiornare `theme`, `customColors` e `localStorage`.
- [x] Applicare classi `dark` / `custom` in base al valore `theme`.
- [x] Applicare le CSS variables custom in base a `customColors`.
- [ ] Sostituire `setTheme` esposto dal context con una funzione `updateTheme()` che aggiorna state, `localStorage` e in futuro il DB.
- [ ] Aggiornare `updateCustomColor()` per salvare anche in `localStorage`.
- [ ] Aggiungere un `useEffect` che copia `settings.theme` e i campi `custom_*` dentro `theme` e `customColors`.
- [ ] Valutare se rimuovere i default duplicati da `ThemeContext` usando DB/CSS come fonte dei default.

## LanguageContext

- [ ] Creare `LanguageContext.jsx`.
- [ ] Leggere la lingua iniziale da `localStorage`.
- [ ] Leggere la lingua salvata nel DB tramite `SettingsContext`.
- [ ] Caricare il dizionario lingua con API backend.
- [ ] Esporre una funzione `t(key)` per leggere le traduzioni.
- [ ] Esporre una funzione `updateLanguage(language)` che aggiorna state, `localStorage` e in futuro il DB.
- [ ] Gestire fallback se una chiave di traduzione manca.

## LocalStorage

- [ ] Salvare `theme` in `localStorage`.
- [ ] Salvare `customColors` in `localStorage` come JSON.
- [ ] Salvare `language` in `localStorage`.
- [ ] Aggiungere una funzione sicura per leggere JSON da `localStorage` senza crash se il contenuto e corrotto.
- [ ] Valutare una chiave `settings_version` per invalidare la cache se la struttura settings cambia.

## Avvio App

- [ ] Decidere se accettare il flash iniziale dei colori CSS default.
- [ ] Se il flash non e accettabile, aggiungere uno script inline in `index.html` per applicare `theme` e `customColors` da `localStorage` prima del mount React.
- [ ] Valutare se bloccare il render dell'app finche `SettingsContext` non ha caricato le settings.

## API e DB

- [ ] Aggiungere endpoint backend per aggiornare una singola setting.
- [ ] Aggiornare il DB quando l'utente cambia tema, colori o lingua.
- [ ] Mantenere il DB come fonte persistente ufficiale.
- [ ] Usare `localStorage` solo come cache veloce frontend.
- [ ] Valutare se cambiare `getAllSettings()` frontend per restituire direttamente una singola `Settings` invece di `Settings[]`.

## Pulizia Frontend

- [ ] Rimuovere import inutilizzati da `Setting.jsx`: `useState` e `useEffect` non sono piu usati.
- [ ] Spostare UI tema, colori e lingua in componenti separati se `Setting.jsx` cresce troppo.
- [x] `AppProviders.jsx` resta solo composizione dei provider, senza chiamate API dirette.
