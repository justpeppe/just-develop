## Repo pubblico

`just-develop` è un setup agentico generico per Claude Code e Antigravity. Nel repo entra solo ciò che serve a tutti; percorsi locali, server MCP di una singola macchina, credenziali e stack specifici restano fuori dal repository nella configurazione del client o in un repo locale separato.

## Agent skills

### Issue tracker

Le issue e le spec vivono come file markdown in `.scratch/`. Leggi `docs/agents/issue-tracker.md` prima di creare o chiudere un ticket.

### Triage labels

Etichette: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. Dettagli in `docs/agents/triage-labels.md`.

### Domain docs

Single-context. Dettagli in `docs/agents/domain.md` e `GLOSSARY.md`.

## Aree a rischio

Gli hook in `hooks/` (guardrail Claude/AGY e hook Git `pre-commit`, `commit-msg`, `post-merge`, `post-checkout`, `post-rewrite`) e gli script in `scripts/` (`sync-from-claude.py`, `session_check.py`, `background_checker.py`, `check-updates.py`, `extract-repo-retro.py`): un errore qui spegne i guardrail, rompe il sync di Antigravity, fa filtrare credenziali nei digest o blocca le pipe di `SessionStart`.

## Branch e Commit

- **Branching:** usa 3 livelli minuscoli `office|home/<tipo>/<slug>` con `<tipo>` tra `feat`, `fix`, `refactor`, `docs`, `test`, `chore`. I branch vengono creati, cambiati e integrati su `main` (merge non-squash) dall'utente; gli agenti lavorano sul branch corrente.
- **Messaggi di commit:** formato `tipo(ambito): descrizione`, una sola riga, al massimo 15 parole dopo i due punti, senza `Co-Authored-By`. `hooks/git/commit-msg` controlla il formato accettando anche `merge: ...` (1 riga) e i messaggi automatici Git/GitHub (`Merge branch/branches/pull request/remote-tracking branch/tag`, `Revert "`). Ambiti: `flow`, `hooks`, `scripts`, `skills`, `mcp`, `docs`, `tests`.

## Decisioni

Ogni scelta architetturale portata o scartata va in `DECISIONS.md`, con pro, contro, fonte e data (`Superata da: N (gg/mm/aaaa)` sulle voci sostituite).

## Verifiche

Esegui dopo ogni modifica a hook, script, regole, skill o documentazione; devono uscire `0`. Usa `python`, o `python3` se `python` non è presente:

- Suite completa (hook, sync, pipe/lock safety, budget token, anti-leak, `docs/`): `python -X utf8 -I tests/run.py` (eseguito anche da `hooks/git/pre-commit`).
- Allineamento Claude Code e Antigravity: `python -X utf8 -I scripts/sync-from-claude.py --check` (su macchina configurata con `SETUP.md`).
- Controllo manuale novità Git cross-PC e aggiornamenti 24h: `python -X utf8 -I scripts/check-updates.py`.
