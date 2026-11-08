# Decisioni

Cosa abbiamo portato in `just-develop` e perché. Sessione dell'8 novembre 2026. Le due origini sono `agents-config-repo` (il 7z) e `agents-setup-repo`.

## 1. Il 7z è l'ossatura

**Scelta:** flusso, hook, test e sincronizzazione vengono dal 7z; da `agents-setup-repo` arrivano le regole globali e la tabella delle fonti.

**Perché:** il 7z ha 70 commit di lavoro reale e hook già testati. Le sue regole globali stavano in `~/.claude/CLAUDE.md`, fuori dal repo, e `agents-setup-repo` copre quel vuoto.

| Pro | Contro |
|---|---|
| Hook con molti casi di prova già scritti | Alcune parti nascono in un contesto di lavoro e vanno ripulite |

**Fonti:** Scelta dell'utente, 8/11/2026; storico git e confronto dei due repo, 8/11/2026.

## 2. Via Delphi e i percorsi Windows

**Scelta:** esclusi hook BOM, MCP Delphi, `update-mcp.bat`, errori `BUILD-*` e riferimenti aziendali. Il setup deve funzionare su Mac e Windows.

**Perché:** il repo è personale e generico; quel materiale riguarda un contesto di lavoro specifico.

| Pro | Contro |
|---|---|
| Repo riusabile su ogni progetto | Tornando a Delphi quei controlli vanno riportati |

**Fonti:** Scelta dell'utente, 8/11/2026; storico git del 7z, 8/11/2026.

## 3. Ticket senza percorsi né righe

**Scelta:** il ticket descrive il comportamento e una verifica eseguibile. L'esecutore trova i punti cercando nel codice.

| Pro | Contro |
|---|---|
| Non invecchia | Un modello economico può cercare di più |

