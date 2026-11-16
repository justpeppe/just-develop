---
name: junior-deep-docs
description: Write or update docs/ (Mintlify + GitBook SUMMARY.md) for a junior developer: runtime chains, state fields with units/threads, and every function, API parameter, and flag. Trigger after changing documented code, when asked to document a module, or to keep a chat explanation of code.
---

# Junior deep docs

The reader is a junior developer learning what runs under the hood. Explain every mechanism in full so the module is transparent from trigger to side effect.

## 1. Investigate

Read the module's source before writing and answer six questions:

1. **Boundaries:** which files belong to the module, who calls it, and what it delegates elsewhere.
2. **Runtime chain:** in order, what happens from trigger (click, command, hook, request) to final effect: `trigger -> handler -> function -> called function`.
3. **State:** every type, record, struct, enum, field, or JSON schema holding state; for each field list its unit (`ms`, `byte`, `Hz`, `0..1`), ownership (who creates/frees), and thread constraints.
4. **Inventory:** every public or key function, constant, pattern, and type in each file by **file and symbol**.
5. **Calls:** for each project function and external API call, explain every parameter, flag, return type and unit, and why this call was chosen over alternatives.
6. **Traps and checks:** built-in defences against subtle bugs (encoding, path quirks, races, null/empty values, quoting) and the command or manual check verifying the module.

*Done when* boundaries are mapped and every inventory item answers questions 2, 3, 5, and 6.

## 2. Write the page

Move from high-level behavior down to the single flag using Mintlify components (`<Info>`, `<Steps>`, `<Tabs>`, `<AccordionGroup>`, `<Warning>`):

1. **What it does & invariants:** practical role of the module, invariants and design choices (why it is shaped this way), a `File | Role | Called by | Not its job` table, and a vertical `flowchart TD` diagram.
2. **The run:** `<Steps>` for the runtime chain, a `Control | Event | Handler | Effect` table for UI modules, and the state table with units, ownership, and thread rules.
3. **Each file:** one section per file and one subsection per key symbol or cohesive group, quoting exact code and explaining non-obvious logic and its cause.
4. **Reference:** functions and external calls with parameters, flags, and return types/units; traps in `<Warning>` or `<AccordionGroup>`; verification commands or manual test steps.

Keep `docs/index.mdx` (complete repo file catalogue + page map), `docs/docs.json`, and `docs/SUMMARY.md` in sync with every page.

## Style

- Name each heading after the real file, mechanism, or symbol so the sidebar alone teaches the system.
- Open every page and section with a direct statement about the system itself.
- Write plain, direct prose in ASCII punctuation following `humanizer` clarity (literal headings, concrete claims, varied sentence openings, active verbs).
- Place code containing `|`, `{}` or `<>` in fenced code blocks outside table cells so MDX parses cleanly.
- Reference code strictly by **file and symbol**; keep quoted snippets matching the current source.

## Done when

- every tracked repo file appears in the catalogue in `docs/index.mdx`;
- `docs/docs.json` and `docs/SUMMARY.md` list every page and every listed page exists on disk;
- every key symbol, state field (with unit/thread), external call, and flag of the touched module is documented by name;
- `mint validate` (or `npx mint dev`) renders pages cleanly without MDX or link errors.
