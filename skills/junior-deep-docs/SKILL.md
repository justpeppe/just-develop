---
name: junior-deep-docs
description: Write or update the code guide in docs/ (Mintlify, with a GitBook-compatible SUMMARY.md) so a junior developer understands how the code works, down to every function, data field, API parameter and flag. Use after a change touches code that docs/ explains, when the user asks to document a module, or when a question about the code in chat deserves to be kept.
---

# Junior deep docs

The reader is a junior developer who must understand what runs under the hood. Every mechanism gets its explanation; nothing stays a black box.

## 1. Investigate

Read the module's source in full before writing, and answer six questions:

1. **Boundaries:** which files belong to the module, who calls it, what it leaves to other modules.
2. **Runtime chain:** in order, what happens from the trigger (a click, a command, a hook, a request) to the final effect: `trigger -> handler -> function -> called function`.
3. **State:** every type, record, enum, field or JSON structure that holds state; for each field its unit (`ms`, `byte`, `Hz`, range `0..1`), who creates and frees it, and which thread reads and writes it.
4. **Inventory:** every function, constant, regular expression and type in each file.
5. **Calls:** for each project function and each external API call, what each parameter means, what each flag does, the type and unit of the return value, and why this call instead of an alternative.
6. **Traps and checks:** the defences in the code against subtle bugs (encoding marks, path quirks, deadlocks, null references, quoting) and the command or manual test that verifies the module.

*Done when* the boundaries are written down and every item in the inventory has its answers to questions 2, 3, 5 and 6.

## 2. Write the page

Go from the big picture down to the single flag, with Mintlify components (`<Info>`, `<Steps>`, `<Tabs>`, `<AccordionGroup>`, `<Warning>`):

1. **What it does:** what this part of the system does in reality and which problem it solves; then the table `File | Role | Called by | Not its job` and a `flowchart TD` diagram.
2. **The run:** `<Steps>` for the runtime chain. With a UI, the table `Control | Event | Handler | Effect`. The state table with units, ownership and thread.
3. **Each file:** one section per file, one subsection per function or group of related code, quoting the real code and explaining each non-obvious instruction and the reason for it.
4. **Reference:** every function and external call with parameters, flags and return values; then the traps in `<Warning>` or `<AccordionGroup>`, and the verification commands or manual test steps.

Keep `docs/index.mdx`, `docs/docs.json` and `docs/SUMMARY.md` listing every page, and the catalogue in `docs/index.mdx` listing every file of the repo.

## Style

- Each heading names the real file, mechanism or function it covers, so the sidebar alone teaches the system.
- Each page and section opens with a statement about the system itself.
- Plain prose, edited with `humanizer`, in text without emoji.
- Code that contains `|`, `{}` or `<>` goes in a fenced block outside table cells, so MDX parses it.
- Point at code by file and function; quoted code matches the current source.

## Done when

- every repo file appears in the catalogue in `docs/index.mdx`;
- every function, type, field, external call and flag of the module is explained on its page, each one by name;
- `npx mint dev` renders the pages without MDX errors.
