Status: resolved

# Spec: Allineamento v2 (`Agents/config/{just-develop,delphi}`, branching cross-PC e flusso universale)

Fonti progettuali approvate: `.scratch/allineamento-just-develop/round2/09-architettura-v2.md` e override esplicito dell'utente sulla Review binaria (`quick` | `double` con 3 subagenti `inherit`, zero `Review: single`, zero `3.8 Flash`).

## Problem Statement

Oggi `<old-config-repo>` (PC Ufficio) e `justpeppe/just-develop` (PC Casa) divergono su hook, sync, modelli e workflow, mescolano codice pubblico generico con percorsi/regole Delphi/aziendali, e caricano un contesto always-on eccessivo (`~17 KB` in `flow.md` + `ponytail` runtime) che consuma velocemente i limiti di Claude Pro / Team e Antigravity. Inoltre mancano una strategia branch ordinata tra due PC, l'allineamento automatico di `~/.gemini/config/` su `pull`/`checkout` e un controllo silenzioso 8h/24h senza bloccare le pipe di `SessionStart`.

## Solution

1. **Due repository disaccoppiati sotto `<LOCAL_GIT_ROOT>\Agents\config\`:**
   - **`just-develop`** (pubblico su `github.com/justpeppe/just-develop`, branch `office/feat/allineamento-v2`, identità locale `justpeppe` / `trimarchig2002@gmail.com`): zero riferimenti aziendali o Delphi, branching a 3 livelli `office|home/<tipo>/<slug>`, guardrail unificati, sync automatico e flusso universale Claude Desktop/Code ↔ Antigravity 2.0.
   - **`delphi`** (solo locale su PC Ufficio, zero `remote`, con storico ricerche `22..28` e `pulizia-repo`): regole Delphi 13 Win64, hook BOM/CRLF e `delphi_git` read-only, `update-mcp.bat` e troubleshooting `delphi_build`.
2. **Branching, Sync e Controllo 8h/24h sicuri:**
   - Branching `office|home/<tipo>/<slug>` tutto minuscolo (`[a-z0-9-]`), merge non-squash su `main`, `fetch.prune=true`, creazione/cambio branch bloccati agli agenti.
   - Fix `commit-msg` (whitelist merge/revert/PR/IDEA multi-riga sopra il controllo 1-riga, `merge:` a 1 riga max 15 parole, no `Co-Authored-By`).
   - Hook Git `post-merge`, `post-checkout` e `post-rewrite` per mantenere `~/.gemini/config/` allineato al branch; controllo silenzioso 8h (Git + rilevatore cross-PC con `status --porcelain` + `merge-tree`) / 24h (`git ls-remote` sui repo `.skill-lock.json` + fetch plugin/asset) con lock kernel OS (`msvcrt.locking` / `fcntl.flock`) e spawn pipe-safe (`CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP` + `DEVNULL`).
3. **Flusso Universale `/writing-for-agents` & Review Binaria (`quick` | `double`):**
   - `flow.md` snello (`<= 3.000 B`) con checklist invariante di chiusura inline + skill `flow-design` e `implement-ticket` (`dmi: false`) indipendenti dal tool `Skill` di Claude.
   - **Review solo binaria:** **`Review: quick`** (`0` subagenti: modifiche meccaniche/testuali senza nuovo stato né nuovi rami logici) oppure **`Review: double`** (SEMPRE **3 subagenti paralleli su `inherit`**: `Standards` + `Spec` di Matt Pocock + `ponytail-review`, stesso modello del ticket). Nessuna fascia `single` e nessun `3.8 Flash`.
4. **Migrazione atomica preparata senza toccare la macchina live:**
   - Script PowerShell `%USERPROFILE%\.just-develop-local\switch-to-v2.ps1` pronto e verificato sintatticamente per effettuare a freddo lo switch di `settings.json`, `hooks.json`, `config.json` (`ponytail` spento anche in AGY), `CLAUDE.md` (solo `@import`), regole `delphi.md`, junction, eliminazione `delphi-researcher`/`write-docs` e spostamento degli archivi fuori da `<LOCAL_GIT_ROOT>`.

## User Stories

1. Come sviluppatore su due PC, voglio lavorare su `just-develop` con branch `office|home/<tipo>/<slug>` senza conflitti Directory/File né leak di dati Delphi/aziendali.
2. Come utente di Antigravity 2.0 e Claude Desktop/Code, voglio che gli agenti siano bloccati su `git push`, `git merge`, creazione/cambio branch, bypass `cmd /c`, lettura segreti e lettura integrale di file `.jsonl > 100 KB`, senza falsi positivi PowerShell su filtri negativi o `Select-String`.
3. Come utente, voglio che `commit-msg` accetti i messaggi reali di merge (con `Conflicts:` e PR multi-riga) e `revert`, mantenendo il formato `tipo(ambito): descrizione` in max 15 parole senza `Co-Authored-By`.
4. Come utente, voglio che `git pull`/`switch`/`rebase` riallineino subito `~/.gemini/config/` e che un check background non bloccante segnali novità Git (8h, incluse sovrapposizioni cross-PC) e Skill/Plugin/MCP (24h) in italiano semplice.
5. Come utente su piani Pro/Team/Ultra, voglio un nucleo `flow.md <= 3.000 B`, progettazione e implementazione eseguibili su entrambi i client e una review netta `quick` (0 subagenti, `S/G/C = 0/0/0`) o `double` (3 subagenti `inherit`, qualsiasi bit `= 1`).
6. Come sviluppatore Delphi in Ufficio, voglio un repo locale `delphi` isolato con regole `delphi.md`, hook BOM/`delphi_git`, `update-mcp.bat` e uno script di switch a freddo verificato prima di applicarlo.

## Implementation Decisions

- **Repo `just-develop` (`<REPO_ROOT>`):**
  - Hook e sync (Ticket 01 & 02): `hooks/claude/block-dangerous-git.py`, `hooks/antigravity/{block-dangerous-git.js,block-secrets-read.js}`, `hooks/git/{pre-commit,commit-msg,post-merge,post-checkout,post-rewrite}`, `scripts/{sync-from-claude.py,session_check.py,background_checker.py,check-updates.py}`.
  - Flusso, skill e docs (Ticket 03 & 04): `flow.md`, `shared/global.md`, `personal/global.md`, rimozione `flow-prompts.md`, `skills/{flow-design,implement-ticket,aim-higher,junior-deep-docs,ui-ux-doctrine}/SKILL.md`, `AGENTS.md`, `README.md`, `GUIDE.md`, `GLOSSARY.md`, `DECISIONS.md`, `SETUP.md`, `SETUP-REPO.md`, `docs/*`.
  - Suite test & anti-leak (Ticket 05): `tests/run.py` con verifiche complete su hook, sync, pipe/lock safety, `commit-msg` (`sh.exe`), budget byte e scanner anti-leak su `git ls-files`.
- **Repo `delphi` (`<LOCAL_STACK_REPO>`) + switch (`%USERPROFILE%\.just-develop-local\switch-to-v2.ps1`):**
  - Ticket 01 in `delphi/`: `delphi.md`, `AGENTS.md`, `CLAUDE.md`, `DECISIONS.md`, `README.md`, `hooks/{ensure-delphi-bom.py,block-mcp-delphi-git-push.py,block-delphi-git.js}`, `hooks/git/pre-commit`, `scripts/update-mcp.bat`, `mcp.delphi.json`, `docs/delphi-troubleshooting.md`, `tests/run.py` + `switch-to-v2.ps1`.
- **Divieto di effetti collaterali live:** nessuno script di implementazione o test modifica `~/.claude/`, `~/.gemini/` o `<OLD_LOCAL_CONFIG_REPO>`, né esegue `git commit`, `git merge` o `git push`.

## Testing Decisions

- Tutti i test in `just-develop/tests/run.py` e `delphi/tests/run.py` usano directory temporanee (`tempfile.TemporaryDirectory()`), salvano/ripristinano `GIT_*` dall'ambiente, e vengono eseguiti con `python -X utf8 -I tests/run.py` (exit `0`).
- `switch-to-v2.ps1` viene validato con `[System.Management.Automation.Language.Parser]::ParseFile` (0 errori di parsing) più eventuale dry-run su home temporanea senza toccare `%USERPROFILE%`.

## Out of Scope

- Esecuzione dal vivo di `switch-to-v2.ps1` sulla postazione reale dell'utente, `git commit`, `git merge`, `git push` verso GitHub.
