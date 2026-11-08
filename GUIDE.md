# Guida pratica: lavorare con Opus, Sonnet e Gemini

Manuale rapido per te. Le regole che leggono i modelli sono in [`flow.md`](flow.md) (sempre attivo) e [`flow-prompts.md`](flow-prompts.md). Il significato di ogni termine è in [`GLOSSARY.md`](GLOSSARY.md). Installazione e aggiornamenti li fa l'agente leggendo [`SETUP.md`](SETUP.md).

## 1. Cosa scrivere in base a cosa stai facendo

| Sto per… | Dove | Cosa scrivo |
|---|---|---|
| Progettare una funzione nuova | Claude Code (Opus) | `/grill-with-docs <idea in 2-3 righe>` |
| Affrontare un lavoro grande o nebbioso | Claude Code (Opus) | `/wayfinder <obiettivo>` |
| Correggere un bug | Claude Code (Opus `high`) | `/diagnosing-bugs` + sintomo e passi |
| Capire un modulo del progetto | Ovunque | `Spiegami <file>` (risponde in chat e aggiorna la pagina in `docs/`) |
| Trovare dove pulire l'architettura | Claude Code / Antigravity | `/improve-codebase-architecture <area>` |
| Implementare un ticket, dall'inizio al commit | Antigravity | `Implementa il ticket <N>` |
| Rilanciare la review su un diff | Antigravity | `Rivedi il ticket <N>` |
| Vedere i ticket, chi li implementa e perché | Claude Code | `Tabella dei ticket` |
| Capire cosa è stato fatto | Claude Code o Antigravity | `Spiegami il flusso di <cosa>` |
| Sapere da dove viene un'affermazione | Ovunque | `Qual è la fonte?` |
| Sapere quale skill usare | Ovunque | `/ask-matt <situazione>` |
| Chiarire una risposta confusa | Claude Code | `/wait-what` |
| Aggiornare skill, plugin e MCP | Claude Code | `Aggiorna il setup seguendo SETUP.md` |
| Cercare MCP utili per te | Claude Code | `Cerca MCP utili seguendo SETUP.md` |

## 2. Chi fa cosa

| Modello | Quando | Livello |
|---|---|---|
| **Opus** (Claude Code) | Decisioni, grilling, spec, ticket, bug difficili | `high` per decisioni costose da annullare, `medium` per il resto |
| **Gemini Flash** (Antigravity) | Esecutore di default, quando un errore si vede da test o build | `Medium`; `Low` solo per modifiche meccaniche; `High` come gradino dopo due fallimenti |
| **Gemini Argon** (Antigravity) | Ticket dove un errore passa i test e si scopre tardi | `Medium`; nel selettore può partire da `High`, controlla prima di iniziare |
| **Sonnet** (subagente Claude) | Ricerche su documentazione e web | `high` |
| **Haiku** (subagente Claude) | Cercare file o simboli nel codice | predefinito |

Opus scrive la scelta per ogni ticket nella riga `Esecutore:`.

## 3. Il ciclo di un lavoro

1. **Decidi con Claude.** `/grill-with-docs`, poi `/to-spec` e `/to-tickets`. I ticket finiscono in `.scratch/<lavoro>/issues/`, sul branch della spec.
2. **Implementa con Gemini.** Chat pulita, modello e livello dalla riga `Esecutore:`, poi `Implementa il ticket 01`. Resti lì fino al commit.
3. **Review automatica.** Con `Review: double` Gemini lancia 3 subagenti e corregge da solo. Con `Review: quick` bastano build, test e `docs/`.
4. **Prova.** Gemini aggiorna `.scratch/`, ti mostra il Walkthrough e, se serve, i passi da provare.
5. **Commit.** Sul branch della spec, dopo il tuo ok. Per il ticket dopo apri una sessione nuova; il merge su `main` lo fai tu a spec finita.

Mentre Gemini lavora puoi progettare la spec successiva con Claude.

## 4. Cosa ti viene mostrato

| Quando | Chi | Cosa ricevi |
|---|---|---|
| Fine di `/to-tickets` | Claude | Tabella dei ticket: titolo, prompt, modello e livello, review, perché; sotto, il `flowchart TD` delle dipendenze |
| Fine ticket | Gemini | Walkthrough: effetto in 2 frasi, `flowchart TD`, API e flag con la fonte, spiegazione dei passaggi, prova manuale |
| Fine di un lavoro | Claude | `flowchart TD` del flusso toccato e tabella `Cosa, Perché, Fonte` |

La mappa di tutto il setup è in [`docs/index.mdx`](docs/index.mdx).

## 5. Comandi utili

| Vuoi… | Scrivi |
|---|---|
| Capire il perché completo | `spiegami il perché` |
| Far controllare bug, rischi e codice superfluo (in Antigravity) | `/ponytail-review uncommitted` |
| Vedere le scorciatoie rimandate nel codice | `/ponytail-debt` |
| Vedere la documentazione in locale | `npx mint dev --port 3333` dentro `docs/` |
