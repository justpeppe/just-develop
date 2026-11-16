---
name: flow-design
description: Design phase workflow across Claude and Antigravity: entry routing, aim-higher research, grilling, spec, vertical tickets with S/G/C binary review grading, contrarian premortem, and delivery table. Trigger on new feature requests, /grill-with-docs, /to-spec, /to-tickets, /wayfinder, or "tabella dei ticket".
---

# Design Workflow

Resolve `~` to the OS home directory (`$HOME` on macOS/Linux, `%USERPROFILE%` on Windows) before opening any skill path below. Read each referenced `SKILL.md` directly with `Read` or `read_file` so the workflow runs identically in Claude and Antigravity.

## 1. Entry Router

Classify a new request from observed facts and ask confirmation in one line:
`Via: /<skill>, perché <segnale>. Correggimi se sbaglio.`

- External issue or PR report -> read `~/.agents/skills/triage/SKILL.md`
- Regression, broken behaviour, or legacy discrepancy -> read `~/.agents/skills/diagnosing-bugs/SKILL.md`
- Needs hands-on UI or state validation -> read `~/.agents/skills/prototype/SKILL.md`
- Large fog-wrapped multi-session work (`/wayfinder`) -> read `~/.agents/skills/aim-higher/SKILL.md` first (unless user replies `salta`), then `~/.agents/skills/wayfinder/SKILL.md`
- New feature or design change -> continue to Step 2.

*Done when* the request is routed to the matching skill or confirmed to enter Step 2.

## 2. Aim Higher, Grilling & Domain Modeling

Skip Step 2.1 if the user replies `salta`.

1. **Aim Higher:** read `~/.agents/skills/aim-higher/SKILL.md`. Research the codebase, official documentation, and web; explain Principle, Cause, and External Judge; present 2-3 concrete options (`(Consigliata)` first) with pros and cons.
2. **Grilling & Glossary:** read `~/.agents/skills/grilling/SKILL.md` and `~/.agents/skills/domain-modeling/SKILL.md`.
   - Work one frontier round at a time, giving a 1-line concrete example and recommended answer per question.
   - Always ask: *"Come rendiamo questa modifica verificabile del tutto?"*
   - Update `GLOSSARY.md` and `docs/adr/` lazily as domain terms or hard-to-reverse decisions crystallize.

*Done when* the user confirms shared understanding and the question frontier is empty.

## 3. Native Spec & Tracer-Bullet Tickets

Use the native Spec and Ticket contracts below directly (they replace `to-spec` and `to-tickets` so every artifact keeps this workflow's header fields, UI reachability, and symbol-level precision self-contained).

### Spec (`.scratch/<work>/spec.md`)

1. Propose high, minimal test seams and confirm them with the user. If large module seams changed, offer `/codebase-design` with the deletion test.
2. Write `.scratch/<work>/spec.md` with `Status: ready-for-agent` and sections: `## Problem Statement`, `## Solution`, `## User Stories`, `## Implementation Decisions`, `## Testing Decisions`, `## Out of Scope`. Inline prototype snippets when locking a state machine or schema contract.

### Vertical Tickets (`.scratch/<work>/issues/<NN>-<slug>.md`)

1. Slice the spec into small vertical tracer bullets sized for one fresh session (use expand-contract batches only for wide mechanical refactors). Present `Title | Blocked by | What it delivers` and confirm granularity and dependencies with the user.
2. Write one file per ticket numbered `01`, `02`, ... in dependency order with these headers:
   - `**Status:** ready-for-agent`
   - `**Blocked by:** <NN, ... | None (can start immediately)>`
   - `**Review:** quick | double`
   - `**Esecutore:** <Model · Level>` (`Hydrogen Low` for mechanical edits <= 30 lines with zero new state; `Hydrogen Medium` default when build/tests catch mistakes; `Carbon Medium` on Office/Ultra or `Argon Medium` on Home/Pro when errors pass build/tests or `C = 1`)
   - `**Metrica (S/G/C):** <0|1>/<0|1>/<0|1> (<reason>)`
   - `**HITL:** yes | no` (plus optional `Angolo formativo` 5-15 line API card when instructive)
   - `**Verificato:** <YYYY-MM-DD> @ <short-commit>` (refreshed after verifying every cited file and symbol still exists)
3. Score `S/G/C` (`0|1` each) and apply the binary review mapping:
   - **`S` (Stato):** `1` if creating or mutating persistent state, memory/pointers, or data schemas.
   - **`G` (Forza Giudice):** `0` if compiler and automated tests catch logic bugs; `1` if verification needs manual UI, audio/video, or unchecked runtime behavior.
   - **`C` (Concorrenza/Sicurezza):** `1` if touching threads/async, unmanaged resources, security/git hooks, parsers, sync/update scripts, or critical shared APIs.
   - **Mapping:** `0/0/0` -> **`Review: quick`** (0 subagents); any bit `= 1` (`S`, `G`, or `C`) -> **`Review: double`** (3 parallel subagents on `inherit`).
4. Write the ticket body with:
   - `## What to build`: expected behavior, exact UI reachability path, and whether it is reachable today.
   - `## File e simboli toccati`: exact **file paths and symbol names** (cite file and symbol only; add a unique grep-verified snippet only to disambiguate repeated blocks or lock a prototype contract).
   - `## Acceptance criteria`: executable pass/fail checks (`- [ ] ...`).
   - `## Ipotesi`: explicit unverified assumptions.

*Done when* `spec.md` and every ticket file are saved in `.scratch/<work>/` with verified symbols and `S/G/C` headers.

## 4. Contrarian Premortem & Delivery Table

Skip the `contrarian` run only when the spec has one ticket OR every ticket is `Review: quick`.

1. **Premortem (Claude Code):** `agents/contrarian.md` sets `antigravity: false`, so run it in Claude Code. Before launching, record `git status --short` and file hashes (`Get-FileHash` on Windows, `shasum` on macOS/Linux) for `spec.md` and `issues/*.md`. Pass only the paths to `.scratch/<work>/spec.md` and `issues/*.md`.
2. **Validate report:** check that spec, tickets, and code stayed unchanged and outputs live only in `.scratch/<work>/contrarian/`. Reopen every cited proof and re-run verification scripts. Keep valid objections, discard disproven ones with reason, mark unchecked ones `non verificato`, and update only the tickets the user chooses.
3. **Delivery Table (end of ticket design and on `"tabella dei ticket"`):** sort rows **riskiest first** (`Review: double` and `C=1` at the top, respecting dependencies):
   `Ticket | Prompt (Implementa il ticket <N>) | Modello · livello | Review | Perché`
   Below the table, draw a vertical `flowchart TD` of ticket dependencies and state in one line the execution order and parallelizable slices.

*Done when* contrarian findings are resolved with the user, the delivery table (riskiest first) is shown, and the `flowchart TD` dependency graph is presented.
