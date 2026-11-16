# 03: Nucleo `flow.md`, Regole Globali e Skill Universali (`/writing-for-agents`)

**Status:** resolved
**Blocked by:** None (can start immediately)
**Review:** double
**Esecutore:** @token-pro-2
**Metrica (S/G/C):** 1/1/0 (regole/skill critiche cross-client soggette ad audit `/writing-for-agents` e override review)

## What to build

Riscrivere il nucleo `flow.md`, le regole globali (`shared/global.md`, `personal/global.md`), rimuovere l'orfano `flow-prompts.md` e completare/allineare le 5 skill in `<REPO_ROOT>\skills\` secondo `/writing-for-agents`, `SKILL-MECHANICS.md` e l'override Review binaria (`quick` | `double` con 3 subagenti `inherit`, zero `single`, zero `3.8 Flash`).

## File e simboli toccati

- `flow.md` (`<= 3.000 B`):
  - Ruoli e Modelli reali (**Ufficio:** AGY Ultra `Hydrogen Low|Medium` / `Carbon Medium` + Claude Team `Sonnet 5.5 medium` / `Opus`; **Casa:** AGY Pro `Hydrogen Low|Medium` / `Argon Medium` + Claude Pro `Sonnet 5.5 medium` / `Opus`); zero `3.8 Flash` e zero `Review: single`.
  - Lingua, spiegazione API/parametri/flag/unità/thread, opzioni pro/contro `(Consigliata)`, citazioni per **file e simbolo**.
  - Branching `<pc>/<tipo>/<slug>`, sessione pulita tra ticket/fasi con stato in `.scratch/` al posto di `/compact`.
  - Puntatori affilati con leading word a `flow-design` (nuova feature, spec, ticket, wayfinder, `/grill-with-docs`, `/to-spec`, `/to-tickets`, `tabella dei ticket`) e `implement-ticket` (`Implementa il ticket <N>`, `Rivedi il ticket <N>`).
  - Checklist invariante di chiusura ticket inline (4 passi): spiega chiaramente `Review: quick` (0 subagenti) vs `Review: double` (3 subagenti paralleli su `inherit`: `Standards` + `Spec` + `ponytail-review`), build/test verdi prima e dopo, `## Answer`, Walkthrough e conferma utente per `Status: resolved` + commit.
  - Zero negazioni evitabili (`never`, `/implement`, `/implement-spec`), zero no-op (`1-2 lookup`), zero duplicazioni.
- `shared/global.md`: regole condivise snelle, inclusa 1 riga positiva sui file di segreti/credenziali (sostituendo `no-ini-files.md` senza scrivere estensioni vietate in comandi).
- `personal/global.md`: preferenze personali pulite e generiche (zero leak aziendali, compatibile con `sync-from-claude.py`).
- `flow-prompts.md`: **rimosso** (assorbito in `flow-design` e `implement-ticket`).
- `skills/flow-design/SKILL.md` (`dmi: false`, tool-agnostic):
  - Nota unica per risolvere `~` alla home reale aprendo file sotto `~/.agents/skills/`.
  - Entry Router (`triage`, `diagnosing-bugs`, `prototype` vs Step 2).
  - Aim Higher (`~/.agents/skills/aim-higher/SKILL.md`) + Grilling (`grilling`, `domain-modeling`) + domanda verificabilità.
  - Contratto nativo **Spec** (`.scratch/<work>/spec.md`, offerta `/codebase-design`) e **Ticket** (`.scratch/<work>/issues/<NN>-<slug>.md` con `Blocked by`, `Status: ready-for-agent`, UI reachability, `## Ipotesi`, verifica eseguibile, **file e simbolo**, metrica `S/G/C` con mapping netto `0/0/0 -> Review: quick` e qualsiasi bit `= 1 -> Review: double` — mai `single`, zero `3.8 Flash` — `Esecutore:`, `HITL:`): **non** legge `to-spec` o `to-tickets` per evitare conflitti di template e `/setup-matt-pocock-skills`.
  - Premortem `contrarian` in Claude Code + Tabella di consegna rischi prima + `flowchart TD`.
