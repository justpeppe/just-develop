---
title: "Guida alle skill"
description: "Tutte le skill del setup (proprie, esterne e plugin ponytail opzionale), chi le lancia, prompt d'esempio e skill escluse dal flusso."
keywords: ["skills", "flow-design", "implement-ticket", "aim-higher", "junior-deep-docs", "ui-ux-doctrine", "mattpocock"]
---

Le procedure ripetibili di `just-develop` vivono come skill in `skills/` (collegate a entrambi i client tramite junction) accanto alle skill esterne installate da `SETUP.md` e ai comandi opzionali di `ponytail`. Ogni descrizione rispecchia il file `SKILL.md` reale su disco.

<Info>
Una skill senza `disable-model-invocation` può essere attivata automaticamente dall'agente quando il prompt corrisponde alla sua descrizione, oltre che da te. Una skill con `disable-model-invocation: true` risponde solo quando la richiami tu con `/nome-skill`.
</Info>

## Le 5 skill del repository (`skills/`)

Queste cinque skill vivono in `skills/` di `just-develop` e arrivano sia a Claude Code sia ad Antigravity tramite le junction configurate da `SETUP.md`. Tutte e cinque sono model-invoked (`disable-model-invocation` omesso).

| Skill | Quando si usa | Chi la lancia | Prompt d'esempio | Cosa produce |
|---|---|---|---|---|
| `flow-design` (`skills/flow-design/SKILL.md`) | Richiesta nuova, `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/wayfinder`, `tabella dei ticket` | Agente o Tu (`/flow-design`) | `Progetta questa funzione con /flow-design: ...` | Routing iniziale, ricerca `aim-higher`, spec in `.scratch/`, ticket verticali con `S/G/C`, `contrarian`, tabella di consegna |
| `implement-ticket` (`skills/implement-ticket/SKILL.md`) | Implementazione o review di un ticket pronto | Agente o Tu (`/implement-ticket`) | `Implementa il ticket 03` oppure `Rivedi il ticket 03` | Pre-flight, edit mirati, `docs/`, check deterministici, review `quick` o `double` (3 subagenti `inherit`), `## Answer`, Walkthrough, commit |
| `aim-higher` (`skills/aim-higher/SKILL.md`) | Prima di fissare un piano o quando vuoi confrontare strade da senior | Agente (via `flow-design`) o Tu | `Pensa più in grande su questo modulo` | Principio, causa, giudice esterno e 2-3 opzioni con pro, contro e fonti |
| `junior-deep-docs` (`skills/junior-deep-docs/SKILL.md`) | Dopo modifiche a codice documentato, per spiegare un modulo o salvare risposte in `docs/` | Agente o Tu | `Spiegami come funziona questo modulo` | Pagina in `docs/` con catene runtime, stato (unità/thread), chiamate API/flag e catalogo `index.mdx` aggiornato |
| `ui-ux-doctrine` (`skills/ui-ux-doctrine/SKILL.md`) | Progettazione, modifica o review di schermate, form, dialoghi o pagine HTML | Agente o Tu | `Controlla accessibilità e stati di questa schermata` | Verifica su limiti di Nielsen (`0.1 s`, `1 s`, `10 s`), WCAG 2.2 AA (`4.5:1`, `24 px`) e 4 stati UI |

## Come funzionano `flow-design` e `implement-ticket`

<Steps>
  <Step title="Risoluzione della home e lettura diretta">
    Sia `flow-design` sia `implement-ticket` risolvono `~` nella home reale del sistema (`$HOME` su POSIX, `%USERPROFILE%` su Windows) e aprono i `SKILL.md` tramite `Read` o `read_file`, così il flusso funziona in modo identico su Claude Code e Antigravity 2.0 senza dipendere dal tool `Skill`.
  </Step>
  <Step title="Contratto nativo di Spec e Ticket">
    `flow-design` integra direttamente i formati di `.scratch/<work>/spec.md` e `.scratch/<work>/issues/<NN>-<slug>.md` con `Blocked by`, `Status: ready-for-agent`, raggiungibilità UI, `## Ipotesi`, criteri eseguibili per file e simbolo, `Esecutore:`, `HITL:` e la metrica `S/G/C` (`0/0/0` -> `Review: quick`; qualsiasi bit `= 1` -> `Review: double`).
  </Step>
  <Step title="Review binaria e chiusura">
    `implement-ticket` lancia `git add -N -- . ':(exclude).scratch'` e valuta `git diff -- . ':(exclude).scratch'`. Su `Review: quick` esegue l'auto-verifica senza subagenti; su `Review: double` lancia 3 subagenti paralleli su `inherit` (`Standards` + `Spec` + `ponytail-review` a 6 assi), corregge in una passata, aggiorna `## Answer` e presenta il Walkthrough in 5 sezioni prima del commit.
  </Step>
