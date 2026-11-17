# Flusso di lavoro

## Ruoli e Modelli
- **Progettista** (`Sonnet 5.5 medium`, `Opus` su bug difficili o scelte architetturali; `Carbon Medium` su AGY): esplora, fa grilling, scrive spec, ticket e diagnosi.
- **Esecutore** (`Hydrogen Low` per edit meccanici `<= 30` righe senza nuovo stato; `Hydrogen Medium` default quando build e test catturano gli errori; `Carbon Medium` o `Argon Medium` quando gli errori sfuggono ai test o `Review: triple`): implementa un ticket per sessione.
- **Revisore**: `Review: quick` (auto-verifica, `0` subagenti) o `Review: triple` (`3` subagenti paralleli su `inherit`: `Standards`, `Spec`, `diff-review`); premortem a contesto pulito su spec e ticket.

## Metodo e Scelte
- Per ogni API o metodo chiave spiega parametri, flag, tipo di ritorno, unità di misura e vincoli di thread.
- Sulle vere scelte proponi 2-3 opzioni con **A favore** e **Contrario**, mettendo **`(Consigliata)`** per prima.

## Branch, Sessioni e Puntatori
- Lavora sul branch corrente (`<tipo>/<slug>` minuscolo); creazione, cambio branch, merge su `main` e push spettano all'utente.
- Tieni lo stato in `.scratch/` e apri una sessione pulita a ogni fase o ticket. Risolvi `~` nella home del sistema (`$HOME` o `%USERPROFILE%`) e apri i `SKILL.md` direttamente come file:
  - **Design** (nuova funzione o diagnosi, `/wayfinder`, `/grill-with-docs`, `/to-spec`, `/to-tickets`, `tabella dei ticket`): `~/.agents/skills/flow-design/SKILL.md`.
  - **Implement** (`Implementa il ticket <N> di <spec>`, o `Rivedi il ticket <N> di <spec>` per sola ri-verifica): `~/.agents/skills/implement-ticket/SKILL.md`.

## Chiusura ticket (invariante)
Ogni ticket termina in quest'ordine:
1. Leggi ticket e `AGENTS.md`; verifica che build e test esistenti partano verdi e restino intatti.
2. Applica modifiche chirurgiche per file e simbolo e aggiorna `docs/` (`~/.agents/skills/junior-deep-docs/SKILL.md`).
3. Porta a exit `0` build e controlli di `AGENTS.md`, esegui la review del ticket (`quick` o `triple`), correggi i difetti reali in una passata e ri-verifica.
4. Scrivi `## Answer` nel ticket con `Status` aperto, presenta il Walkthrough e attendi conferma dell'utente per `Status: resolved` e commit.
