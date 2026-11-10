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

## 8. Matt come skill, ponytail come plugin

**Scelta:** le skill semplici stanno in `~/.agents/skills` per entrambi gli agenti; ponytail resta plugin.

| Pro | Contro |
|---|---|
| Una versione sola per Claude e Gemini | Niente auto-update: serve il ramo Aggiorna |
| Matt non offre un plugin per Antigravity | Il nome `code-review` coincide con quello integrato in Claude |

**Fonti:** repo `mattpocock/skills` (solo `.claude-plugin/`, controllato l'8/11); migrazione del 7z del 19/10/2026; hook di `ponytail`.

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

## 21. Analisi e allineamento di un repo in `SETUP-REPO.md`

**Scelta:** un file separato da `SETUP.md`, che prima analizza memorie e trascrizioni di Claude e Gemini per capire la causa degli errori, poi allinea il repo. Una regola entra in `AGENTS.md` solo come ultima opzione e solo se supera il filtro del passo 6.

| Pro | Contro |
|---|---|
| Le regole nascono da prove e cause, e `AGENTS.md` resta corto | Leggere molte trascrizioni costa tempo e quota: non misurato |

**Fonti:** scelta dell'utente, 8/11/2026; `bootstrap.md` di `agents-setup-repo`; skill `/retro` di Matt Pocock; [Anthropic, Memory](https://code.claude.com/docs/en/memory) e [Best practices](https://code.claude.com/docs/en/best-practices); [AGENTS.md](https://agents.md/); [Google, Rules](https://antigravity.google/docs/rules/) e [Hooks](https://antigravity.google/docs/hooks/), lette l'8/11/2026.

## 22. Via `i-have-adhd`

**Scelta:** disinstallato da Claude Code e Antigravity e tolto dal setup. Al suo posto, una regola di stile in `personal/global.md`.

| Pro del toglierlo | Contro del toglierlo |
|---|---|
| 7.201 byte di istruzioni in meno in ogni sessione (`SKILL.md` del plugin, misurato l'8/11/2026), e spazio nel budget di 20.000 token delle regole globali di Antigravity | Sparisce il formato con l'azione in prima riga, comodo nelle emergenze: non misurato |
| Niente conflitto con le spiegazioni complete e le fonti richieste | |

**Fonti:** scelta dell'utente, 8/11/2026; decisione 14 di `pulizia-repo` nel 7z, archivio privato; README del plugin, che non cita studi sull'efficacia, letto l'8/11/2026; [Google, Rules](https://antigravity.google/docs/rules/), letta l'8/11/2026.

## 23. Il setup spiega mentre installa

**Scelta:** prima di installare, l'agente chiede cosa la persona conosce, spiega solo ciò che manca usando `GUIDE.md`, e alla fine propone al massimo 3 idee e raccoglie le sue.

| Pro | Contro |
|---|---|
| Un collega impara mentre configura | L'installazione dura di più: non misurato; si può rispondere `salta` |

**Fonti:** scelta dell'utente, 8/11/2026. Nessuna misura.

## 24. Il repo è pubblico: ciò che è di una macchina resta su quella macchina

**Scelta:** il repo contiene solo ciò che serve a tutti, come le [skill di Matt Pocock](https://github.com/mattpocock/skills). Scartato un server MCP presente su una sola macchina, proposto durante un'installazione per far passare `--check`.

| Pro | Contro |
|---|---|
| Un collega installa senza ereditare percorsi e dati di altri | Ogni macchina registra a mano i propri server |
| `mcp.json` resta valido su Mac e Windows (decisione 2) | `--check` mostra i server presenti su una sola macchina come avviso e non li controlla |

**Fonti:** scelta dell'utente, 8/11/2026. Nessuna misura.

## 25. Il formato dei commit lo controlla un hook

**Scelta:** `attribution` di Claude Code con `commit` e `pr` vuoti e `sessionUrl = false`, e un hook `commit-msg` che accetta solo `tipo(ambito): descrizione`, una riga, al massimo 15 parole, senza `Co-Authored-By`; passano anche `merge: ...` e i messaggi che git scrive da solo per merge e revert. I co-author già presenti nella storia restano.

| Pro | Contro |
|---|---|
| La regola vale anche quando un agente la dimentica | Si aggira con `--no-verify` |
| La storia e i branch condivisi non cambiano | I vecchi co-author restano visibili |

**Fonti:** scelta dell'utente, 8/11/2026; [Anthropic, All settings](https://code.claude.com/docs/en/settings-reference.md) per `attribution`; [Git, githooks](https://git-scm.com/docs/githooks) per `commit-msg`, lette l'8/11/2026. Che l'app desktop rispetti `attribution` è `non verificato`.

## 26. `Status: resolved` entra nel commit del ticket, e niente `/implement`

**Scelta:** `Status: resolved` si scrive subito prima del commit, senza hash. `/implement` si aggiunge a `/implement-spec` tra le skill da non usare; la skill resta installata, perché una modifica locale si perderebbe all'aggiornamento.

**Perché:** un commit non può contenere il proprio hash, quindi la vecchia regola lasciava il ticket modificato dopo ogni commit. `/implement` termina con un commit, mentre il flusso lo fa solo dopo l'ok dell'utente.

| Pro | Contro |
|---|---|
| Il branch resta pulito dopo ogni ticket | L'hash non si legge nel ticket: serve `git log -- <ticket>` |
| Stato e `## Answer` viaggiano insieme | Il divieto di `/implement` è una regola scritta, nessun hook lo impone |

**Fonti:** scelta dell'utente, 8/11/2026; `implement/SKILL.md` di Matt Pocock, letta l'8/11/2026. Nessuna misura.

## 27. Via `write-docs`; `aim-higher`, `ui-ux-doctrine` e `junior-deep-docs` riscritte in inglese

**Scelta:** `write-docs` esce dal setup. Le altre tre skill dell'utente sono riscritte in inglese con `writing-for-agents`: niente esempi Delphi, niente `file:riga` né copertura "righe 1..N", citazioni per file e funzione, un criterio di fine esplicito («Done when»). `ui-ux-doctrine` tiene solo numeri con una fonte: i 24 px dei bersagli da WCAG 2.2 e i limiti di risposta di Nielsen (0,1 s, 1 s, 10 s). `aim-higher` prende la versione "principio e causa" invece di quella basata sul metodo di Felix Rieseberg (Altitude, Depth, Range: l'obiettivo dietro l'obiettivo, il lavoro da esperto, le idee da campi vicini).

**Perché:** `write-docs` è la skill ufficiale di GitBook per gli spazi GitBook, la loro sincronizzazione con un repo Git (Git Sync) e le change request; qui la guida è Mintlify e `SUMMARY.md` serve solo per compatibilità. Le skill sono in inglese come le altre installate, e la lingua delle risposte resta una sola regola, in `personal/global.md`. La versione Rieseberg di `aim-higher` chiedeva di arrivare fino al «Rung 3 (Durable Engine)», un meccanismo che renda obsoleto il lavoro futuro, e di trattare ogni obiettivo difficile come ragionevole: due spinte ad allargare il lavoro, contro la regola Scope di `shared/global.md`.

| Pro | Contro |
|---|---|
| Una descrizione in meno nel contesto di ogni sessione | Chi pubblica su GitBook deve installarla da sé: `npx skills add GitBookIO/gitbook-skills` |
| Le tre skill non citano più Delphi né un repo specifico (controllato con `grep`) | Le versioni nuove non sono ancora provate su un lavoro reale |

**Fonti:** scelta dell'utente, 10/11/2026; `SKILL.md` della vecchia `aim-higher`, Altitude e regola 5, letta il 10/11/2026; [GitBook, AI coding assistants and SKILL.md](https://gitbook.com/docs/getting-started/ai-documentation/ai-coding-assistants-and-skillmd), letta il 10/11/2026; [W3C, Understanding SC 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), letta il 10/11/2026. I limiti di Nielsen vengono da fonti secondarie viste in ricerca il 10/11/2026, [video NN/g](https://www.nngroup.com/videos/3-response-time-limits-interaction-design/) e [Nielsen, Time Scales of UX](https://jakobnielsenphd.substack.com/p/time-scale-ux): l'articolo originale non è stato letto. Nessuna misura.

## 28. Le skill dell'utente vivono nel repo, gli agenti le leggono tramite link

**Scelta:** `aim-higher`, `junior-deep-docs` e `ui-ux-doctrine` stanno in `skills/` di questo repo. Sulla macchina, `~/.agents/skills/<nome>` è un link alla cartella del repo; `~/.claude/skills/<nome>` è un link a `~/.agents/skills/<nome>`, e Antigravity le vede da `~/.gemini/config/skills`, che dove la CLI `skills` l'ha creato è già un link a `~/.agents/skills`. Esiste così una sola copia di ogni skill.

**Perché:** prima stavano solo sulla macchina, senza storia né review, e chi installava il setup non le riceveva. Nessuno dei due agenti legge `~/.agents/skills` da solo: Claude Code carica `~/.claude/skills` e segue i link; Antigravity carica `~/.gemini/config/skills`, oppure le cartelle indicate in `~/.gemini/config/skills.json`.

| Pro | Contro |
|---|---|
| Diff, review e commit anche per le skill | Se la cartella del repo si sposta o sparisce, i link si rompono e le skill spariscono da entrambi gli agenti |
| Chi installa il setup le riceve | Su Windows i link sono junction: il comportamento lì è `non verificato` |

**Fonti:** scelta dell'utente, 10/11/2026; [Anthropic, Skills](https://code.claude.com/docs/en/skills), tabella delle posizioni e frase sui link simbolici; [Google, Skills](https://antigravity.google/docs/skills) e [Google, Customization discovery](https://antigravity.google/docs/customization-discovery) per `~/.gemini/config/skills` e `skills.json`; tutte lette il 10/11/2026. Che `~/.gemini/config/skills` sia un link è stato visto con `ls -ld` su questo Mac. Un link rotto lo segnala `sync-from-claude.py --check`, provato in `tests/run.py`. Nessuna misura.

## 29. Un contrarian smonta i ticket prima del codice

**Scelta:** alla fine di `/to-tickets`, prima della tabella di consegna, Opus lancia l'agente `contrarian` (`agents/contrarian.md`): un subagente a contesto pulito che fa il premortem dei ticket, cioè immagina che siano già falliti e cerca perché. Ha tutti gli strumenti: cerca nel codice, sul web, nella documentazione e nei server MCP, e può scrivere ed eseguire script di verifica nella sua cartella `.scratch/<lavoro>/contrarian/`. Ogni obiezione cita una prova riapribile. Opus confronta `git status --short` e le impronte dei file di spec e ticket prima e dopo, per vedere che siano intatti, ricontrolla le prove, scarta quelle smentite e segna `non verificato` quelle che non riesce a controllare; l'utente sceglie cosa cambiare. Modello, livello e quando si salta li dice il file dell'agente. Sulla macchina `~/.claude/agents/just-develop` è un link a `REPO/agents`. L'agente esiste solo in Claude Code: il campo `antigravity: false` dice a `sync-from-claude.py` di non copiarlo, perché `gemini_agent()` darebbe alla copia solo strumenti di lettura e `search_web`, e `/to-tickets` si fa comunque con Opus in Claude Code.

**Perché:** prima esisteva solo come riga nella guida ai modelli di `flow.md`, senza un momento né un formato. Chi ha scritto spec e ticket non vede i propri buchi. Che un errore trovato nei ticket costi meno di uno trovato in implementazione è `non verificato` per questo flusso. Limitare gli strumenti gli avrebbe tolto i server MCP e la possibilità di provare un'affermazione con un calcolo: la scelta dell'utente è dargli tutto e controllare dopo, invece di impedire prima.

| Pro | Contro |
|---|---|
| Un revisore che non ha visto il ragionamento non ne è influenzato | Chi riceve il compito di trovare problemi ne trova sempre: senza la regola della prova diventa rumore |
| Cerca ovunque e prova le affermazioni con script propri | Che scriva solo nella sua cartella è un'istruzione, non un blocco: lo controlla Opus dopo, confrontando le impronte dei file |
| Ogni obiezione è controllabile | Stesso modello: occhi nuovi, non una risposta più intelligente |
| | Non esiste in Antigravity |
| | Un subagente in più per ogni lavoro: costo non misurato |

**Fonti:** scelta dell'utente, 10/11/2026; [Anthropic, Best practices](https://code.claude.com/docs/en/best-practices), sezioni "By someone who didn't write the code" e "Know what subagents cost", letta il 10/11/2026; [Anthropic, Subagents](https://code.claude.com/docs/en/sub-agents), per i campi `model` ed `effort`, per i campi sconosciuti ignorati e per la lettura ricorsiva di `~/.claude/agents`, letta il 10/11/2026: la pagina non dice se segue una cartella collegata, quindi è `non verificato`; il premortem di Gary Klein, *Performing a Project Premortem* (Harvard Business Review, 2007), visto solo tramite fonti secondarie il 10/11/2026: lo studio citato misura più ragioni trovate, non ragioni più giuste. Nessuna misura su questo flusso.