</Steps>

## Skill esterne installate con `SETUP.md`

Le skill di terze parti vengono installate in `~/.agents/skills/` (o `~/.claude/skills/` per `find-skills`) e collegate a entrambi i client. Sono divise qui per fase del flusso.

### Ingresso e progettazione (`mattpocock/skills`)

| Skill | Attivazione | Quando usarla | Prompt d'esempio | Cosa produce |
|---|---|---|---|---|
| `grilling` | Agente o Tu | Stress-testare un'idea a round di domande | `Intervistami su questa idea` | Albero decisionale risolto round per round |
| `domain-modeling` | Agente o Tu | Chiarire termini di dominio, scrivere `GLOSSARY.md` o ADR | `Allinea il glossario su questi concetti` | Voci in `GLOSSARY.md` e ADR in `docs/adr/` |
| `triage` | Solo Tu (`/triage`) | Classificare issue esterne o PR in arrivo | `/triage guarda il ticket 42` | Raccomandazione stato/etichetta e brief riprodotto |
| `diagnosing-bugs` | Agente o Tu | Bug difficili o regressioni | `/diagnosing-bugs l'hook fallisce su percorsi con spazi` | Loop rosso riproducibile, ipotesi falsificabili, test di regressione |
| `prototype` | Agente o Tu | Validare una macchina a stati o un layout prima del codice vero | `Costruisci un prototipo usa e getta per questo flusso` | Demo HTML/UI isolata per rispondere alla domanda progettuale |
| `wayfinder` | Solo Tu (`/wayfinder`) | Lavori grandi che richiedono più sessioni | `/wayfinder migra il modulo pagamenti` | Mappa `.scratch/<effort>/map.md` e ticket decisionali ordinati |
| `codebase-design` | Agente o Tu | Progettare moduli profondi, interfacce e seam di test | `Usa /codebase-design su questi moduli` | Proposta di interfacce compatte e test di cancellazione |
| `ask-matt` | Solo Tu (`/ask-matt`) | Quando non ricordi quale skill di Matt usare | `/ask-matt devo riordinare un modulo vecchio` | Scelta guidata della skill adatta |
| `wait-what` | Solo Tu (`/wait-what`) | Quando una risposta è confusa o troppo densa | `/wait-what` | Riformulazione chiara usando `GLOSSARY.md` |
| `grill-me` | Solo Tu (`/grill-me`) | Intervista rapida senza aggiornamento glossario/ADR | `/grill-me su questo refactor` | Chiarimento delle scelte di piano |

### Implementazione, review e scrittura

| Skill | Attivazione | Quando usarla | Prompt d'esempio | Cosa produce |
|---|---|---|---|---|
| `tdd` | Agente o Tu | Sviluppo test-first (ciclo rosso-verde-refactor) | `Implementa questa funzione con tdd` | Test che fallisce prima, poi implementazione minima e refactor |
| `code-review` | Agente o Tu | Review di branch o PR già committati rispetto a un punto fisso | `Fai code-review rispetto a main` | Due report separati: `Standards` e `Spec` |
| `improve-codebase-architecture` | Solo Tu | Cercare moduli superficiali da approfondire | `/improve-codebase-architecture src/` | Report HTML delle opportunità e grilling su quella scelta |
| `pr` | Agente o Tu | Scrivere il testo di una pull request | `Prepara il testo della PR con la skill pr` | Corpo della PR sintetico e orientato alle modifiche |
| `writing-for-agents` | Agente o Tu | Creare o rifinire `SKILL.md`, `AGENTS.md` o `CLAUDE.md` | `Rivedi questa skill con writing-for-agents` | Istruzioni corte, positive e con criteri `*Done when*` |
| `humanizer` | Agente o Tu | Togliere tono artificiale, trattini doppi e formule AI dalla prosa | `Rendi naturale questo documento con humanizer` | Testo pulito che mantiene i fatti originali |
| `mintlify` | Agente o Tu | Configurare o modificare siti `docs/` (`docs.json`, componenti MDX) | `Controlla docs.json e i link di docs/` | Configurazione Mintlify, pagine e controllo `mint validate` |

### Manutenzione, ricerca e supporto

