# 02: Sync Claude↔AGY, Hook `post-*` e Controllo Background 8h/24h

**Status:** resolved
**Blocked by:** 01 (condivide `scripts/` e `hooks/git/`)
**Review:** double
**Esecutore:** @diff-repos
**Metrica (S/G/C):** 1/0/1 (scrive su config locali generate, spawn detached e lock kernel)

## What to build

Aggiornare `scripts/sync-from-claude.py`, aggiungere gli hook Git di sync (`post-merge`, `post-checkout`, `post-rewrite`) e realizzare il sistema di controllo silenzioso 8h/24h multipiattaforma (`scripts/session_check.py`, `scripts/background_checker.py`, `scripts/check-updates.py`) in `<REPO_ROOT>\`.

## File e simboli toccati

- `scripts/sync-from-claude.py`: `write_atomic` (temp + `os.replace`), skip `rules/claude-md.md` quando `~/.claude/CLAUDE.md` contiene solo `@import`, rispetto dei file extra in `~/.gemini/config/rules/` (non cancellarli e non segnalarli come errore), gestione sicura se `~/.claude/CLAUDE.md` o `settings.json` mancano (primo avvio), pulizia automatica delle sole junction rotte che puntavano dentro `REPO/skills/*` mantenendo l'errore su link rotti verso altri repo, nessuna cancellazione di agenti/knowledge locali, segnalazione `note:` su MCP extra locali, controllo `permissions.deny` per `Bash(agy *)` / `PowerShell(agy *)`, controllo `block-dangerous-git.py` (con controllo segreti e `onFailure: block`), `block-dangerous-git.js`, `block-secrets-read.js`, disattivazione o verifica di `ponytail` spento in entrambi i client senza duplicare `ponytail-review` fuori da plugin.
- `hooks/git/post-merge`, `hooks/git/post-checkout`, `hooks/git/post-rewrite`:
  - `post-merge`: risolve `PY` (`python` prima di `python3`), esegue `"$PY" -X utf8 -I scripts/sync-from-claude.py`, e resetta gli avvisi `behind` di `just-develop` in `~/.just-develop-local/update-state.json` (se esiste).
  - `post-checkout` (`$1 $2 $3`): esce `0` se `$3 != 1`, se `$1 = $2`, se `$2` è tutto zeri (`0000000000000000000000000000000000000000`), o se esistono `$GIT_DIR/rebase-merge`, `$GIT_DIR/rebase-apply` o `$GIT_DIR/BISECT_LOG`; altrimenti esegue `sync-from-claude.py` (senza whitelist fragile di path).
  - `post-rewrite` (`$1`): se `$1 = rebase`, esegue `sync-from-claude.py` e resetta `behind` di `just-develop` in `update-state.json`.
- `scripts/session_check.py`: hook `SessionStart` (`--client claude|antigravity`, zero chiamate di rete, `< 50 ms`), legge `%USERPROFILE%\.just-develop-local\update-state.json` (o `~/.just-develop-local/`), stampa `{}` se nessuna novità non letta; altrimenti emette notifica (`injectSteps` `user_markdown` / breve `systemMessage` per AGY; su Claude emette `additionalContext` sulle novità Git di `just-develop` solo quando `cwd` è dentro `just-develop`, e segnala aggiornamenti skill/plugin globali solo se presenti). Se `now - last_git >= 8h` o `now - last_assets >= 24h`, avvia `scripts/background_checker.py` in modo detached (`CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP` su Windows, `start_new_session=True` su POSIX, `stdin/stdout/stderr=DEVNULL`, `close_fds=True`).
- `scripts/background_checker.py` e `scripts/check-updates.py`:
  - Lock esclusivo kernel su `~/.just-develop-local/update.lock` (`msvcrt.locking` su Windows / `fcntl.flock` su POSIX, zero `os.kill`).
  - Controllo 8h Git (`just-develop`): `git fetch --prune origin` (`GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`, timeout `10 s`), stato `HEAD...origin/main` e `main...origin/main`, controllo collisioni case-insensitive `refs/remotes/origin/*`, e rilevatore branch fratelli `origin/home/*` / `origin/office/*` non uniti a `origin/main` (verifica prima `git status --porcelain -- ':(exclude).scratch'` intersecato coi file remoti per evitare falsi allarmi su spec aperte e la cecità di `merge-tree` sui file sporchi locali, poi `git merge-tree --write-tree --name-only HEAD B` parsando correttamente riga 0 tree OID e file in conflitto fino alla riga vuota, con fallback < 2.38), più `sync-from-claude.py --check`.
  - Controllo 24h Skill/Plugin/MCP: **`git ls-remote <sourceUrl> HEAD`** sui soli `sourceUrl` delle skill effettivamente presenti in `~/.agents/skills/` (filtrate da `~/.agents/.skill-lock.json`, senza tentare match con `skillFolderHash`), confrontando con l'ultimo `HEAD` salvato in `update-state.json` e segnalando i nomi dei repo cambiati (rimandando a `npx skills check` su richiesta dell'utente; zero REST API GitHub!), più `git fetch` + check `version`/`HEAD` sui plugin abilitati (e su eventuali asset locali opzionali in `update-config.json` fuori repo, zero hardcode Delphi).
  - Traduce commit `tipo(ambito): descrizione` in changelog italiano semplice (`Nuove funzioni`, `Correzioni e sicurezza`, `Miglioramenti / Documentazione`).
  - `check-updates.py` esegue lo stesso controllo in modalità sincrona interattiva su richiesta dell'utente.

## Acceptance criteria

- [ ] `sync-from-claude.py` non fallisce né cancella file extra in `rules/`, non crea `rules/claude-md.md` vuoto, pulisce junction rotte solo dentro `REPO/skills/*`, usa `write_atomic` via `os.replace`.
- [ ] `session_check.py` non tocca la rete e su spawn di un worker simulato che dorme `3 s` chiude `EOF` in `< 1,5 s` sotto `node` / `sh.exe`.
- [ ] `background_checker.py` usa lock kernel (`msvcrt.locking`/`fcntl.flock`), segnala esplicitamente modifiche locali non committate invece di fidarsi di `merge-tree`, parsa correttamente gli errori reali di `merge-tree` e usa `git ls-remote` senza chiamate `api.github.com`.
- [ ] Nessun file aziendale/Delphi hardcoded e nessuna modifica dal vivo a `~/.claude/` o `~/.gemini/`.

## Ipotesi

- `git` >= 2.38 è installato per `git merge-tree --write-tree`; in caso contrario è previsto il fallback su intersezione file.

## Answer

- **File creati/modificati:**
  - `scripts/sync-from-claude.py`
  - `scripts/session_check.py`
  - `scripts/background_checker.py`
  - `scripts/check-updates.py`
  - `hooks/git/post-merge`
  - `hooks/git/post-checkout`
  - `hooks/git/post-rewrite`
- **Verifica eseguita (dopo l'ultima modifica):**
  - Comando: `python -X utf8 -I C:\Works\GIT\Agents\config\just-develop\tests\run.py`
  - Output copiato: `ok`
  - Exit code: `0` (`JD_EXIT:0`)
  - Pre-commit/Commit: non eseguito (commit finale riservato dopo prova manuale/ok utente; `Status` mantenuto `ready-for-agent`).
- **Tentativi:** 3 (implementazione `@diff-repos` + aggiunta detector `case_collisions`/`sibling_overlaps` + 1 passata fix Stage 4).
- **Finding review:** 6 (5 fixed, 1 discarded) — fixed: `update.lock`, `clear_git_state` senza creazione file assente + `clear-git.flag` + retry lock, `git fetch --prune origin` timeout `10`, `origin/<branch>` senza `-u`, `-uall` in `parse_porcelain_dirty_paths`, helper `norm_path_ci`, `read_json_doc` con `with`/`try` in `sync-from-claude.py`; discarded: estrarre 2 righe `SCRIPTS` da `post-merge`/`post-checkout`/`post-rewrite` in un file shell aggiuntivo (basso valore rispetto al nuovo file).
