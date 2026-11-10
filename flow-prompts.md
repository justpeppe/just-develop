# Riferimento operativo per Review, Documentazione (`junior-deep-docs`), Walkthrough, Retro e Contrarian (`flow-prompts.md`)

Questo file contiene le istruzioni operative per i **3 subagenti di Doppia Review**, per la **Documentazione del Codice (`docs/` con Mintlify + `junior-deep-docs` + `humanizer`)**, per il **Walkthrough di fine ticket**, per la **`/retro`** e per il **contrarian** sui ticket. Non contiene template da copiare e incollare a mano tra le chat: gli strumenti leggono direttamente il ticket da `.scratch/` e le modifiche da `git diff`.

---

## 1. Doppia Review (`code-review` su due assi + `ponytail-review`) e Fix autonomo

Quando un ticket marcato **`Review: double`** (default) ha superato la build dentro **`Implementa il ticket <N>`** — oppure quando l'utente chiede esplicitamente **`Rivedi il ticket <N>`** — l'agente esegue `git add -N -- . ':(exclude).scratch'` e lancia con `invoke_subagent` **in parallelo tre subagenti indipendenti** a contesto pulito. Ognuno riceve `git diff -- . ':(exclude).scratch'`: la skill `code-review` intera guarda solo il già committato, mentre il commit arriva alla fine, quindi i subagenti ne leggono le istruzioni e usano il diff passato.
*(Eccezioni: per i ticket piccoli marcati **`Review: quick`** (al massimo 30 righe) e per i **fix applicati a seguito della Doppia Review** non si lanciano i subagenti: bastano build, test e `docs/` verdi).*

1. **Subagente Standards — istruzioni di `code-review`, asse Standards:** legge `code-review/SKILL.md`, `junior-deep-docs/SKILL.md`, `humanizer/SKILL.md`, la skill di Mintlify, `CODING_STANDARDS.md` (se presente), `AGENTS.md`, il ticket in `.scratch/` e il `git diff`. Controlla:
   - rispetto degli standard del repo;
   - presenza dei commenti di documentazione su metodi e strutture non banali (con unità di misura e vincoli di thread);
   - se il diff tocca la UI, rispetto di `ui-ux-doctrine`;
   - **documentazione in `docs/` secondo `junior-deep-docs`:** verifica incrociata tra il codice reale e le pagine (`docs.json`, `index.mdx`/`README.md`, `SUMMARY.md`, pagine di sezione). Boccia come **`Must fix`** una pagina che omette strutture di stato o metodi centrali, che non specifica parametri, flag e unità di misura delle API, o che usa titoli da template.
2. **Subagente Spec — istruzioni di `code-review`, asse Spec:** legge `code-review/SKILL.md`, il ticket in `.scratch/` e il `git diff`. Riporta i requisiti mancanti o parziali, il comportamento non richiesto e ciò che sembra fatto ma è sbagliato.
3. **Subagente Qualità, Sicurezza e Rischi — `ponytail-review`:** legge `ponytail-review/SKILL.md`, il ticket e il `git diff` (più il codice collegato). Cerca bug logici, condizioni di gara, gestione errori mancante, rischi sotto carico e codice superfluo. Verifica anche che i test provino il codice vero, non i mock.