- `skills/implement-ticket/SKILL.md` (`dmi: false`, tool-agnostic):
  - Pre-flight (ticket, `AGENTS.md`, `git log -n 5 --oneline`, test verdi mantenuti intatti), modifiche mirate per file+simbolo, aggiornamento `docs/` (`junior-deep-docs`, senza `1..N`), verifica UI (`ui-ux-doctrine`), gate deterministico.
  - Review binaria: `git add -N -- . ':(exclude).scratch'` e passaggio di `git diff -- . ':(exclude).scratch'` e ticket path in sola lettura (zero `> .scratch/_review.diff`, zero `3.8 Flash`, zero file extra `agents/review-*.md`); `Review: quick` (auto-verifica) vs `Review: double` (sempre **3 subagenti paralleli su `inherit`** con le checklist inline compatte di **`Standards`** + smell baseline + lettura obbligatoria di `AGENTS.md` del repo e di eventuali stack doc da esso puntate, **`Spec`**, e **`ponytail-review`** 6 assi, senza fargli aprire i 64 KB di `humanizer`/`mintlify`), terminando il turno fino al completamento dei 3 subagenti, fix in 1 passata e ri-verifica deterministica.
  - `## Answer` (`Tentativi`, `Finding review`), Walkthrough 5-sezioni (incl. HITL granulare 1 azione fisica/riga con nomi naturali visibili), chiusura `Status: resolved` pre-commit (versionato) o post-commit + `Commit: <hash>` (ibrido).
- `skills/aim-higher/SKILL.md`, `skills/junior-deep-docs/SKILL.md`, `skills/ui-ux-doctrine/SKILL.md`: verifica/rifinitura `/writing-for-agents` (zero `1..N`, solo **file e simbolo**, zero riferimenti Delphi/work-domain, `ui-ux-doctrine` generica).

## Acceptance criteria

- [ ] `flow.md` pesa `<= 3.000 B`, contiene zero riferimenti a `Review: single`, `3.8 Flash`, `/implement`, `/implement-spec`, `righe 1..N` o path/simboli Delphi/work-domain.
- [ ] `flow-design/SKILL.md` e `implement-ticket/SKILL.md` hanno `dmi: false`, implementano la review binaria (`quick` = 0 subagenti; `double` = 3 subagenti `inherit` `Standards`+`Spec`+`ponytail-review` inline) e funzionano senza il tool `Skill`.
- [ ] `flow-prompts.md` è rimosso dal repo.
- [ ] Tutti i file superano l'audit `/writing-for-agents` (zero negazioni evitabili, zero no-op, `*Done when*` verificabili).

## Ipotesi

- Le skill esterne (`grilling`, `domain-modeling`, `triage`, `diagnosing-bugs`, `prototype`) restano installate in `~/.agents/skills/`.

## Answer

- **File creati/modificati/rimossi:**
  - `flow.md` (`2273` byte `<= 3000`)
  - `shared/global.md`
  - `personal/global.md`
  - `flow-prompts.md` (rimosso)
  - `skills/flow-design/SKILL.md`
  - `skills/implement-ticket/SKILL.md`
  - `skills/aim-higher/SKILL.md`
  - `skills/junior-deep-docs/SKILL.md`
  - `skills/ui-ux-doctrine/SKILL.md`
- **Verifica eseguita (dopo l'ultima modifica):**
  - Comando: `python -X utf8 -I C:\Works\GIT\Agents\config\just-develop\tests\run.py`
  - Output copiato: `ok`
  - Exit code: `0` (`JD_EXIT:0`)
  - Dimensione verificata `flow.md`: `2273` B
  - Pre-commit/Commit: non eseguito (commit finale riservato dopo prova manuale/ok utente; `Status` mantenuto `ready-for-agent`).
- **Tentativi:** 2 (implementazione `@token-pro-2` + 1 passata fix Stage 4).
- **Finding review:** 4 (4 fixed, 0 discarded) — deduplicazione `flow.md` (`## Metodo e Scelte`), rimozione negazione `omitting Co-Authored-By` in `personal/global.md`, riscrittura positiva + `*Done when*` in `skills/*/SKILL.md`, sanitizzazione riferimenti privati residui in `.scratch/allineamento-v2/`.
