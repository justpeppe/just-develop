---
name: implement-ticket
description: "Execute or re-review a ticket end-to-end: pre-flight, surgical edits, docs, quick/triple review, Answer, Walkthrough, and commit gate. Trigger on \"Implementa il ticket <N> di <spec>\" or \"Rivedi il ticket <N> di <spec>\"."
---

# Implement Ticket Workflow

Open referenced `~/.agents/skills/*/SKILL.md` files directly from the user home directory (`$HOME` or `%USERPROFILE%`). For standalone `Rivedi il ticket <N> di <spec>`, start at Step 3. If `<spec>` is omitted and multiple specs in `.scratch/` contain ticket `<N>`, ask the user which spec to run.

## 1. Pre-flight & Surgical Implementation

1. Read `.scratch/<work>/issues/<NN>-<slug>.md`, the repo's `AGENTS.md` (plus any stack doc it points to), and `git log -n 5 --oneline`.
2. Run the repo's build and existing test suite before editing, keeping all existing tests green throughout.
3. Apply surgical edits to the files and symbols named in the ticket (use short single-line target anchors on CRLF files so edits match reliably).

*Done when* every ticket change is implemented and existing tests pass.

## 2. Documentation & Deterministic Gate

1. Read and follow `~/.agents/skills/junior-deep-docs/SKILL.md` to update the touched module page in `docs/` and `docs/index.mdx` (plus `docs/docs.json` and `docs/SUMMARY.md` when present).
2. When UI, forms, or layouts changed, read and verify touched controls and states against `~/.agents/skills/ui-ux-doctrine/SKILL.md`.
3. Run every build and deterministic check in `AGENTS.md` until all exit `0`.

*Done when* all `AGENTS.md` checks exit `0` and `docs/` matches the code.

## 3. Binary Review & Single-Pass Fix

Run `git add -N -- . ':(exclude).scratch'` so new files appear in the diff while `.scratch/` stays excluded, and review `git diff -- . ':(exclude).scratch'`:

- **`Review: quick`:** run zero subagents; self-verify every acceptance criterion, `AGENTS.md` rule, and `docs/` update against the diff.
- **`Review: triple`:** launch **3 parallel read-only subagents on `inherit`** with fresh context, passing each the ticket path, `git diff -- . ':(exclude).scratch'`, and its inline brief below (subagents work strictly from repo files, the diff, and their inline brief; in Antigravity, end your turn right after launching them so the runtime resumes once all 3 finish).

### Inline Subagent Briefs (`Review: triple`)

1. **`Standards` subagent:**
   - Read `AGENTS.md` and every stack doc it references (plus `CODING_STANDARDS.md` / `CONTRIBUTING.md` when present), the ticket, and `git diff -- . ':(exclude).scratch'`.
   - Check: (a) repo coding standards and stack invariants (docstrings/XMLDoc with units, ownership, and thread rules); (b) Fowler judgement-call smells (overridden by repo standards; skip linter-enforced rules): Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest; (c) `~/.agents/skills/ui-ux-doctrine/SKILL.md` when UI changed; (d) `docs/` alignment (updated symbols, state fields with units/threads, API params/flags, `index.mdx` and optional `docs.json`/`SUMMARY.md` links, literal headings, plain direct prose free of emoji). Report hard violations vs judgement calls by file and symbol in under 400 words.
2. **`Spec` subagent:**
   - Read the ticket (and parent `spec.md` when referenced) plus `git diff -- . ':(exclude).scratch'`.
   - Report: (a) missing or partial acceptance criteria; (b) unrequested behavior (scope creep); (c) logic that contradicts the ticket or weakens/mocks away real tests. Quote the ticket/spec requirement for each finding in under 400 words.
3. **`diff-review` subagent (6 axes):**
   - Inspect `git diff -- . ':(exclude).scratch'`, the ticket, and connected callers, callees, tests, and config across 6 axes: (1) **Bug** (wrong result, crash, edge cases, broken callers); (2) **Risk** (injection, secrets, unchecked input, data loss/write order); (3) **Scale** (races, repeated work, unbounded growth, `O(n^2)`); (4) **Missing test** (untested risky branch, parser, or security fix); (5) **Speed** (real hot-path regressions); (6) **Lean** (dead code, duplicated helpers, speculative abstractions, mixed-responsibility functions).
   - Verify a concrete failure scenario in source files for every finding; group into **Must fix / Should fix / Nice to have**, ending with `Verdict: Ship.` or `Verdict: fix ... first.`

### Filter & Single-Pass Fix

Verify each reported finding directly in source files; keep only confirmed defects and fix code and `docs/` in a single pass, then re-run Step 2 checks until all exit `0` (ask the user first if a fix alters user-visible behavior).

*Done when* all confirmed review findings are fixed and Step 2 checks exit `0` after the final edit.

## 4. Answer, Walkthrough & Commit Gate

1. Append `## Answer` to `.scratch/<work>/issues/<NN>-<slug>.md` (and update `.scratch/<work>/map.md` when present), keeping `Status` open until user approval: record modified files, exact check/test summary lines with exit codes, and resolved review findings.
2. Present the **5-section Walkthrough**:
   - **A. Cosa fa adesso il programma** (2 sentences on user-facing effect).
   - **B. Il giro degli Eventi e dei Dati** (vertical `flowchart TD`, 5-9 nodes).
   - **C. Sotto il cofano: API, Funzioni, Parametri e Flag usati** (`Funzione / API | Scopo | Parametri e Flag | Tipo di ritorno e Unità | Perché e Fonte`).
   - **D. Passaggi chiave del codice** (2-4 passages: file + symbol, 1-5 line snippet, state/variables mechanism, why, gotcha).
   - **E. Prova manuale HITL** (when `HITL: yes`: state preconditions once, then list `Test A`, `Test B`, ... with numbered single physical actions naming only visible UI cues (icon, shape, label, position, or key, e.g. *"clicca il pulsante a forma di microfono `Voice`"*), followed by `Atteso:` visible/audible outcome and `Log:` what to check in the latest runtime log; after user testing, read the latest log and record each result or `"non provato"` in `## Answer`).
3. Ask `Committo?` and wait for user approval:
   - **Versioned repo** (`.scratch/` tracked in Git): set `Status: resolved`, then commit the ticket's code/doc changes together with its `.scratch/` ticket file.
   - **Hybrid repo** (`.scratch/` excluded from Git): commit the ticket's code changes first, then write `Status: resolved` and `Commit: <hash>` in the ticket file.

*Done when* `## Answer` holds verified outputs, the Walkthrough is presented, and `Status: resolved` is recorded with user confirmation.
