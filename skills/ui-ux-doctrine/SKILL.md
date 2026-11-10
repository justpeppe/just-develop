---
name: ui-ux-doctrine
description: Usability and accessibility rules for any user interface, from desktop windows and forms to web pages and HTML reports. Use when designing, building, changing or reviewing a screen, form, dialog, layout or interactive flow.
---

# UI/UX doctrine

Apply these rules to the controls and flows the current change creates or touches. Defects in untouched UI go in the report as optional observations.

When the repo has a design system (a `design.md`, tokens, shared styles or components), it comes first: follow its palette, typography, spacing and components.

## Feedback and control

The response time limits are Jakob Nielsen's three limits (NN/g).

- Answer every action with visible feedback within 0.1 s. Past 1 s, show that work is running. Past 10 s, show progress and a way to cancel.
- Label things with the user's domain words, as the repo's glossary defines them.
- Give every state a clear way out: Cancel, Undo, Esc.
- Place destructive actions (Delete, Clear, Reset) apart from frequent ones (Save, OK), and confirm them when they cannot be undone.
- Follow the platform's conventions: standard shortcuts, Enter for the default action, Esc to cancel, a logical tab order.
- Group related fields into small visual chunks, and move secondary options into a menu or an advanced section.

## Accessibility: WCAG 2.2 level AA

- Text contrast at least 4.5:1; large text and the boundaries of UI components at least 3:1 (SC 1.4.3, 1.4.11).
- Pointer targets at least 24 by 24 CSS px, or spaced so a 24 px circle centred on each touches no other target (SC 2.5.8).
- Every flow works from the keyboard, with a visible focus indicator (SC 2.1.1, 2.4.7).
- Meaning travels in text, an icon or a shape as well as colour (SC 1.4.1).

## States and responsiveness

Every view that shows data or runs work covers four states:

1. **Empty:** what is missing and how to add it.
2. **Loading:** progress, and cancel for long work.
3. **Success:** the resulting state, visible.
4. **Error:** the cause in human words and the action that recovers.

Slow I/O, network, database and file work runs off the UI thread, so the window keeps responding.

## Done when

Each touched control and flow passes this list, and the report names what was checked:

- tab order, Enter and Esc behave as the platform expects;
- destructive actions are separated, and confirmed when irreversible;
- status and errors carry text or an icon alongside colour;
- long operations keep the UI responsive and show progress and errors;
- the UI checks listed in the repo's `AGENTS.md`, if any, pass.
