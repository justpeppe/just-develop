---
name: aim-higher
description: Grounded, ambitious exploration before a plan is fixed, backed by the code, official docs and the web. Use at the start of /grill-with-docs or /wayfinder on new work, or when the user asks to aim higher ("pensa più in grande").
---

# Aim higher

Run this before the plan is fixed. The target is the choice a senior engineer would make, backed by evidence, in place of a patch over the symptom. The user can answer `salta` at any point: then go straight to the smallest solution.

## 1. Gather evidence

Collect facts from three sources before proposing anything:

1. **The code:** how the area works today, which files, functions and data structures are involved, who calls them. Read the repo's glossary and ADRs when they exist.
2. **Official documentation** of the language, framework or library, in the version the project uses.
3. **The web:** standards, protocols, established libraries and engineering practice for this class of problem.

Cite code by file and symbol, and pages by publisher, title and date read.

*Done when* every claim used in steps 2 and 3 has a source or is marked `non verificato`.

## 2. Principle and cause

State, in plain words:

- **The real need:** the outcome behind the requested change.
- **The mechanism:** the technical principle that governs the problem (event loop, memory ownership, state and UI separation, algorithmic complexity) and what an expert does about it.
- **The outside judge:** the objective check that will prove the solution works: a test, a build, a before and after measurement, a reproduction. A target nobody can measure yet is a hypothesis; label it so.

## 3. Options

Present 2 or 3 concrete options, the recommended one first and marked `(Consigliata)`. The documented standard or best practice is always one of them, with its source. A solution the user already proposed sits among the options on equal terms.

For each option: how it works in practice (which modules it touches), pros, cons.

Ambition raises the standard of the current work. Inside a ticket, the ticket is the scope: ideas that widen it go back as a note for a future ticket.

End by asking which option to carry into `/grill-with-docs` or `/to-spec`.