**Fonti:** [`to-tickets`](https://github.com/mattpocock/skills) di Matt Pocock e [guida Claude Code](https://code.claude.com/docs/en/best-practices) sulla verifica eseguibile, lette l'8/11/2026. Nessuna fonte misura il confronto.

## 4. Gemini implementa e rivede da solo

**Scelta:** Claude decide e scrive i ticket. Gemini implementa, lancia la review, corregge. L'utente prova se serve. Niente copia-incolla di prompt.

| Pro | Contro |
|---|---|
| Un revisore a contesto pulito non è influenzato da chi ha scritto | Stesso modello: secondo sguardo, non più intelligenza |
| L'utente resta sulla prova finale | Nessun umano legge il diff |

**Fonti:** [antirez, luglio 2026](https://antirez.com/news/169), a favore di controllare idee e test; [Karpathy, aprile 2026](https://karpathy.bearblog.dev/sequoia-ascent-2026/) (sintesi AI riletta da lui), a favore di ispezionare i diff; [subagenti Antigravity](https://antigravity.google/docs/subagents).

## 5. Doppia Review con 3 subagenti, commit alla fine

**Scelta:** Standards e Spec con le istruzioni di `code-review`, più `ponytail-review`. Ricevono il diff dopo `git add -N -- . ':(exclude).scratch'`: `.scratch/` resta fuori così una spec in corso non entra nella review. Il commit arriva dopo review, correzioni ed eventuale prova.

**Perché:** la skill `code-review` intera legge solo il già committato. I ticket piccoli usano `Review: quick`.

| Pro | Contro |
|---|---|
| Tre letture indipendenti a contesto pulito | Più quota per ticket: non misurata |

**Fonti:** Scelta dell'utente, 8/11/2026; `code-review/SKILL.md` di Matt Pocock; [Git, gitglossary](https://git-scm.com/docs/gitglossary) per `exclude`; [Google, Subagents](https://antigravity.google/docs/subagents) per `invoke_subagent`, lette l'8/11/2026.

## 6. Un branch per spec, niente worktree

**Scelta:** i ticket di una spec stanno sullo stesso branch, un ticket Gemini alla volta. Il merge lo fa l'utente. Il parallelo è Gemini che implementa mentre Claude progetta la spec successiva.

| Pro | Contro |
|---|---|
| Nessun costo di worktree per ticket piccoli | Un solo ticket Gemini alla volta |

**Fonti:** Scelta dell'utente, 8/11/2026: alcuni ticket sono piccoli e un branch copre una o più spec. Nessuna misura.

## 7. Base Matt Pocock, idee da Superpowers

**Scelta:** si resta sulle skill di Matt. Da Superpowers si prende l'idea di un ticket che basti a chi non ha contesto.

**Fonti:** [README di Matt](https://github.com/mattpocock/skills) e [README di Superpowers](https://github.com/obra/superpowers), attivi a novembre 2026; [Umar, ottobre 2026](https://umaranis.com/2026/10/25/superpowers-vs-matt-pococks-skills/), nessun vincitore netto; [Eberhardt, ottobre 2026](https://blog.scottlogic.com/2026/10/19/an-honest-review-of-matt-pococks-skills.html), risultati misti.

## 8. Matt come skill, ponytail e ADHD come plugin

**Scelta:** le skill semplici stanno in `~/.agents/skills` per entrambi gli agenti; ponytail e i-have-adhd restano plugin.

| Pro | Contro |
|---|---|
| Una versione sola per Claude e Gemini | Niente auto-update: serve il ramo Aggiorna |
| Matt non offre un plugin per Antigravity | Il nome `code-review` coincide con quello integrato in Claude |

**Fonti:** repo `mattpocock/skills` (solo `.claude-plugin/`, controllato l'8/11); migrazione del 7z del 19/10/2026; hook di `i-have-adhd` e `ponytail`.

## 9. Regola dei modelli senza prezzi

**Scelta:** Flash quando l'errore si vede da test o build, Argon quando si scopre tardi. Prezzi e punteggi restano fuori dai file.

**Perché:** invecchiano; Argon cambia prezzo dopo il 30 novembre 2026.

**Fonti:** [Google, Gemini 4 Argon](https://ai.google.dev/gemini-api/docs/latest-model), che consiglia di provare tutti i livelli. Il costo per ticket non è misurato.

## 10. Mintlify resta

**Scelta:** ogni repo tiene la sua guida in `docs/` con Mintlify e `junior-deep-docs`.

| Pro | Contro |
|---|---|
| Guida navigabile, utile per capire il sistema | Aggiornarla a ogni ticket costa token |

**Fonti:** Scelta dell'utente, 8/11/2026; flusso del 7z; [Mintlify, Mermaid](https://www.mintlify.com/docs/components/mermaid-diagrams), letta l'8/11/2026.

## 11. Setup eseguito dall'agente

**Scelta:** `SETUP.md` si rivolge all'agente, con tre rami: Installa, Aggiorna, Cerca MCP. Sostituisce `install.sh` e `update.sh`, che erano solo bash.

| Pro | Contro |
|---|---|
| Stesso percorso su Mac e Windows | Un documento di installazione può guidare l'agente verso azioni dannose |

**Mitigazione:** l'agente mostra le fonti esterne e attende l'ok.

**Fonti:** [arXiv 2603.11862](https://arxiv.org/pdf/2603.11862), solo anteprima di ricerca, letta a novembre 2026; Scelta dell'utente, 8/11/2026.

## 12. Aggiornamenti su richiesta

**Scelta:** autoUpdate per i plugin Claude, e il ramo Aggiorna per tutto il resto, con report dei cambi prima di applicare.

**Perché:** il controllo a ogni avvio del 7z era costato circa 500 righe e 3-8 secondi con falsi errori, ed era stato tolto.

| Pro | Contro |
|---|---|
| Vedi i cambiamenti prima di applicarli | Se non lo lanci resti indietro |

**Fonti:** [marketplace Claude Code](https://code.claude.com/docs/it/discover-plugins); decisione n. 1 di `pulizia-repo` nel 7z.

## 13. Ricerca MCP guidata

**Scelta:** l'agente traccia il profilo dell'utente, cerca, filtra e propone al massimo 5 server. Installa solo ciò che l'utente sceglie.

**Perché:** i server MCP possono portare istruzioni malevole nelle descrizioni dei tool, e il registro ufficiale non ordina per qualità.

**Fonti:** [MCP, sicurezza](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices) e [OWASP MCP](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html), solo anteprima di ricerca; prova diretta del registro l'8/11.

## 14. Non portato per ora

- Le pagine `docs/` lunghe del 7z, circa 1.250 righe scritte attorno a Delphi: al loro posto c'è la mappa in `docs/index.mdx`.
- `CODING_STANDARDS.md` del 7z: regole di codice per quel contesto.
- `.scratch/` del 7z: storia di lavoro con riferimenti aziendali.
- `docs/prompting-guide.md` e `gemini-web/` di `agents-setup-repo`: l'Executor Prompt non serve più col passaggio su disco.

## 15. Ogni affermazione ha una fonte

**Scelta:** ogni affermazione su strumenti, modelli o pratiche dice dove si legge: pagina ufficiale con data, autore con data, codice o comando eseguito. Bastano file e funzione. Ciò che manca di fonte è `non verificato`.

| Pro | Contro |
|---|---|
| Puoi controllare ogni frase | Ogni risposta costa più ricerca: non misurata |

**Fonti:** Scelta dell'utente, 8/11/2026; skill `aim-higher`, regole 1 e 2.

## 16. Regole Antigravity in `config/rules/`

**Scelta:** la sincronizzazione scrive `rules/claude-md.md` e lascia `~/.gemini/GEMINI.md` agli import dei plugin.

| Pro | Contro |
|---|---|
| Letto da App, CLI e IDE | Tutte le regole globali condividono un budget di 20.000 token |

**Fonti:** [Google, Rules](https://antigravity.google/docs/rules/), letta l'8/11/2026: l'IDE non elenca `~/.gemini/config/GEMINI.md`, e ogni file si tronca oltre 24.000 byte. Il limite per file è controllato in `tests/run.py`.

## 17. La sincronizzazione non cancella

**Scelta:** agenti e knowledge presenti solo in Antigravity vengono segnalati e restano al loro posto.

| Pro | Contro |
|---|---|
| Nessuna perdita di dati, anche nel ramo Aggiorna | Un agente tolto da Claude va rimosso a mano |

**Fonti:** prova su una home finta, 8/11/2026: la versione precedente li cancellava; `tests/run.py` ora lo controlla.

## 18. Diagrammi e tabelle per capire

**Scelta:** tabella dei ticket con `flowchart TD` delle dipendenze, Walkthrough a fine ticket, diagramma e tabella `Cosa, Perché, Fonte` a fine lavoro, mappa in `docs/index.mdx`. Si nominano file e funzioni, senza righe.

| Pro | Contro |
|---|---|
| Capisci il flusso senza leggere tutto il codice | Più testo a ogni consegna |

**Fonti:** Scelta dell'utente, 8/11/2026; flusso del 7z; [Mermaid, Flowcharts](https://mermaid.js.org/syntax/flowchart.html) per `TD`; [Google, Walkthrough](https://antigravity.google/docs/walkthrough/), letta l'8/11/2026, che documenta il riepilogo ma non i diagrammi: il rendering Mermaid in Antigravity è `non verificato`.

## 19. Impostazioni e blocchi mantenuti

**Scelta:** restano `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`, `autoCompactWindow`, i preset di Antigravity e il blocco dei file `.ini`.

| Pro | Contro |
|---|---|
| Già nella configurazione reale dell'utente; il blocco `.ini` protegge i segreti | `permissionPreset` e `autoExecutionPolicy` non hanno una chiave documentata |

**Fonti:** `install.sh` di `agents-setup-repo` e `config.json` reale, 8/11/2026; [Claude Code, Subagents](https://code.claude.com/docs/en/sub-agents): la variabile è un default, quindi un modello indicato per il subagente, come Haiku, ha la precedenza; [Claude Code, Settings reference](https://code.claude.com/docs/en/settings-reference); [Google, Settings](https://antigravity.google/docs/settings/) documenta solo `enableTerminalSandbox`. Gli altri due sono `non verificati`.

## 20. Rilievi delle review non applicati

- Analizzatore dei comandi scritto due volte: Claude esegue Python e Antigravity Node, e `tests/run.py` prova gli stessi casi su entrambi.
- `sync-from-claude.py` in un solo file: è una sequenza lineare e dividerla aggiungerebbe solo importazioni.
- Lista dei divieti ripetuta in `SETUP.md`, sincronizzazione e test: una è l'istruzione, una il controllo, una il dato di prova.
- `C:\Repos\GIT\app` in `tests/run.py`: è un percorso generico che prova il caso di una cartella chiamata `GIT`.

**Fonti:** rilettura del codice, 8/11/2026.
