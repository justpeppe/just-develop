---
name: ui-ux-doctrine
description: Usability and accessibility rules (WCAG 2.2 AA, Nielsen limits) for desktop windows, web pages, forms, dialogs, and HTML reports. Trigger when designing, building, changing, or reviewing any screen, layout, or interactive flow.
---

# UI/UX doctrine

Apply these rules to the controls and flows created or modified by the current change. Report defects in untouched UI separately as optional notes.

When the repo provides a design system (`design.md`, tokens, shared styles, or UI components), follow its palette, typography, spacing, and components first.

## Feedback and control

Response time thresholds follow Jakob Nielsen's three limits (NN/g):

- Give visible feedback within `0.1 s`; past `1 s`, show an active work indicator; past `10 s`, show progress and a way to cancel.
- Label controls with the user's domain words from `GLOSSARY.md` when present.
- Provide a clear exit from every state (`Cancel`, `Undo`, `Esc`).
- Separate destructive actions (`Delete`, `Clear`, `Reset`) from frequent ones (`Save`, `OK`), and confirm irreversible actions.
- Respect platform conventions: standard shortcuts, `Enter` for the default action, `Esc` to cancel, logical tab order.
- Group related fields into small visual chunks, moving secondary options into a menu or advanced section.

## Accessibility: WCAG 2.2 level AA

- Maintain at least `4.5:1` contrast for normal text and `3:1` for large text and UI component boundaries (SC 1.4.3, 1.4.11).
- Size pointer targets at least `24 x 24 CSS px`, or space them so a `24 px` circle centred on each clears adjacent targets (SC 2.5.8).
- Ensure every flow works from the keyboard with a visible focus indicator (SC 2.1.1, 2.4.7).
- Convey meaning with text, an icon, or a shape alongside colour (SC 1.4.1).

## States and responsiveness

Design every data-driven or async view for four explicit states:

1. **Empty:** what is missing and how to add it.
2. **Loading:** progress indicator, plus cancel for long work.
3. **Success:** visible confirmation of the resulting state.
4. **Error:** cause in plain human words and the action that recovers.

Run slow I/O, network, database, and file operations off the UI thread so the interface keeps responding.

## Done when

Each touched control and flow passes all items below, and the report lists what was checked:

- tab order, `Enter`, and `Esc` behave as the platform expects;
- destructive actions are separated and confirmed when irreversible;
- status and errors carry text or an icon alongside colour;
- long operations keep the UI responsive with progress and error recovery;
- any UI checks listed in the repo's `AGENTS.md` pass.
