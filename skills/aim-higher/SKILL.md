---
name: aim-higher
description: Explore code, official docs, and the web for principle, cause, and senior options before locking a plan. Trigger at the start of /flow-design, /grill-with-docs, /wayfinder, or when the user asks to aim higher ("pensa più in grande").
---

# Aim higher

Run this before fixing a plan so the design reflects what a senior engineer would choose from evidence, rather than patching a symptom. If the user replies `salta`, move straight to the smallest viable solution.

## 1. Gather evidence

Collect facts from three sources before proposing options:

1. **The code:** how the area works today, which files, symbols, and data structures are involved, and who calls them. Read `GLOSSARY.md` and relevant ADRs when present.
2. **Official documentation:** language, framework, or library behavior in the version the project runs.
3. **The web:** standards, protocols, established libraries, and engineering practice for this class of problem.

Cite code by **file and symbol**, and external pages by publisher, title, and date read.

*Done when* every claim used in steps 2 and 3 cites a verified source or is marked `non verificato`.

## 2. Principle and cause

State in plain words:

- **The real need:** the outcome behind the requested change.
- **The mechanism:** the technical principle governing the problem (event loop, memory ownership, state/UI separation, algorithmic complexity) and how experienced engineers address it.
- **The outside judge:** the objective check proving the solution works (automated test, build, before/after measurement, reproduction). Label any unmeasured target as a hypothesis.

## 3. Options

Present 2 or 3 concrete options, placing the recommended one first and marked `(Consigliata)`. Always include the documented standard or best practice with its source, and weigh any user-proposed option on equal terms.

For each option state: how it works (which modules and symbols it touches), pros, and cons.

Keep scope tied to the current work; capture ideas that widen scope as a follow-up note. End by asking which option to carry into grilling or spec.

*Done when* 2-3 evidence-backed options are presented and the user picks a direction (or replies `salta`).
