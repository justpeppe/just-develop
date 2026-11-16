# Personal global rules

**Language.** Reply in plain Italian and explain jargon the first time it appears. Code, comments, and identifiers stay in English unless a repo's `AGENTS.md` says otherwise.

**Style.** Go straight to the point, without AI preamble, and number the steps of a procedure. When the user asks why, explain principle and cause in full.

**Next prompts.** End every turn that waits on the user with the exact commands or prompts to paste next, in a code block.

**Commits.** Commit only after the user confirms, once the review in `flow.md` is done and the checks listed in the repo's `AGENTS.md` pass. Keep commit messages and PR descriptions as plain human-authored Conventional Commits.

**Shell.** On macOS use zsh syntax: quote every glob passed to a tool (`--include='*.m'`) and keep leading `=` tokens out of commands. On Windows use PowerShell syntax (`;` instead of `&&`).