**Filtro e correzione autonoma (Zero Decision Fatigue per l'utente, una sola passata):**
- Controlla ogni finding sul codice reale (`Read` / `Grep`): scarta subito in silenzio i falsi positivi e le preferenze di stile fuori perimetro.
- Se restano **bug tecnici reali, leak, warning, pagine `docs/` incomplete/riassuntive/disallineate o punti della spec mancanti**, correggili **subito** e riesegui la verifica reale (build, test, verifica MDX) prima di presentare il Walkthrough, **senza rilanciare una seconda Doppia Review sui fix appena applicati**. Interpella l'utente solo se la correzione richiede di cambiare una scelta di prodotto o comportamento visibile.

---

## 2. Struttura della Guida del Codice in `docs/` (`junior-deep-docs` + `mintlify`)

In ogni repo la documentazione del codice vive in **`docs/`** (servita da web con **Mintlify** tramite `docs/docs.json` e `npx mint dev --port 3333`, e compatibile GitBook tramite `SUMMARY.md`), seguendo la skill **`junior-deep-docs`**:

```text
docs/
├── docs.json                  # Configurazione Mintlify (tema, colori, gruppi di navigazione)
├── index.mdx (e README.md)    # Homepage: architettura generale + Catalogo Completo del 100% dei file del repo
├── SUMMARY.md                 # Indice di navigazione GitBook
├── adr/                       # Se serve: Architecture Decision Records (decisioni importanti e alternative scartate)
└── <sezioni-del-progetto>/    # Una pagina .md/.mdx per ogni Area funzionale reale (es. login.md, pagamenti.md)
```

### Come si scrive una pagina
Le domande di indagine sul codice, la struttura della pagina, lo stile e i controlli di fine sono nella skill `junior-deep-docs`: leggila prima di scrivere o rivedere una pagina di `docs/`.

---

## 3. Formato del Walkthrough fisso in chat a fine ticket

Prima di dare la parola all'utente per la prova manuale:
1. **Aggiorna il file del ticket in `.scratch/<lavoro>/issues/<NN>-<slug>.md` scrivendo `## Answer`, senza toccare `Status`** (`Status: resolved` si scrive subito prima del commit, con l'ok dell'utente) (e aggiorna `.scratch/<lavoro>/map.md` se presente, così il disco resta la memoria condivisa tra Claude Code e Antigravity, evitando che un modello dimentichi cosa ha fatto l'altro).
2. **Assicurati che `docs/SUMMARY.md` e le pagine `docs/*.md` toccate siano aggiornate** e verificate dalla review.
3. **Presenta il Walkthrough del ticket** in italiano semplice (stile `GLOSSARY.md`), seguendo queste **5 sezioni**:

### A. Cosa fa adesso il programma (in 2 frasi)
L'effetto pratico dal punto di vista di chi usa il programma.

### B. Il giro degli Eventi e dei Dati (Diagramma Mermaid sempre `flowchart TD`)
Diagramma **sempre verticale (`flowchart TD`, mai `LR`)** da 5–9 blocchi: `Controllo / Chiamante → Metodo (modulo) → Stato / Effetto`.

### C. Sotto il cofano: API, Funzioni, Parametri e Flag usati
Tabella chiara per le funzioni di libreria o i metodi centrali toccati dal ticket:

| Funzione / API chiamata | A cosa serve (in umano) | Parametri e Flag passati (uno per uno) | Cosa restituisce (tipo e unità di misura) | Perché questa scelta e dove si legge |
|---|---|---|---|---|
| `NomeFunzione(param1, flag)` | Cosa fa in concreto | `- param1`: cos'è e che valore ha<br>`- FLAG_X`: cosa attiva/cambia | Tipo di ritorno, range valori (es. ms, sec, `0.0..1.0`) | Perché usiamo questa API/flag, con la documentazione ufficiale da cui si legge |

### D. I mattoni del codice (Scheda SMIG + Codice vero)
Per ciascuno dei 2–4 passaggi centrali toccati dal ticket:
- **Dove siamo:** file + nome dell'Evento o Metodo (la riga solo se aiuta a trovarlo).
- **Codice chiave (1–5 righe vere):** il frammento esatto.
- **Meccanismo:** cosa fa e quali **Variabili / Campi / Record** legge o modifica.
- **Perché è scritto così:** la ragione tecnica.
- **Occhio a (Trappola / Gotcha):** il caso limite (thread, memoria, valori nulli, limiti).

### E. Prova manuale HITL, se il ticket la richiede (Passi A, B...)
I passi concreti da provare a schermo. Chiudi con: `Se la prova manuale passa, dimmi e facciamo commit.`

---

## 4. Dove finiscono le proposte di `/retro` (quando la lanci)

| Tipo di lezione | Dove va |
|---|---|
| Errore meccanico ripetibile (git, encoding, formato) | Un controllo automatico (hook o script), **non** prosa in `CLAUDE.md` |
| Nuovo modulo, evento, stato, API usata o giro di eventi | La pagina di sezione corrispondente in `docs/` (+ `docs/SUMMARY.md` se è una pagina nuova) |
| Regola di stile del codice per le review di un progetto | `CODING_STANDARDS.md` di quel repo |
| Termine di dominio o tecnico chiarito | `GLOSSARY.md` |
| Decisione architetturale importante e costosa da invertire | `docs/adr/` |

## 5. Contrarian sui ticket (fine di `/to-tickets`)

Finiti i ticket e prima della tabella di consegna, Opus lancia l'agente `contrarian` (`agents/contrarian.md` di just-develop, dove stanno modello, istruzioni, regola della prova e quando si salta; esiste solo in Claude Code). Ha tutti gli strumenti, così può cercare ovunque e scrivere ed eseguire script di verifica; ciò che crea va in `.scratch/<lavoro>/contrarian/`. Gli passa il percorso della spec e dei ticket in `.scratch/<lavoro>/`, non il ragionamento che li ha prodotti. Prima di lanciarlo Opus annota `git status --short` e l'impronta dei file di spec e ticket (`shasum`, su Windows `Get-FileHash`): i ticket appena scritti spesso non sono tracciati, e `git status` da solo non ne vedrebbe le modifiche.

Quando arriva il report, Opus:

1. rifà `git status --short` e le impronte, e controlla che spec, ticket e codice siano come prima e che il contrarian abbia scritto solo nella sua cartella;
2. riapre ogni prova citata e rilancia gli script di verifica;
3. tiene le obiezioni la cui prova regge, scarta dicendolo quelle smentite, e mostra come `non verificato` quelle che non è riuscito a controllare;
4. ti presenta la tabella e modifica solo i ticket che scegli.

*Fatto quando* ogni obiezione è accolta, con il ticket cambiato, oppure scartata con il motivo.
