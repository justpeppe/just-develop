# Shared global rules

**Scope.** Change exactly what was asked. When you spot an improvement beyond the request, name it in one line at the end and let the user decide.

**Commits.** `type: description`, at most 15 words after the colon, where `type` is a conventional-commit type (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`). A repo's own `AGENTS.md` may set another format; it wins.

**Code comments.** Plain one-line comments, separated by blank lines. Numbered steps and bullets belong in the text around the code.

**Agent memory.** When running `/retro`, `/grill-with-docs`, or `flow-design`, also read this project's agent memory (Claude Code: `~/.claude/projects/<project-path-with-dashes>/memory/`) and propose, entry by entry, what to promote into `AGENTS.md` and what to archive.

**Antigravity CLI.** Test Antigravity changes inside the desktop app instead of running `agy` from a terminal (which hangs until timeout), and preserve `~/.gemini/bin/agy` because the hub process runs from it.

**Secrets.** Read public source files and public configuration examples (`sample`, `template`, `dist`); leave private environment and settings files untouched unless the user explicitly asks to inspect a specific file.

**Orchestration.** Follow the roles and disk handoff in `flow.md`. When a subagent completes research or implementation, verify its result against source files before calling it done; in the same turn, name any recurring executor mistake and propose a one-line prevention for `AGENTS.md` or the ticket contract.

**Evidence.** Every factual claim about a tool, model, or practice, and every pro and con, states where it was read: official documentation (publisher, page, date read), a named author with date, the source code, or a command actually run. Cite **file and symbol** names (function, class, method, constant, config key, section heading); mark missing sources as `non verificato`, and state explicitly when a source measures nothing.
