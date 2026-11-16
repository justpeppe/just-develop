# SETUP

Istruzioni per l'agente che configura la macchina dell'utente. Esegui il ramo richiesto e spiega ogni passo in una frase di italiano semplice. `REPO` è la cartella di questo file.

| L'utente chiede di | Ramo |
|---|---|
| Installare o configurare | [Installa](#installa) |
| Aggiornare skill, plugin o MCP | [Aggiorna](#aggiorna) |
| Cercare MCP utili | [Cerca MCP](#cerca-mcp) |
| Analizzare o allineare un progetto | [`SETUP-REPO.md`](SETUP-REPO.md) |

## Regole di ogni ramo

- Rileva il sistema (macOS, Linux o Windows). `PY` è `python` se esiste, altrimenti `python3`; esegui gli script del repo con `PY -X utf8 -I`.
- Prima di modificare un file di configurazione fuori da `REPO`, copialo accanto con suffisso `.bak-<data>`.
- Nei file JSON unisci le chiavi e conserva quelle esistenti. Salta ciò che è già corretto.
- Mostra all'utente le fonti esterne da cui scaricherai e attendi il suo ok: il repo è suo, il codice di queste fonti no.
- Nei comandi degli hook metti i percorsi tra virgolette (`\"` nel JSON): `REPO` può contenere spazi.
- Quando un passo dipende dal comportamento di uno strumento, leggi la sua pagina ufficiale e cita pagina e data nel report. Le pagine già controllate sono in `DECISIONS.md`. Ciò che non trovi scritto segnalalo come `non verificato`.
- Se trovi `i-have-adhd` (`DECISIONS.md`, decisione 22), `write-docs` (`DECISIONS.md`, decisione 27) o vecchie regole locali sostituite da `shared/global.md` e `flow.md`, proponi all'utente di rimuovere plugin/file/voci obsolete e `skills/write-docs`.
- I segreti li inserisce l'utente nella configurazione del client. Nel repo finiscono solo i nomi delle variabili.
- Per Antigravity lavora sui file in `~/.gemini/`. Il comando `agy` da terminale si blocca: quando serve l'app, chiedi all'utente di provare lì.

## Fonti

Tabella di ciò che il setup installa e aggiorna.

| Fonte | Claude Code | Antigravity |
|---|---|---|
| `mattpocock/skills` | skill | skill |
| `blader/humanizer` | skill | skill |
| `anthropics/skills`: `skill-creator`, `pdf` | skill | skill |
| `vercel-labs/skills`: `find-skills` | skill | skill |
| `https://mintlify.com/docs` | skill | skill |
| `DietrichGebert/ponytail` *(opzionale, spento di default in v2)* | plugin disattivato (`enabledPlugins`) | `plugins.ponytail.enabled = false` |
| Server in `REPO/mcp.json` | MCP utente | `~/.gemini/config/mcp_config.json` |

Skill di questo repo in `REPO/skills/`: `flow-design`, `implement-ticket`, `aim-higher`, `junior-deep-docs`, `ui-ux-doctrine`. La copia versionata vive in `REPO`: gli agenti la leggono tramite link simbolici o junction in `~/.agents/skills/`.

## Installa

**Prima dei passi, conosci chi installa.** Può essere un collega o un amico che vede tutto questo per la prima volta. Chiedi una cosa alla volta, e accetta `salta`:

- Hai già usato Claude Code o Antigravity? Su cosa lavori?
- Sai cosa sono skill, plugin, hook, MCP e subagenti? Li hai mai usati?
- Conosci il lavoro di Matt Pocock, Karpathy o antirez? E la differenza tra vibe coding e lavorare da una spec?

Per ogni concetto che non conosce usa la sezione `Se parti da zero` di `GUIDE.md`: spiega cos'è e quando serve, con un esempio preso dal suo lavoro. Chi conosce già un concetto non lo risente. Durante i passi dì cosa stai facendo e a quale concetto corrisponde. Se `personal/global.md` riflette le preferenze di un'altra persona, chiedi cosa tenere prima di importarlo.

1. **Controlla i prerequisiti.** Servono `git` (`>= 2.38` per `git merge-tree --write-tree`), `node`, `npx`, `PY`, `claude` (`>= 2.1.295` per `onFailure`) e la cartella `~/.gemini/config`. Mostra la tabella Fonti e i file che modificherai. *Fatto quando* l'utente conferma.
2. **Fai i backup** di `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude.json`, `~/.gemini/GEMINI.md` e dei file `hooks.json`, `mcp_config.json`, `skills.json`, `config.json` e delle cartelle `rules/`, `agents/`, `knowledge/` in `~/.gemini/config/`, quando esistono. *Fatto quando* ogni file esistente ha la sua copia.
3. **Attiva hook e configurazione Git** in `REPO` (se è un repository Git):
   - `git -C REPO config core.hooksPath hooks/git` (attiva `pre-commit`, `commit-msg`, `post-merge`, `post-checkout`, `post-rewrite`);
   - `git -C REPO config fetch.prune true` (allinea la rimozione dei branch chiusi tra PC; su GitHub abilita *Automatically delete head branches*).
4. **Installa e collega le skill.** Per ogni fonte esterna di tipo skill:
   - Elenca i nomi con `npx -y skills@latest add <fonte> --list` e confrontali con `~/.agents/.skill-lock.json`. Se un nome esiste già da un'altra fonte, chiedi all'utente prima di sovrascriverlo.
   - Installa con `npx -y skills@latest add <fonte> -g -y -a claude-code -a antigravity -s <nomi>`.
   - Controlla che `code-review` punti alla skill di Matt Pocock in Claude Code, e dopo il sì dell'utente disinstalla eventuali plugin che duplicano queste skill (`mattpocock-skills@mattpocock`, `humanizer@humanizer`, `skill-creator@claude-plugins-official`).
   - Collega tutte e **5** le skill di `REPO/skills/` (`flow-design`, `implement-ticket`, `aim-higher`, `junior-deep-docs`, `ui-ux-doctrine`): crea `~/.agents/skills/<nome>` come symlink (o junction su Windows con percorso assoluto) verso `REPO/skills/<nome>`, poi `~/.claude/skills/<nome>` verso `~/.agents/skills/<nome>`, e lo stesso in `~/.gemini/config/skills/<nome>` se `~/.gemini/config/skills` non è già un link a `~/.agents/skills`. Chiedi conferma se al posto del link esiste già una cartella reale.
   - Collega gli agenti di `REPO/agents/`: crea `~/.claude/agents/just-develop` come symlink o junction verso `REPO/agents`.

   *Fatto quando* tutte e 5 le skill di `REPO/skills/` compaiono in `~/.claude/skills/<nome>` e `~/.gemini/config/skills/<nome>`, e `~/.claude/agents/just-develop` punta a `REPO/agents`.
5. **Mantieni `ponytail` spento in entrambi i client.** In v2 `implement-ticket` include inline i 6 assi di review, quindi `ponytail` non serve a runtime:
   - In `~/.claude/settings.json` imposta `enabledPlugins."ponytail@ponytail": false` (se il plugin è presente).
   - In `~/.gemini/config/config.json` imposta `plugins.ponytail.enabled = false` ed evita `@[ponytail](...)` in `~/.gemini/GEMINI.md`.
   - Solo se l'utente chiede esplicitamente comandi come `/ponytail-audit` o `/ponytail-debt`, installa `ponytail` tenendolo disattivato fino all'uso.
6. **Importa le regole.** In `~/.claude/CLAUDE.md` scrivi solo i 3 `@import` verso `REPO`: `@REPO/shared/global.md`, `@REPO/personal/global.md`, `@REPO/flow.md`. Rimuovi eventuali import verso vecchi repo dopo il sì dell'utente. *Fatto quando* le tre righe compaiono una sola volta e senza duplicati inline.
7. **Configura Claude Code** in `~/.claude/settings.json`:
   - `permissions.deny`: `Bash(git push *)`, `Bash(git merge *)`, `PowerShell(git push *)`, `PowerShell(git merge *)`, `Bash(agy *)`, `PowerShell(agy *)`, `Read(//**/*.ini)`, `Read(//**/.env)`, `Read(//**/*.env)`.
   - `hooks.PreToolUse`: matcher `Bash|PowerShell`, comando `PY -X utf8 -I "REPO/hooks/claude/block-dangerous-git.py"`, `"type": "command"`, `"onFailure": "block"`.
   - `hooks.SessionStart`: matcher `startup`, comando portabile che cerca `python` prima di `python3` ed esegue `"REPO/scripts/session_check.py" --client claude` (es. `sh -c 'PY=$(command -v python || command -v python3); "$PY" -X utf8 -I "REPO/scripts/session_check.py" --client claude'`, `timeout: 10`).
   - `model`: `"sonnet"`; `env.CLAUDE_CODE_SUBAGENT_MODEL`: `"sonnet"`; rimuovi eventuale `CLAUDE_CODE_AUTO_COMPACT_WINDOW` o `autoCompactWindow` obsoleto (in v2 le chat ripartono pulite da `.scratch/`).
   - Chiave di primo livello `attribution`: `{"commit": "", "pr": "", "sessionUrl": false}`.
   - Rimuovi hook Git di un setup precedente dopo conferma dell'utente.
8. **Configura Antigravity** in `~/.gemini/config/hooks.json` e `config.json`:
   - `git-guardrails` (`PreToolUse`, matcher `run_command`): `node "REPO/hooks/antigravity/block-dangerous-git.js"`.
   - `secrets-guardrails` (`PreToolUse`, matcher `run_command|read_file|view_file|grep_search|list_dir|find_by_name|call_mcp_tool|mcp_.*|read_resource`): `node "REPO/hooks/antigravity/block-secrets-read.js"`.
   - `just-develop-session-check` (`SessionStart`, `enabled: true`): comando portabile `python`/`python3` che esegue `"REPO/scripts/session_check.py" --client antigravity` (`timeout: 10`).
   - In `~/.gemini/config/config.json` imposta `plugins.ponytail.enabled = false` e conserva `userSettings.permissionPreset = "AGENT_PERMISSION_PRESET_DEFAULT"`, `userSettings.enableTerminalSandbox = true` e `userSettings.autoExecutionPolicy = "CASCADE_COMMANDS_AUTO_EXECUTION_PROCEED_IN_SANDBOX"`.
9. **Sincronizza Antigravity** con `PY -X utf8 -I "REPO/scripts/sync-from-claude.py"`. Scrive regole (`shared.md`, `personal.md`, `flow.md`, omettendo `claude-md.md` quando `CLAUDE.md` contiene solo `@import`), agenti e `skills.json`, rispettando regole, agenti e server MCP locali extra. *Fatto quando* esce `0`.
10. **Verifica.**
    - `PY -X utf8 -I "REPO/tests/run.py"` stampa `ok`.
    - `PY -X utf8 -I "REPO/scripts/sync-from-claude.py" --check` esce `0`.
    - `PY -X utf8 -I "REPO/scripts/check-updates.py"` termina senza errori.
    - Chiedi all'utente di aprire Claude Code per verificare con `/` le skill, poi di aprire Antigravity e far eseguire a Gemini `git status` (passa) e un comando innocuo di branch come `git branch test-verify` (viene bloccato).
    - `REPO/hooks/antigravity/block-dangerous-git.log` registra la riga di `deny` (senza testo comando), provando che l'hook è attivo.
11. **Riporta** cosa funziona ora, cosa manca e le eventuali skill assenti. Mostra il diagramma di `GUIDE.md` e proponi una prima prova su una piccola modifica reale.
12. **Rifinisci insieme.** Chiedi cosa cambiare o chiarire, proponi al massimo 3 idee (tra cui `Cerca MCP` e `SETUP-REPO.md`) passando dal filtro del passo 6 di `SETUP-REPO.md`. Applica solo ciò che l'utente sceglie.

## Aggiorna

1. **Scopri cosa cambia, senza applicare nulla.**
   - Controllo rapido unificato via `git ls-remote` (zero limiti REST API GitHub) + stato cross-PC: `PY -X utf8 -I "REPO/scripts/check-updates.py"`.
   - Dettaglio skill: `npx -y skills@latest check`.
   - Plugin Claude (se abilitati): `claude plugin marketplace update <nome>`, poi confronta `plugin.json` con la versione installata.
   - Clone plugin Antigravity (se presenti): `git -C <clone> fetch`, poi `git -C <clone> log --oneline HEAD..@{u}`.
   - MCP: per ogni server in `REPO/mcp.json` verifica l'ultima versione dalla sua fonte ufficiale (`url` si aggiorna sul server; `npx`/`uvx` dal pacchetto; binari dalle release).

   Mostra versione attuale, nuova e cambi di comportamento. *Fatto quando* l'utente sceglie cosa aggiornare.
2. **Salva il punto di ritorno:** copia `~/.agents/skills` e `~/.agents/.skill-lock.json` in `~/.agents/skills-backup`, sostituendo la copia precedente. Salta le 5 junction verso `REPO/skills/`: vivono nella storia Git.
3. **Applica** solo ciò che l'utente ha scelto (`npx -y skills@latest update -g -y`, aggiornamento plugin/clone/MCP), verificando che la CLI non crei cartelle per agenti non usati.
4. **Riallinea e verifica** eseguendo il passo 9 e il passo 10 di Installa (`sync-from-claude.py`, `tests/run.py`, `--check`).
5. **Riporta** cosa è cambiato, cosa è rimasto invariato e come ripristinare `~/.agents/skills-backup`.

## Cerca MCP

Un server MCP dà all'agente accesso a dati e azioni e può portare istruzioni malevole nelle descrizioni dei tool. Proponi pochi server e installa solo ciò che l'utente sceglie.

1. **Traccia il profilo.** Chiedi su cosa lavora e quali servizi usa. Leggi i manifest dei repo che indica (`package.json`, `pyproject.toml` e simili) e gli MCP già presenti in `REPO/mcp.json` e nella configurazione dei client. *Fatto quando* hai un elenco di attività ricorrenti che un agente oggi non copre bene.
2. **Cerca con fonti attuali.** Cerca nella documentazione ufficiale del servizio, nel registro `https://registry.modelcontextprotocol.io/v0.1/servers?search=<termine>&version=latest` (non ordina per qualità) e sul web. Annota fonte e data.
3. **Filtra.** Tieni un server quando: editore identificabile, codice pubblico e mantenuto di recente, compatibile macOS/Windows e Claude/Antigravity, permessi minimi, utilità rispetto alle CLI installate e descrizioni pulite.
4. **Proponi al massimo 5 server**, ciascuno con: cosa migliora, pro, contro, fonte con data, permessi/credenziali richiesti, comando di installazione. *Fatto quando* l'utente sceglie.
5. **Installa i server scelti** in `REPO/mcp.json` (se generici e condivisibili) o nella sola configurazione locale del client (`claude mcp add -s user` e `~/.gemini/config/mcp_config.json`) se specifici della macchina. Fai inserire eventuali segreti all'utente.
6. **Verifica** con `PY -X utf8 -I "REPO/scripts/sync-from-claude.py" --check`, poi con una chiamata reale a un tool del nuovo server.
