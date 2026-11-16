# 01: Hook Git, Guardrail Claude/AGY, `cmd /c`, Blocco Branch e Fix Segreti

**Status:** resolved
**Blocked by:** None (can start immediately)
**Review:** double
**Esecutore:** @diff-repos
**Metrica (S/G/C):** 1/0/1 (tocca hook di sicurezza, parser shell e `commit-msg`)

## What to build

Aggiornare tutti i guardrail Git e segreti in `<REPO_ROOT>\hooks\` per:
1. Bloccare creazione/cambio branch agli agenti e chiudere il bypass `cmd` / `cmd.exe` in entrambi i client;
2. Portare la parità di blocco segreti su shell dentro Claude Code (`block-dangerous-git.py`);
3. Eliminare i falsi positivi PowerShell/commenti/virgole in `block-secrets-read.js` e bloccare letture `*.jsonl > 100 KB` senza range corto;
4. Correggere `hooks/git/commit-msg` (merge PR/tag/conflitti/revert multi-riga) e aggiornare `hooks/git/pre-commit` (`python` prima di `python3`, `-X utf8 -I`, warning formato branch non bloccante su detached `HEAD`).

## File e simboli toccati

- `hooks/claude/block-dangerous-git.py`: `SHELLS`, `is_dangerous_git`, `is_dangerous_part`, `main` (aggiungere blocco creazione/cambio branch `switch -c|-C|<branch>`, `checkout -b|-B|--orphan|<branch>`, `branch <nome>`, `worktree add -b|-B`; aggiungere `cmd` / `cmd.exe` (`/c`, `/k`) in `SHELLS`; aggiungere controllo lettura segreti su `command` usando concatenazione `'.i'+'ni'` / `'.e'+'nv'`; supportare here-string PowerShell `@"..."@` / `@'...'@` in `sanitize_for_split`).
- `hooks/antigravity/block-dangerous-git.js`: `SHELLS`, `dangerousGitRule`, `matchDangerousCommand`, main block (aggiungere blocco creazione/cambio branch agli agenti; aggiungere `cmd` / `cmd.exe` in `SHELLS`; estendere `HEREDOC` alle here-string PowerShell `@"..."@`/`@'...'@`; scrivere in `block-dangerous-git.log` **solo su `deny`** e senza testo comando dentro `try/catch`).
- `hooks/antigravity/block-secrets-read.js`: `isSafeInspectCommand`, `scanString`, `findBlockedToken`, main block (preservare `echo (cat ...)` e `git log -p` bloccati; permettere filtri negativi PS `-ne`, `-notin`, `-notlike`, `-notmatch`, `-Exclude`, commenti `#`, `Select-String`/`rg` su sorgenti non segreti, normalizzazione virgole attorno a `SAFE_ENV_SUFFIXES`; in `read_file`/`view_file` leggere `Path` o `AbsolutePath`, bloccare file `*.jsonl` > `100 KB` se mancano `StartLine`/`EndLine` validi o se `(Number(EndLine) - Number(StartLine) + 1) > 100`, accettando sia numeri sia stringhe numeriche es. `"1"`; lasciare liberi `.log`/`.txt`; mai estensioni segrete letterali nei comandi).
- `hooks/git/commit-msg`: valutare la whitelist di merge/revert automatici (`Merge branch `, `Merge branches `, `Merge pull request `, `Merge remote-tracking branch `, `Merge tag `, `Revert "`) **dopo** `grep -qi 'co-authored-by'` ma **prima** di `[ "$message" = "$subject" ]`, lasciando `"merge: "?*` sotto al controllo 1-riga (max 15 parole, formato `tipo(ambito): descrizione`).
- `hooks/git/pre-commit`: `PY=$(command -v python || command -v python3)`, `"$PY" -X utf8 -I tests/run.py`, più controllo non bloccante in detached `HEAD` (`b=$(git symbolic-ref --quiet --short HEAD) || exit 0`) che avvisa se il branch corrente (diverso da `main`) non rispetta `^(office|home)/(feat|fix|refactor|docs|test|chore)/[a-z0-9][a-z0-9-]*$`.

## Acceptance criteria

- [ ] `block-dangerous-git.py` e `block-dangerous-git.js` bloccano `git checkout -b x`, `git switch -c x`, `git switch main`, `git branch demo`, `git worktree add -b x`, `cmd /c "git stash drop"`, `cmd.exe /d /s /c "git push"`, consentendo ancora `git status`, `git add -N`, `git diff`, here-string PS `@"..."@` innocue.
- [ ] `block-dangerous-git.py` blocca la lettura shell di file segreti (`.e`+`nv`, `.i`+`ni` costruiti via concatenazione) rispettando esclusioni sicure (`--exclude`, `:!*`, `.example`).
- [ ] `block-secrets-read.js` lascia passare `Get-ChildItem | Where-Object { $_.Extension -ne ... }`, `Select-String ... *.pas`, commenti `#`, virgole attorno a `.example`, blocca `echo (cat ...)`, `git log -p` su segreti, e blocca `read_file` su `*.jsonl > 100 KB` senza range `<= 100` righe (lasciando passare `.log`/`.txt`).
- [ ] `commit-msg` (eseguito con `sh.exe`) accetta `Merge branch ...` con `Conflicts:` scommentati, `Merge pull request #N` multi-riga, `Merge tag` multi-riga e `Revert "..."` multi-riga, mentre rifiuta `merge: x\n\ncorpo` e qualsiasi `Co-Authored-By`.
- [ ] Zero simboli o path aziendali/Delphi dentro questi file.

## Ipotesi

- Su Windows `git` è disponibile in `PATH` e `C:\Program Files\Git\bin\sh.exe` è presente per eseguire gli hook shell.

## Answer

- **File creati/modificati:**
  - `.gitattributes` (eol `lf` su `hooks/git/*` e `*.sh`)
  - `hooks/claude/block-dangerous-git.py`
  - `hooks/antigravity/block-dangerous-git.js`
  - `hooks/antigravity/block-secrets-read.js`
  - `hooks/git/commit-msg`
  - `hooks/git/pre-commit`
- **Verifica eseguita (dopo l'ultima modifica):**
  - Comando: `python -X utf8 -I C:\Works\GIT\Agents\config\just-develop\tests\run.py`
  - Output copiato: `ok`
  - Exit code: `0` (`JD_EXIT:0`)
  - Assenza log residuo `hooks/antigravity/block-dangerous-git.log`: `False`
  - Pre-commit/Commit: non eseguito (commit finale riservato dopo prova manuale/ok utente; `Status` mantenuto `ready-for-agent`).
- **Tentativi:** 2 (implementazione `@diff-repos` + 1 passata fix Stage 4).
- **Finding review:** 5 (5 fixed, 0 discarded) — 3 shell bypass `cmd`/`powershell`, 6 secret inspection bypass, `.gitattributes` `eol=lf`, parametro morto `cwd`, rimozione `block-dangerous-git.log` untracked.
