# Flusso di lavoro con gli agenti

Il vocabolario del flusso descritto in `flow.md`: chi lavora, come si passa da una richiesta a un commit, come si controlla la qualità e come si capisce il codice. Scritto per essere letto da uno junior: ogni termine in una o due frasi semplici.

## Language

### Chi lavora

**Opus**:
Il modello più forte (Opus 5.5 in Claude Code): fa da architetto insieme a te per grilling, wayfinder, spec, ticket, e diagnosi bug.

**Sonnet**:
Un modello veloce e preciso (Sonnet 5.5 in Claude Code), lanciato come subagente per le ricerche.

**Haiku**:
Il modello più piccolo di Claude, usato come subagente per cercare file o simboli nel codice.

**Argon**:
Il modello principale di Google (Gemini 4 Argon) dentro Antigravity Ultra che implementa i ticket e applica i fix.

**Progettista**:
Il ruolo di chi fa grilling, spec, ticket e diagnosi dei bug. Oggi è Opus in Claude Code; può farlo anche Gemini 4 Carbon in Antigravity.

**Esecutore**:
Il ruolo di chi implementa un ticket: Gemini Flash o Argon, secondo la riga `Esecutore:` del ticket.

**Revisore**:
Il ruolo di chi controlla il lavoro degli altri: i tre subagenti della Doppia Review e il contrarian.

**Antigravity**:
L'IDE di Google dove lavori con Argon usando la quota del piano Ultra, separata da quella di Claude Code.

**Subagente**:
Un'altra istanza di AI lanciata dalla sessione principale per un compito specifico (come una review o l'esplorazione di più moduli), con il proprio contesto pulito.

**Livello**:
Quanto a fondo ragiona il modello prima di rispondere (`medium` per il lavoro ordinario, `high` per decisioni architetturali, bug difficili e verifiche).

### Il percorso di un lavoro

**Flusso**:
L'insieme di passi in `flow.md` che porta un lavoro da un'idea a un commit: esplorazione, spec, ticket su disco, implementazione, Doppia Review, Walkthrough, prova manuale e commit.

**Ingresso**:
La regola con cui Opus sceglie da quale passo partire davanti a una richiesta nuova.

**Via**:
La riga `Via: /<skill>, perché <segnale>` con cui Opus propone da dove partire, aspettando la tua conferma prima di procedere.

**Aim-higher**:
Il passo iniziale in cui l'AI cerca fatti nel codice, nella documentazione ufficiale e sul web per spiegarti *principio e causa* e proporti le alternative migliori (incluso lo standard ufficiale) prima di progettare.

**Grilling**:
Un'intervista a giri (`/grill-with-docs`) in cui l'AI ti fa le domande necessarie per sciogliere i dubbi progettuali, proponendo per ciascuna i pro, i contro e l'opzione consigliata.

**Wayfinder**:
Il modo di affrontare un lavoro grande o nebbioso (`/wayfinder`): costruisce una mappa delle decisioni e spacca il lavoro in ticket piccoli.

**Spec**:
Il documento (`spec.md` in `.scratch/`) che fissa cosa costruire e perché, scritto dopo il grilling.

**Ticket**:
Un pezzo di lavoro piccolo e autonomo salvato su disco in `.scratch/`, con un obiettivo chiaro e criteri di verifica.
_Avoid_: task (`task` è solo uno dei valori del campo `Type`).

**Nucleo**:
La parte delle regole che ogni agente legge sempre, in ogni sessione: ruoli, lingua, fonti, il ciclo in breve e i commit. Il resto del flusso sta nelle skill e si apre solo quando serve.

**Fondamenta**:
Ciò che ogni repo deve avere prima del primo ticket: `AGENTS.md` con un comando dei test provato, `docs/` e le skill di Matt Pocock configurate. In un repo con una storia vengono dopo l'analisi e l'allineamento.

**Repo ibrido**:
Un repo condiviso con colleghi in cui tutto il materiale degli agenti resta solo sulla tua macchina: regole, spec e ticket, skill e la guida `docs/`. Nel repo comune arrivano solo codice e test.
_Avoid_: repo misto.

**Repo versionato**:
Un repo in cui anche il materiale degli agenti è salvato in git, come questo.

**Contrarian**:
L'agente di Claude Code che fa il premortem dei ticket: finiti i ticket e prima del codice, immagina che il lavoro sia già fallito e cerca perché, nel codice e in qualsiasi fonte. Ogni obiezione porta una prova che chiunque può riaprire; può anche scrivere ed eseguire script di verifica, nella sua cartella in `.scratch/`. Spec, ticket e codice li cambi tu.

