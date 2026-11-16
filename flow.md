# Flusso di lavoro

## Ruoli e Modelli
- **Progettista** (Claude Team/Pro: `Sonnet 5.5 medium`, `Opus` su bug difficili o scelte architetturali; su AGY Ultra anche `Carbon Medium`): esplora, fa grilling, scrive spec, ticket e diagnosi.
- **Esecutore** (Ufficio AGY Ultra: `Hydrogen Low|Medium`, o `Carbon Medium` per errori invisibili ai test; Casa AGY Pro: `Hydrogen Low|Medium`, o `Argon Medium`): implementa un ticket per finestra, aggiorna `docs/`, verifica e lancia la review.
- **Revisore**: 3 subagenti paralleli su `inherit` (`Standards`, `Spec`, `ponytail-review`) su codice e `docs/`; `contrarian` in Claude Code sui ticket.

## Metodo e Scelte
- Per ogni API o metodo chiave spiega parametri, flag, tipo di ritorno, unità di misura e vincoli di thread.
- Sulle vere scelte proponi 2-3 strade con **A favore** e **Contrario**, mettendo **`(Consigliata)`** per prima.

## Branch, Sessioni e Puntatori
- Branch `<pc>/<tipo>/<slug>` in minuscolo: l'utente crea, cambia, unisce su `main` e pubblica il branch; l'agente lavora sul branch corrente.
- Salva lo stato su `.scratch/` e apri una sessione pulita a ogni ticket o fase (preferendola a `/compact`); risolvi `~` nella home reale.
- **Design** (nuova feature, spec, ticket, wayfinder, `/grill-with-docs`, `/to-spec`, `/to-tickets`, `tabella dei ticket`): apri e segui `~/.agents/skills/flow-design/SKILL.md`.
- **Implement** (`Implementa il ticket <N>`, `Rivedi il ticket <N>`): apri e segui `~/.agents/skills/implement-ticket/SKILL.md`.

## Chiusura ticket (invariante)
Ogni ticket termina in quest'ordine:
1. Leggi il ticket, `AGENTS.md` e `git log -n 5`; esegui build e test esistenti prima di modificare codice e mantienili intatti.
2. Applica modifiche chirurgiche per file e simbolo e aggiorna `docs/` (`junior-deep-docs`).
3. Rilancia build e test verdi, poi esegui la review del ticket: **`Review: quick`** (0 subagenti: auto-verifica e check deterministici) oppure **`Review: double`** (3 subagenti paralleli su `inherit`: `Standards` + `Spec` + `ponytail-review`); correggi in una passata e ri-verifica build/test.
4. Scrivi `## Answer` nel ticket (lasciando aperto `Status`), mostra il Walkthrough (`flowchart TD`, tabella API, passi HITL), e attendi conferma utente per `Status: resolved` e commit.
