# Personal global rules

**Language.** Reply in plain Italian and explain jargon the first time it appears. Code, comments and identifiers stay in English unless a repo's `AGENTS.md` says otherwise.

**Next prompts.** End every turn that waits on the user with the exact commands or prompts to paste next, in a code block.

**Commits.** Commit only after the user confirms, once the review in `flow.md` is done and the repo's checks and tests, as its `AGENTS.md` lists them, pass. Commit messages and PR descriptions carry no `Co-Authored-By` trailer or other AI attribution line.

**Shell.** On Mac the shell is zsh: quote every glob passed to a tool (`--include='*.m'`) and keep words starting with `=` out of commands. On Windows use PowerShell syntax.