**Premortem**:
Immaginare che un progetto sia già fallito e cercare le cause prima di cominciare. Il metodo è di Gary Klein (Harvard Business Review, 2007), letto tramite fonti secondarie il 10/11/2026: vedi `DECISIONS.md`, decisione 29.

**Type**:
Il tipo di un ticket: `research`, `prototype`, `grilling` o `task` (`HITL` se fatto insieme a Opus, `AFK` se implementato da Argon).

**Triage**:
Decidere cosa fare di una segnalazione scritta da altri (collega o cliente): chiarirla, trasformarla in ticket o scartarla.

**Implement**:
Il passo in cui si scrive il codice di un ticket e lo si verifica con build o test reali.

**Doppia Review**:
Il controllo automatico di codice e documentazione fatto da tre subagenti indipendenti in parallelo: Standards e Spec con le istruzioni di `code-review`, più `ponytail-review` (bug logici, rischi sotto carico e codice inutile). Lo lancia Gemini da solo, a fine implementazione.

**Fix**:
La correzione applicata autonomamente dall'AI al codice o alla documentazione dopo che la Doppia Review ha trovato problemi tecnici reali verificati.

**Retro**:
Una riflessione mirata (`/retro`) che si lancia solo quando qualcosa è andato storto o dopo aver risolto un bug vero, per capire quale controllo automatico o regola locale avrebbe evitato il problema.

### Capire il codice e valutare la qualità

**Guida del Codice (`docs/` con Mintlify + GitBook)**:
La guida viva del repository servita da web con **Mintlify** (`docs/docs.json`, `docs/index.mdx`) e compatibile **GitBook** (`docs/SUMMARY.md`), scritta secondo la skill `junior-deep-docs`: cataloga i file in `docs/index.mdx` e spiega per ogni modulo i giri degli eventi (`flowchart TD`), le strutture di stato con unità di misura e thread, e ogni funzione/API/flag. Viene aggiornata a ogni ticket e arricchita dalle domande fatte in chat (*Query -> Wiki*).

**Walkthrough**:
La spiegazione strutturata in 5 sezioni che l'AI ti presenta a fine ticket prima della prova manuale: mostra cosa fa il programma, il diagramma verticale `flowchart TD` del giro degli eventi, la tabella delle API/Parametri/Flag usati, i passaggi centrali spiegati con la scheda SMIG e i passi A, B... per provarlo.

**SMIG**:
I quattro punti con cui il Walkthrough ti spiega ogni metodo importante toccato dal ticket: **Dove siamo** (file e metodo), **Meccanismo** (cosa fa e quali variabili/tipi muove), **Perché è fatto così** (l'idea dietro) e **Occhio a / Gotcha** (la trappola o caso limite a cui fare attenzione).

**Valutare criticamente**:
L'abitudine di accompagnare ogni scelta progettuale o proposta con due pensieri basati sui fatti: uno **A favore** e uno **Contrario**.

**Finding**:
Un problema concreto segnalato durante la review, con l'indicazione del file e della gravità (`Must` = da correggere, `Should` = consigliato, `Nice` = rifinitura).

**Aree a rischio**:
Le parti del progetto dove un errore costa caro; in questo repo gli hook di sicurezza e lo script di sincronizzazione.

### Strumenti e file di supporto

**Skill**:
Una scheda di istruzioni specializzate che l'agente carica quando serve (es. `ui-ux-doctrine`, `aim-higher`).

**Hook**:
Uno script automatico che gira prima (`PreToolUse`) o dopo (`PostToolUse`) un comando dell'AI per garantire la sicurezza (blocco di `git push`/`merge` e lettura `.ini`/`.env`).

**MCP**:
Il ponte che collega l'AI a strumenti esterni reali. L'elenco di questo setup è in `mcp.json`.

**`.scratch/`**:
La cartella su disco dove vivono spec, ticket, `DECISIONS.md` e `NOTES.md`. Permette di aprire una sessione nuova e pulita tra una fase e l'altra senza perdere mai il filo del lavoro.

**`DECISIONS.md` e `NOTES.md`**:
I due file dentro `.scratch/<lavoro>/` dove si annotano le decisioni prese e i concetti chiave emersi, sempre accompagnati dalla fonte (codice, messaggio dell'utente o documentazione). Le decisioni sul setup stesso stanno invece in `DECISIONS.md`, nella radice di questo repo.

**Fonte verificata**:
Il posto preciso dove si legge un'affermazione: pagina ufficiale con data di lettura, autore con data, codice o comando eseguito. Ciò che non ce l'ha si scrive `non verificato`.