| Skill | Attivazione | Quando usarla | Prompt d'esempio | Cosa produce |
|---|---|---|---|---|
| `retro` | Solo Tu (`/retro`) | Dopo un bug o errore di sessione per migliorare regole e hook | `/retro su questa sessione` | Proposte di fix su hook, test o `AGENTS.md` |
| `handoff` | Solo Tu (`/handoff`) | Passare il testimone di una sessione lunga a una nuova chat | `/handoff proseguo sui test` | Documento temporaneo in `%TEMP%`/`$TMPDIR` |
| `setup-matt-pocock-skills` | Solo Tu | Inizializzare `docs/agents/` su un nuovo repository | `/setup-matt-pocock-skills` | Configurazione tracker locale, etichette triage e dominio |
| `research` | Agente o Tu | Ricerche approfondite su fonti primarie in background | `Fai research su come gestisce i lock Windows Python` | File markdown di sintesi con fonti primarie citate |
| `teach` | Solo Tu (`/teach`) | Imparare un concetto su più sessioni | `/teach come funzionano i lock di file` | Workspace didattico `./lessons/` |
| `to-questionnaire` | Solo Tu | Raccogliere risposte asincrone da un collega su requisiti mancanti | `/to-questionnaire per il team infra` | Questionario markdown mirato alle lacune note |
| `wizard` | Agente o Tu | Generare script bash interattivi per passi manuali ripetuti | `Crea un wizard per registrare i webhook` | Script bash guidato passo per passo |
| `find-skills` | Agente o Tu | Cercare nuove skill nell'ecosistema aperto | `Cerca una skill per gestire migrazioni SQL` | Suggerimento di pacchetti installabili con `skills` CLI |
| `skill-creator` | Agente o Tu | Creare, valutare e ottimizzare nuove skill | `Crea una skill per generare changelog` | Struttura `SKILL.md` e test dei prompt di attivazione |
| `pdf` | Agente o Tu | Estrarre testo, tabelle o compilare moduli PDF | `Estrai le tabelle da questo PDF` | Dati o PDF modificato |

## Skill opzionali compatibili (fuori da `SETUP.md`)

Queste skill si installano separatamente se ti servono nei tuoi progetti e restano compatibili con entrambi i client quando presenti in `~/.agents/skills/`:

| Skill | Attivazione | Quando usarla | Prompt d'esempio | Cosa produce |
|---|---|---|---|---|
| `deepwiki` | Agente o Tu | Consultare la documentazione di un repository GitHub pubblico | `Cerca su deepwiki come funziona X` | Riepilogo dai sorgenti pubblici del repo cercato |
| `frontend-design` | Agente o Tu | Progettare interfacce web con identità visiva curata | `Disegna la pagina dashboard con frontend-design` | Scelte di tipografia, palette e layout web |

## Plugin `ponytail` (opzionale, spento di default)

In v2 il plugin runtime `ponytail` è disattivato sia in Claude Code (`settings.json`) sia in Antigravity (`config.json`) per risparmiare contesto fisso a ogni turno. I 6 assi di qualità di `ponytail-review` (`Bug`, `Risk`, `Scale`, `Missing test`, `Speed`, `Lean`) sono già integrati direttamente in `implement-ticket` per `Review: double`. Se riabiliti temporaneamente il plugin, ottieni sei comandi aggiuntivi:

- `/ponytail`: imposta il livello di sintesi e minimalismo (`lite`, `full`, `ultra`, `off`).
- `/ponytail-review`: review one-shot su diff non committati, branch o commit.
- `/ponytail-audit`: audit qualità sull'intero repository senza modificare codice.
- `/ponytail-debt`: elenco dei commenti `shortcut:` (o vecchi `ponytail:`) presenti nel codice.
- `/ponytail-gain` e `/ponytail-help`: riepilogo benchmark e guida rapida ai comandi.

## Skill escluse dal flusso

Alcune skill restano installate nei pacchetti condivisi ma non vanno usate al posto del ciclo di `flow.md`:

| Skill esclusa | Perché è esclusa | Cosa usare al suo posto |
|---|---|---|
| `/implement` | Termina creando un commit automatico senza attendere Walkthrough, prova manuale né conferma dell'utente. | `Implementa il ticket <N>` (`implement-ticket`) |
| `/implement-spec` | Integra su un branch tramite `git merge`, comando vietato agli agenti dai guardrail di sicurezza. | Un ticket per finestra con `implement-ticket` e merge manuale su `main` |
| `to-spec` e `to-tickets` | I loro template omettono `Review:`, `Esecutore:`, `S/G/C` e i riferimenti verificati per file e simbolo, e rimandano a `/setup-matt-pocock-skills`. | Contratto nativo già integrato in `flow-design` |
| `grill-with-docs` (invocazione diretta) | Chiama il tool `Skill` di Claude Code, assente in Antigravity 2.0. | Usarlo solo come trigger verso `flow-design`, che legge `grilling` e `domain-modeling` direttamente su disco |
