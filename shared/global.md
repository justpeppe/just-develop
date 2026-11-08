# Shared global rules

**Scope.** Change exactly what was asked. When you spot an improvement beyond the request, name it in one line at the end and let the user decide.

**Commits.** `type: description`, at most 15 words after the colon, where `type` is a conventional-commit type (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`). A repo's own `AGENTS.md` may set another format; it wins.

**Code comments.** Plain one-line comments, separated by blank lines. Numbered steps and bullets belong in the text around the code.

**Agent memory.** When the user runs `/retro` or `/grill-with-docs`, also read this project's agent memory (Claude Code: `~/.claude/projects/<project-path-with-dashes>/memory/`) and propose, entry by entry, what to promote into `AGENTS.md` and what to archive.

**Antigravity CLI.** Never run `agy` from the terminal: it hangs until timeout. Ask the user to test in the Antigravity app instead. Never delete `~/.gemini/bin/agy`: the app's hub process runs from it.

**Orchestration.** Claude decides and writes specs and tickets; Gemini implements each ticket and runs its own review, as `flow.md` describes. When a subagent did research or implementation for you, check the result before calling it done. In the same turn, without waiting for `/retro`, name each executor error that could recur and propose the line for the repo's `AGENTS.md` or the ticket template that would prevent it; apply it once the user agrees.

**Evidence.** Every factual claim about a tool, model or practice, and every pro and con, says where it is read: official documentation or guideline (who publishes it, which page, date read), a named author with date, the code, or a command actually run. Read live sources instead of relying on memory; prefer the last months, because models change quickly. File and function names are enough: line numbers are optional, because they go stale. Mark what has no source as `non verificato`, and say so when a source measures nothing.
