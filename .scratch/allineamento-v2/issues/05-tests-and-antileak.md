# 05: Suite Test Completa (`tests/run.py`), Anti-Leak, Budget e Pipe/Lock Safety

**Status:** resolved
**Blocked by:** 01, 02, 03, 04 (valida l'intero repo `just-develop`)
**Review:** double
**Esecutore:** @contrarian-git
**Metrica (S/G/C):** 1/0/1 (test di sicurezza critici: devono fallire davvero se i controlli si rompono)

## What to build

Estendere `<REPO_ROOT>\tests\run.py` affinché verifichi in autonomia (in `< 10 s`, senza toccare `~/.claude/`, `~/.gemini/` o l'indice Git reale) tutti i guardrail, gli script di sync/background, i budget di contesto, la coerenza `docs/` e la sicurezza anti-leak pubblico.

## File e simboli toccati

- `tests/run.py`:
  - **Guardrail Claude & AGY (`BASH_DENY`/`ALLOW`, `AGY_CMD_DENY`/`ALLOW`):** aggiungere test su blocco creazione/cambio branch (`git checkout -b x`, `git switch -c x`, `git branch demo`, `git worktree add -b x`), bypass `cmd /c` e `cmd.exe /d /s /c`, here-string PowerShell `@"..."@` / `@'...'@`, e blocco lettura segreti shell dentro `block-dangerous-git.py` (costruendo i nomi estensione con `'.i'+'ni'`, `'.e'+'nv'`).
  - **Guardrail segreti AGY (`SEC_DENY`/`ALLOW`):** aggiungere falsi positivi reali risolti (`Where-Object { $_.Extension -ne ... }`, `Select-String ... *.pas`, commenti `#`, liste con virgole attorno a `.example`); creare un file reale `> 100 KB` in `tempfile.TemporaryDirectory()` per testare `SEC_DENY` su `*.jsonl` senza range e `SEC_ALLOW` su `*.jsonl` con `StartLine`/`EndLine` sia int che stringhe `"1"`..`"50"` (`Path` e `AbsolutePath`), più passaggio libero di `.log`/`.txt`.
  - **Hook Git (`commit-msg` con ricerca `C:\Program Files\Git\bin\sh.exe` se `shutil.which('sh')` è `None`):** testare `Merge branch` con `Conflicts:` scommentati, `Merge pull request` multi-riga, `Merge tag` multi-riga, `Revert "..."` multi-riga, `merge: x\n\ncorpo` (deve fallire!), `Co-Authored-By` (deve fallire!) e formato `tipo(ambito): ...` ≤ 15 parole.
  - **`sync-from-claude.py` su home finta:** testare conservazione file extra in `rules/` (es. `delphi.md`), non creazione di `rules/claude-md.md` se solo `@import`, gestione assenza `settings.json`, pulizia automatica delle sole junction rotte verso `REPO/skills/*` mantenendo l'errore su junction rotte esterne.
  - **Pipe/lock safety e `merge-tree`:** testare `session_check.py` con figlio dormiente simulato (chiusura `EOF` rapida senza bloccare su pipe), testare che il lock kernel di `background_checker.py` impedisca due esecuzioni concorrenti e si liberi all'uscita, testare rilevamento cross-PC su repo temporaneo con file sporco in `status --porcelain` (non deve mai dare falso "nessun conflitto") e `merge-tree` reale su conflitto committato.
  - **Budget, Anti-leak e `docs/`:**
    - `flow.md <= 3.000 B`, ogni file rule `< 24.000 B`.
    - Scanner anti-leak su `git ls-files` di `just-develop`: **zero nomi aziendali/privati letterali dentro `tests/run.py` pubblico!** Usare solo pattern generici pubblici (`C:\Users\`, `<LOCAL_WORK_ROOT>`, `<LOCAL_SDK_DIR>`, email diverse da `@example.`/`@noreply.`/`trimarchig2002@gmail.com` in `DECISIONS` se presenti o solo pattern generici, estensioni segrete fuori dai file consentiti `tests/run.py`, `SETUP.md`, `*.example`/`*.sample`/`*.template`/`*.dist`) + caricamento opzionale di una blocklist privata locale `%USERPROFILE%\.just-develop-local\leak-terms.txt` se presente su disco.
    - Controllo identità locale Git di `just-develop`: se configurata, `git config user.email` != `@work-domain.example`.
    - Copertura completa in `docs/index.mdx`, link validi in `docs/docs.json` e `docs/SUMMARY.md`, tutte le `skills/*` citate in `docs/skills.md`, e controllo assenza termini banditi (`Review: single`, `Review: flash`, `3.8 Flash`, `flow-prompts.md`, `righe 1..N`, `Livello 1..4`, emoji) limitato ai soli file operativi (`flow.md`, `skills/*/SKILL.md`, `GUIDE.md`, `README.md`, `SETUP*.md`, `docs/*`), escludendo `DECISIONS.md`, `.scratch/` e `tests/run.py`.

## Acceptance criteria

- [ ] `python -X utf8 -I tests/run.py` dentro `<REPO_ROOT>` stampa `ok` ed esce `0`.
- [ ] I test `commit-msg` girano davvero anche su Windows PowerShell (non vengono saltati).
- [ ] Mutare temporaneamente un parser/budget/leak fa fallire il test corrispondente (nessun test morto o tautologico).
- [ ] L'indice Git reale di `just-develop` rimane invariato dopo i test.

## Ipotesi

- `git` >= 2.38 e `node` sono disponibili nel `PATH` della workstation.

## Answer

- **File modificati:**
  - `tests/run.py`
- **Verifica eseguita (dopo l'ultima modifica):**
  - Comando: `python -X utf8 -I C:\Works\GIT\Agents\config\just-develop\tests\run.py`
  - Output copiato: `ok`
  - Exit code: `0` (`JD_EXIT:0`)
  - Assenza log residuo `hooks/antigravity/block-dangerous-git.log`: `False`
  - Pre-commit/Commit: non eseguito (commit finale riservato dopo prova manuale/ok utente; `Status` mantenuto `ready-for-agent`).
- **Tentativi:** 2 (implementazione `@contrarian-git` + 1 passata fix Stage 4).
- **Finding review:** 6 (6 fixed, 0 discarded) — rimossi commenti numerati `# 1.`..`# 4.`, `checker.lock` -> `update.lock`, eliminati due timing race (`fake_worker` `4.0s` / `< 2.5s`, `FileLock` sincronizzato con `stdin=PIPE`), aggiunti test shell wrapper + 6 secret bypass + `-uall` + `clear_git_state` + `case_collisions` + `sibling_overlaps` (con/senza `-u`), controllo `eff_email` aziendale indipendente da `user.name`, sanitizzazione riferimenti privati residui in `.scratch/allineamento-v2/`.
