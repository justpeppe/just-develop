# SETUP

Istruzioni per l'agente che configura la macchina dell'utente. Esegui il ramo richiesto e spiega ogni passo in una frase di italiano semplice. `REPO` è la cartella di questo file.

| L'utente chiede di | Ramo |
|---|---|
| Installare o configurare | [Installa](#installa) |
| Aggiornare skill, plugin o MCP | [Aggiorna](#aggiorna) |
| Cercare MCP utili | [Cerca MCP](#cerca-mcp) |
| Analizzare o allineare un progetto | [`SETUP-REPO.md`](SETUP-REPO.md) |

## Regole di ogni ramo

- Rileva il sistema (Mac o Windows). `PY` è `python` se esiste, altrimenti `python3`.
- Prima di modificare un file di configurazione fuori da `REPO`, copialo accanto con suffisso `.bak-<data>`.
- Nei file JSON unisci le chiavi e conserva quelle esistenti. Salta ciò che è già corretto.
- Mostra all'utente le fonti esterne da cui scaricherai e attendi il suo ok: il repo è suo, il codice di queste fonti no.
- Nei comandi degli hook metti i percorsi tra virgolette (nel JSON `\"`): `REPO` può contenere spazi.
- Quando un passo dipende dal comportamento di uno strumento, leggi la sua pagina ufficiale e cita pagina e data nel report. Le pagine già controllate sono in `DECISIONS.md`. Ciò che non trovi scritto segnalalo come `non verificato`.
- Se trovi `i-have-adhd`, non fa più parte del setup (`DECISIONS.md`, decisione 22): dopo il sì dell'utente togli plugin e marketplace da Claude Code, il file `~/.claude/.i-have-adhd-always`, e da Antigravity copia, import in `~/.gemini/GEMINI.md` e voce in `config.json`.
- I segreti li inserisce l'utente nella configurazione del client. Nel repo finiscono solo i nomi delle variabili.
- Per Antigravity lavora sui file in `~/.gemini/`. Il comando `agy` da terminale si blocca: quando serve l'app, chiedi all'utente di provare lì.

## Fonti

Unica tabella di ciò che il setup installa e aggiorna.

| Fonte | Claude Code | Antigravity |
|---|---|---|
| `mattpocock/skills` | skill | skill |
| `blader/humanizer` | skill | skill |
| `anthropics/skills`: `skill-creator`, `pdf` | skill | skill |
| `vercel-labs/skills`: `find-skills` | skill | skill |
| `https://mintlify.com/docs` | skill | skill |
| `DietrichGebert/ponytail` | plugin | clone in `~/.gemini/config/plugins/` |
| Server in `REPO/mcp.json` | MCP utente | `~/.gemini/config/mcp_config.json` |

Ponytail resta plugin perché il suo hook lo tiene sempre attivo. Le altre fonti sono solo skill: la CLI tiene una copia in `~/.agents/skills` e la collega a entrambi gli agenti.

Skill dell'utente, senza fonte pubblica nota: `junior-deep-docs`, `ui-ux-doctrine`, `write-docs`, `aim-higher`. Se ne manca una, elencala nel report finale e continua. Se una di queste esiste in `~/.agents/skills/<nome>` ma non in `~/.claude/skills/<nome>`, collegala lì con un link simbolico (su Windows una junction), altrimenti Claude Code non la vede.

## Installa

**Prima dei passi, conosci chi installa.** Può essere un collega o un amico che vede tutto questo per la prima volta. Chiedi una cosa alla volta, e accetta `salta`:

- Hai già usato Claude Code o Antigravity? Su cosa lavori?
- Sai cosa sono skill, plugin, hook, MCP e subagenti? Li hai mai usati?
- Conosci il lavoro di Matt Pocock, Karpathy o antirez? E la differenza tra vibe coding e lavorare da una spec?

Per ogni concetto che non conosce usa la sezione `Se parti da zero` di `GUIDE.md`: spiega cos'è e quando serve, con un esempio preso dal suo lavoro. Chi conosce già un concetto non lo risente. Durante i passi dì cosa stai facendo e a quale concetto corrisponde. Se `personal/global.md` riflette le preferenze di un'altra persona, chiedi cosa tenere prima di importarlo.

1. **Controlla i prerequisiti.** Servono `git`, `node`, `npx`, `PY`, `claude` (2.1.295 o successiva, per `onFailure`) e la cartella `~/.gemini/config`. Mostra la tabella Fonti e i file che modificherai. *Fatto quando* l'utente conferma.
2. **Fai i backup** di `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude.json`, `~/.gemini/GEMINI.md` e dei file `hooks.json`, `mcp_config.json`, `skills.json`, `config.json` e delle cartelle `rules/`, `agents/`, `knowledge/` in `~/.gemini/config/`, quando esistono. *Fatto quando* ogni file esistente ha la sua copia.
3. **Attiva i controlli git** (`pre-commit` e `commit-msg`), se `REPO` è un repository git: `git -C REPO config core.hooksPath hooks/git`.
4. **Installa le skill.** Per ogni fonte di tipo skill:
   - Elenca i nomi con `npx -y skills@latest add <fonte> --list`, che non installa nulla, e confrontali con `~/.agents/.skill-lock.json`. Un nome già presente da un'altra fonte verrebbe sovrascritto: chiedi all'utente.
   - Installa con `npx -y skills@latest add <fonte> -g -y -a claude-code -a antigravity -s <nomi>`.
   - Controlla la collisione: se il nome `code-review` non apre la skill di Matt su Claude Code, segnalalo.
   - Disinstalla i plugin che duplicano queste skill, come `mattpocock-skills@mattpocock`, `humanizer@humanizer` e `skill-creator@claude-plugins-official`, dopo il sì dell'utente.

   *Fatto quando* ogni skill ha il suo `SKILL.md` in `~/.claude/skills/<nome>` e in `~/.gemini/config/skills/<nome>` e nessun plugin la duplica.
5. **Installa i plugin.**
   - Claude Code: `claude plugin marketplace add <owner/repo>`, poi `claude plugin install ponytail@ponytail`. Imposta `extraKnownMarketplaces.<nome>.autoUpdate = true` in `~/.claude/settings.json`.
   - Antigravity: `git clone --depth 1 https://github.com/<owner/repo> ~/.gemini/config/plugins/<nome>` e `.plugins.<nome>.enabled = true` in `~/.gemini/config/config.json`. In `~/.gemini/GEMINI.md` aggiungi `@[ponytail](<plugins>/ponytail/AGENTS.md)`.

   *Fatto quando* `claude plugin list` lo mostra e la cartella esiste.
6. **Importa le regole.** In `~/.claude/CLAUDE.md` aggiungi `@REPO/shared/global.md`, `@REPO/personal/global.md` e `@REPO/flow.md`. Se trovi import verso un vecchio repo di configurazione, mostrali e sostituiscili dopo il sì dell'utente. *Fatto quando* le tre righe sono presenti una volta sola.
7. **Configura i guardrail di Claude Code** in `~/.claude/settings.json`:
   - `permissions.deny`: `Bash(git push *)`, `Bash(git merge *)`, `PowerShell(git push *)`, `PowerShell(git merge *)`, `Read(//**/*.ini)`, `Read(//**/.env)`.
   - `hooks.PreToolUse`: matcher `Bash|PowerShell`, comando `PY -I REPO/hooks/claude/block-dangerous-git.py`, `"type": "command"`, `"onFailure": "block"`.
   - `env.CLAUDE_CODE_SUBAGENT_MODEL = "sonnet"` e `autoCompactWindow = 400000`.
   - Chiave di primo livello `attribution` con `commit = ""`, `pr = ""` e `sessionUrl = false`: niente co-author nei commit.
   - Hook git di un setup precedente: mostrali e toglili dopo il sì dell'utente, perché questo li copre.
8. **Configura i guardrail di Antigravity** in `~/.gemini/config/hooks.json`, con `PreToolUse` in due voci:
   - `git-guardrails`: matcher `run_command`, comando `node REPO/hooks/antigravity/block-dangerous-git.js`.
   - `secrets-guardrails`: matcher `run_command|read_file|view_file|grep_search|list_dir|find_by_name|call_mcp_tool|mcp_.*|read_resource`, comando `node REPO/hooks/antigravity/block-secrets-read.js`.

   In `~/.gemini/config/config.json` imposta `userSettings.permissionPreset = "AGENT_PERMISSION_PRESET_DEFAULT"`, `userSettings.enableTerminalSandbox = true` e `userSettings.autoExecutionPolicy = "CASCADE_COMMANDS_AUTO_EXECUTION_PROCEED_IN_SANDBOX"`.
9. **Sincronizza Antigravity** con `PY -I REPO/scripts/sync-from-claude.py`. Scrive regole, agenti e `skills.json`. Un server MCP `extra` in `--check` è un avviso: esiste solo su questa macchina e resta nella configurazione del client, fuori da `REPO/mcp.json`. *Fatto quando* la sincronizzazione esce 0.
10. **Verifica.**
    - `PY -I REPO/tests/run.py` stampa `ok`.
    - `PY -I REPO/scripts/sync-from-claude.py --check` esce 0.
    - Chiedi all'utente di aprire Claude Code e controllare con `/` che le skill ci siano, poi di aprire il pannello Customizations di Antigravity e far eseguire `git status` a Gemini.
    - `REPO/hooks/antigravity/block-dangerous-git.log` ha una riga nuova con l'ora della prova: è la prova che l'hook gira.
11. **Riporta** cosa funziona ora, cosa manca e le skill dell'utente assenti. Mostra con il diagramma di `GUIDE.md` come si incastrano i pezzi, e proponi di provare il giro su una piccola modifica reale.
12. **Rifinisci insieme.** Chiedi cosa vorrebbe cambiare e cosa non è chiaro. In base a ciò che ti ha raccontato proponi al massimo 3 idee, ognuna con pro, contro e fonte, tra cui il ramo Cerca MCP e `SETUP-REPO.md` per un suo progetto. Le sue idee e le tue passano dal filtro del passo 6 di Analizza in `SETUP-REPO.md`. Applica solo ciò che sceglie. *Fatto quando* l'utente sa fare da solo un giro completo o ha scelto di fermarsi.

## Aggiorna

1. **Scopri cosa cambia, senza applicare nulla.**
   - Skill: `npx -y skills@latest check`.
   - Plugin Claude: `claude plugin marketplace update <nome>`, poi confronta la versione in `plugin.json` con quella installata.
   - Clone Antigravity: `git -C <clone> fetch`, poi `git -C <clone> log --oneline HEAD..@{u}`.
   - MCP: per ogni server di `REPO/mcp.json` cerca l'ultima versione sulla sua fonte ufficiale. Un server con `url` si aggiorna da solo; uno lanciato con `npx` o `uvx` dipende dalla versione indicata; un binario va scaricato dalla release.

   Mostra per ogni fonte la versione attuale, la nuova e i cambi di comportamento letti dal changelog. *Fatto quando* l'utente ha scelto cosa aggiornare.
2. **Salva il punto di ritorno:** copia `~/.agents/skills` e `~/.agents/.skill-lock.json` in `~/.agents/skills-backup`, sostituendo la copia precedente.
3. **Applica** ciò che l'utente ha scelto: `npx -y skills@latest update -g -y`, `claude plugin update <plugin>@<marketplace>`, `git -C <clone> pull --ff-only`. Per un server MCP: cambia la versione in `REPO/mcp.json` e nei client, o riscarica il binario dalla release, poi prova un tool. Per un `skills-lock.json` nel progetto corrente chiedi prima, poi `npx -y skills@latest update -p -y`. Dopo l'update controlla se la CLI ha creato cartelle per agenti che l'utente non usa e segnalale.
4. **Riallinea e verifica** con il passo 9 e il passo 10 di Installa.
5. **Riporta** cosa è cambiato, cosa è rimasto indietro e come tornare alla copia in `~/.agents/skills-backup`.

## Cerca MCP

Un server MCP dà all'agente accesso a dati e azioni e può portare istruzioni malevole nelle descrizioni dei tool. Proponi pochi server e installa solo ciò che l'utente sceglie.

1. **Traccia il profilo.** Chiedi all'utente su cosa lavora e quali servizi usa. Leggi i manifest dei repo che indica (`package.json`, `pyproject.toml` e simili) e gli MCP già presenti in `REPO/mcp.json` e nella configurazione dei client. *Fatto quando* hai un elenco di attività ricorrenti che un agente oggi non può svolgere bene.
2. **Cerca con fonti attuali.** Per ogni attività cerca nella documentazione ufficiale del servizio, poi nel registro `https://registry.modelcontextprotocol.io/v0.1/servers?search=<termine>&version=latest`, poi sul web. Il registro non ordina per qualità. Annota fonte e data di ogni risultato.
3. **Filtra.** Tieni un server quando:
   - l'editore è identificabile, meglio se è il fornitore del servizio;
   - il codice è pubblico e mantenuto di recente;
   - funziona su Mac e Windows, con Claude Code e Antigravity;
   - chiede i permessi minimi;
   - fa ciò che una CLI già installata (per esempio `gh`) non fa;
   - le descrizioni dei tool parlano solo del loro compito.
4. **Proponi al massimo 5 server**, dal più utile, ciascuno con: cosa migliora, pro, contro, fonte con data, permessi e credenziali richiesti, comando di installazione. *Fatto quando* l'utente ha scelto.
5. **Installa i server scelti.** Aggiungili a `REPO/mcp.json` e registrali su Claude Code (`claude mcp add -s user`) e in `~/.gemini/config/mcp_config.json`. Fai inserire i segreti all'utente.
6. **Verifica** con `PY -I REPO/scripts/sync-from-claude.py --check`, poi con una chiamata reale a un tool di ogni server nuovo. Riporta l'esito.
