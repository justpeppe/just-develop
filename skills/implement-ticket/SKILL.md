---
name: implement-ticket
description: Execute a ticket end-to-end across Claude and Antigravity: pre-flight checks, surgical edits, docs update, binary review (quick/double with 3 inherit subagents), Answer log, 5-part Walkthrough, and commit gate. Trigger on "Implementa il ticket <N>" or "Rivedi il ticket <N>".
---

# Implement Ticket Workflow

Resolve `~` to the OS home directory (`$HOME` on macOS/Linux, `%USERPROFILE%` on Windows) before opening any skill path below. Follow steps 1 to 4 sequentially; for `Rivedi il ticket <N>`, start at Step 3.

## 1. Pre-flight & Surgical Implementation

1. Read the target ticket in `.scratch/<work>/issues/<NN>-<slug>.md`, the repo's `AGENTS.md` (plus any stack doc it points to), and run `git log -n 5 --oneline`.
2. Run the repo's build and existing test suite before editing. Keep all existing tests intact and passing throughout your edits.
3. Locate exact call sites and symbols with search/LSP tools, then apply surgical edits on existing files (use short single-line target anchors on CRLF files so edits match reliably and keep diffs minimal). Cite code by **path and symbol**.

*Done when* the ticket's behavior is implemented cleanly and existing tests remain passing.

## 2. Documentation & Deterministic Gate

1. Update the affected module page in `docs/` and keep `docs/index.mdx`, `docs/docs.json`, and `docs/SUMMARY.md` aligned following `~/.agents/skills/junior-deep-docs/SKILL.md` (document API parameters, flags, units, ownership, and thread contracts; reference code by **file and symbol**).
2. When UI, forms, or layouts changed, check touched controls and states against `~/.agents/skills/ui-ux-doctrine/SKILL.md`.
3. Run every deterministic check listed in `AGENTS.md` (build, unit tests, designer/lint, sync/budget checks) until all exit `0`.

*Done when* all deterministic checks and builds exit `0` and `docs/` matches the code.

## 3. Binary Review & Single-Pass Fix

Run `git add -N -- . ':(exclude).scratch'` so new files appear in the diff while `.scratch/` stays excluded. Pass the ticket path and the read-only command `git diff -- . ':(exclude).scratch'` directly so subagents inspect live diffs from Git.

- **`Review: quick`:** run zero subagents; self-verify every acceptance criterion, `AGENTS.md` rule, and `docs/` page against the diff.
- **`Review: double`:** launch **3 parallel fresh-context subagents on `inherit`** (same model as this session) with read-only access, passing each the ticket path, the command `git diff -- . ':(exclude).scratch'`, and its inline brief below. In Antigravity, end your turn right after launching them so the runtime wakes you once all 3 complete. Keep `humanizer` and `mintlify` reference manuals closed inside subagents to preserve quota.

### Inline Subagent Briefs (`Review: double`)

1. **`Standards` subagent:**
   - Read the repo's `AGENTS.md` and every stack doc it points to (plus `CODING_STANDARDS.md` / `CONTRIBUTING.md` if present), the ticket, and `git diff -- . ':(exclude).scratch'`.
   - Check: (a) repo coding standards and stack invariants (including docstrings/XMLDoc with units, memory ownership, and thread constraints); (b) **smell baseline** (Fowler judgement calls overridden by repo standards; skip tooling-enforced rules): Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest; (c) `~/.agents/skills/ui-ux-doctrine/SKILL.md` if UI changed; (d) `docs/` alignment (updated symbols, state structs with units/threads, API params/flags, `index.mdx`/`docs.json`/`SUMMARY.md` links, natural headings, zero AI tells or emoji). Report hard violations vs judgement calls by file/symbol in under 400 words.
2. **`Spec` subagent:**
   - Read the ticket (and parent `spec.md` if referenced) plus `git diff -- . ':(exclude).scratch'`.
   - Report: (a) missing or partial acceptance criteria; (b) unrequested behavior (scope creep); (c) implemented logic that contradicts the ticket or relaxes/mocks away real tests. Quote the ticket/spec line for each finding, under 400 words.
3. **`ponytail-review` subagent (6 axes):**
   - Inspect `git diff -- . ':(exclude).scratch'`, the ticket, and **connected code** (callers, callees, tests, config). Trace real data flow and assumed load across 6 axes: (1) **Bug** (wrong result, crash, edge cases, broken callers); (2) **Risk** (injection, secrets, unchecked input, data loss/write order); (3) **Scale** (races, repeated work, unbounded growth, `O(n^2)`); (4) **Missing test** (risky new branch/parser/security fix that lacks a failing test); (5) **Speed** (real hot-path slowdowns); (6) **Lean** (dead code, duplicated or reimplemented helpers, YAGNI abstractions, mixed-job functions).
   - Require a concrete failure scenario per finding verified in source files; group into **Must fix / Should fix / Nice to have**, ending with `Verdict: Ship.` or `Verdict: fix ... first.`

### Filter & Single-Pass Fix

Verify every reported finding directly in source code (`Read`/`Grep`); discard false positives and out-of-scope style tastes silently. Fix all real defects, leaks, warnings, spec gaps, and `docs/` gaps in **one pass**, then re-run Step 2 deterministic checks until green (ask the user only if a fix alters visible product behavior).

*Done when* every real review finding is fixed and Step 2 deterministic checks pass after the last edit.

## 4. Answer, Walkthrough & Commit Gate

1. Append `## Answer` to `.scratch/<work>/issues/<NN>-<slug>.md` (and update `.scratch/<work>/map.md` if present), keeping `Status` open until user approval: record modified files, exact test/check summary lines and exit codes copied from tool output, `Tentativi: <N>`, and `Finding review: <tot> (<fixed>, <discarded>)`.
2. Present the **5-section Walkthrough** in plain Italian:
   - **A. Cosa fa adesso il programma** (2 sentences on practical user-facing effect).
   - **B. Il giro degli Eventi e dei Dati** (vertical `flowchart TD`, 5-9 blocks).
   - **C. Sotto il cofano: API, Funzioni, Parametri e Flag usati** (`Funzione / API | Scopo | Parametri e Flag | Tipo di ritorno e Unità | Perché e Fonte`).
   - **D. I mattoni del codice (Scheda SMIG)** (2-4 key passages: file + symbol, 1-5 line snippet, mechanism with variables/state, why, gotcha).
   - **E. Prova manuale HITL** (when `HITL: yes`: preconditions, numbered single physical action per step using **visible natural UI labels** rather than internal control names, expected UI result, and expected log line; after user tests, read the newest `.txt` log and record each test outcome or `"non provato"` in `## Answer`).
3. Ask confirmation (`Committo?`). After user approval:
   - **Versioned repo** (`.scratch/` tracked in Git): set `Status: resolved` immediately before committing, then commit only the ticket files and its `.scratch/` ticket (commit hash stays inspectable via `git log -- <ticket>`).
   - **Hybrid repo** (`.scratch/` excluded from Git): commit the code changes first, then write `Status: resolved` and `Commit: <hash>` in the ticket file.

*Done when* `## Answer` holds verified outputs, the Walkthrough is presented, and `Status: resolved` is recorded with user confirmation.
