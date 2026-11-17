---
name: flow-design
description: "Design workflow from idea to spec, vertical tickets, premortem, and delivery table. Trigger on new feature or design requests, /wayfinder, /grill-with-docs, /to-spec, /to-tickets, or \"tabella dei ticket\"."
---

# Design Workflow

Open referenced `~/.agents/skills/*/SKILL.md` files directly from the user home directory (`$HOME` or `%USERPROFILE%`). On `"tabella dei ticket"`, jump to Step 4.3.

## 1. Entry Router

Classify a new request from observed facts and confirm the matching route briefly before proceeding:

- External issue or PR report -> read `~/.agents/skills/triage/SKILL.md`
- Regression, broken behavior, or legacy discrepancy -> read `~/.agents/skills/diagnosing-bugs/SKILL.md`
- Needs hands-on UI or state validation -> read `~/.agents/skills/prototype/SKILL.md`
- Large ambiguous multi-session work (`/wayfinder`) -> read `~/.agents/skills/aim-higher/SKILL.md`, then `~/.agents/skills/wayfinder/SKILL.md`
- New feature or design change -> continue to Step 2.

*Done when* the request is routed to the matching skill or enters Step 2.

## 2. Aim Higher, Grilling & Domain Modeling

1. **Aim Higher** (unless the user replies `salta`): read and follow `~/.agents/skills/aim-higher/SKILL.md`.
2. **Grilling & Glossary:** read and follow `~/.agents/skills/grilling/SKILL.md` and `~/.agents/skills/domain-modeling/SKILL.md`. Add a 1-line concrete example to each frontier question and ask: *"Come rendiamo questa modifica verificabile del tutto?"*
3. **Pre-spec Premortem:** on complex or multi-ticket work, launch a fresh-context `inherit` subagent (or `/swarm`) after Grilling to challenge assumptions and surface simpler, higher-leverage designs before writing `spec.md`; resolve valid findings with the user.

*Done when* the user confirms shared understanding, pre-spec premortem findings (when run) are resolved, and the question frontier is empty.

## 3. Spec & Vertical Tickets

Write `spec.md` and ticket files directly from the contracts below.

### Spec (`.scratch/<work>/spec.md`)

1. Propose high, minimal test seams and confirm them with the user. When wide module boundaries change, offer `~/.agents/skills/codebase-design/SKILL.md` with the deletion test.
2. Save `.scratch/<work>/spec.md` with `Status: ready-for-agent` and sections: `## Problem Statement`, `## Solution`, `## User Stories`, `## Implementation Decisions`, `## Testing Decisions`, `## Out of Scope`. Inline prototype snippets when locking a state machine or schema contract.

### Vertical Tickets (`.scratch/<work>/issues/<NN>-<slug>.md`)

1. Slice the spec into small vertical tracer bullets sized for one fresh session (use expand-contract batches only for wide mechanical refactors). Present `Title | Blocked by | What it delivers` and confirm granularity and dependencies with the user.
2. Write one file per ticket (`01`, `02`, ...) in dependency order with these headers:
   - `**Status:** ready-for-agent`
   - `**Blocked by:** <NN, ... | None>`
   - `**Review:** quick | triple (<1-line reason>)`
   - `**Esecutore:** <Model · Level>` (chosen per `Ruoli e Modelli` in `flow.md`)
   - `**HITL:** yes | no`
3. Assign `Review:` with a 1-line reason:
   - **`Review: triple`:** creates or mutates persistent state, memory/pointers, or schemas; touches threads/async, unmanaged resources, security/git hooks, parsers, sync/update scripts, or critical shared APIs; or requires manual UI/audio/video verification.
   - **`Review: quick`:** self-contained mechanical or logic change fully verified by compiler and automated tests, outside every `triple` trigger above.
4. Write the ticket body with:
   - `## What to build`: target behavior, UI reachability path, and whether it is reachable today.
   - `## File e simboli toccati`: verified **file paths and symbol names** (include a short grep-verified snippet only to disambiguate repeated blocks or lock a schema/state contract).
   - `## Acceptance criteria`: executable pass/fail checks (`- [ ] ...`).
   - `## Ipotesi`: explicit unverified assumptions (`Nessuna` when all facts are verified).

*Done when* `spec.md` and every ticket file are saved in `.scratch/<work>/` with verified file/symbol references and headers.

## 4. Ticket Premortem & Delivery Table

Run steps 1-2 when the spec has 2 or more tickets and at least one is `Review: triple`; otherwise go straight to step 3.

1. **Premortem:** launch a fresh-context `inherit` subagent (or `/swarm`) passing `.scratch/<work>/spec.md` and `.scratch/<work>/issues/*.md` with this brief:
   - Assume every ticket was implemented as written and failed. Inspect code, project docs, official docs, and the web; keep `spec.md`, `issues/*.md`, and repo files untouched, writing any verification scripts or notes only in `.scratch/<work>/contrarian/`.
   - Check: (a) behavior contradicted by current code; (b) uncovered edge cases; (c) missing or inverted ticket dependencies; (d) acceptance checks that pass on broken code; (e) unsupported API usage.
   - Return at most 5 correctness/behavior objections in Italian, most severe first, each with a reopenable proof (`file + symbol`, official doc with date read, or script command + output):
     `Obiezione | Prova | Cosa si rompe | Modifica proposta al ticket`
2. **Validate report:** confirm `git status --short`, `spec.md`, and `issues/*.md` stayed clean (with scratch artifacts confined to `.scratch/<work>/contrarian/`), reopen every cited proof, and re-run any verification script. Present confirmed objections to the user (marking unverifiable claims `non verificato` and dropping disproven ones with a 1-line reason) and update only the tickets the user approves.
3. **Delivery Table:** sort rows **riskiest first** (`Review: triple` at the top, respecting dependencies):
   `Ticket | Prompt (Implementa il ticket <N> di <spec>) | Modello · livello | Review | Perché`
   Below the table, draw a vertical `flowchart TD` of ticket dependencies and state in one line the execution order and parallelizable slices.

*Done when* premortem objections (when run) are resolved with the user, the risk-sorted delivery table is shown, and the `flowchart TD` dependency graph is presented.
