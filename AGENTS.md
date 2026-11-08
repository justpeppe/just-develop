## Repo pubblico

`just-develop` è un setup agentico generico, come le skill di Matt Pocock: chiunque lo installa sulla propria macchina. Claude Code decide e scrive i ticket, Gemini in Antigravity li implementa e li rivede.

Nel repo entra ciò che serve a tutti. Ciò che esiste su una sola macchina (server MCP, percorsi, nomi, account) resta nella configurazione del client di quella macchina.

## Agent skills

### Issue tracker

Le issue vivono come file markdown in `.scratch/`. Leggi `docs/agents/issue-tracker.md` prima di creare o chiudere un ticket.

### Triage labels

Etichette: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. Dettagli in `docs/agents/triage-labels.md`.

### Domain docs

Single-context. Dettagli in `docs/agents/domain.md` e `GLOSSARY.md`.

## Aree a rischio

Gli hook in `hooks/` e `scripts/sync-from-claude.py`: un errore qui spegne i guardrail in silenzio su ogni repo.

## Commit

Formato `tipo(ambito): descrizione`, una sola riga, al massimo 15 parole, senza `Co-Authored-By`. `hooks/git/commit-msg` controlla tutto questo, non l'elenco degli ambiti, e accetta anche `merge: ...` e i messaggi automatici di merge e revert. Ambiti: `flow`, `hooks`, `scripts`, `skills`, `mcp`, `docs`, `tests`.

## Decisioni

Ogni cosa portata o scartata va in `DECISIONS.md`, con motivo, fonte e data.

## Verifiche

Esegui entrambe dopo ogni modifica a hook, regole o script; devono uscire 0. Usa `python`, o `python3` se `python` non esiste.

- Hook e script: `python -I tests/run.py` (lo lancia anche `hooks/git/pre-commit`).
- Allineamento Claude Code e Antigravity: `python -I scripts/sync-from-claude.py --check`, solo su una macchina già configurata con `SETUP.md`.
