import json
import os
import re
import sys

REASON_GIT = (
    "I comandi git distruttivi o verso l'esterno ('push', 'merge', 'reset --hard', "
    "'clean -f', 'branch -D/-f', 'checkout -- / .', 'restore', 'stash drop') sono bloccati: "
    "possono perdere lavoro locale o cambiare il remoto. Vanno eseguiti manualmente dallo sviluppatore."
)
GIT_WORD = "git"
GIT_BLOCKED_SUBCOMMANDS = {"push", "merge"}

# Global git options that take a separate value, such as -C <path> or -c <name=value>.
GIT_OPTIONS_WITH_ARG = {
    "-c",
    "-C",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--super-prefix",
    "--exec-path",
    "--config-env",
}

LAUNCHERS = {"env", "sudo", "command", "exec", "nohup", "time"}
SHELLS = {"sh", "bash", "zsh", "dash", "pwsh", "powershell"}
ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
SHELL_RUN_FLAG = re.compile(r"^-(?:[a-z]*c|command)$", re.IGNORECASE)

# A letter after the last dot keeps tags and release branches such as v1.2.0 out.
FILE_EXTENSION = re.compile(r"\.[a-zA-Z][a-zA-Z0-9]*$")

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?([^\n]*)\n.*?\n\1[ \t]*(?=\n|$)", re.DOTALL)
LEX_TOKEN = re.compile(r'\\.|"(?:\\.|[^"\\])*"|\'[^\']*\'|(?:^|(?<=[\s;&|()]))#[^\r\n]*', re.DOTALL)
BACKTICK_SUB = re.compile(r"`([^`\r\n]*\S+\s+\S+[^`\r\n]*)`")
CMD_IN_DQUOTES = re.compile(r"\$\(([^)\r\n]+)\)|`([^`\r\n]*\S+\s+\S+[^`\r\n]*)`")
WORD_TOKEN = re.compile(r'(?:\\.|"(?:\\.|[^"\\])*"|\'[^\']*\'|\S)+', re.DOTALL)


def extract_git_subcommand_and_args(args):
    """Return the git subcommand and its arguments, skipping global options and their values."""
    i = 0
    while i < len(args):
        arg = args[i].strip("\"'")
        if not arg:
            i += 1
            continue

        if arg in GIT_OPTIONS_WITH_ARG:
            i += 2
            continue

        if arg.startswith("-"):
            i += 1
            continue

        subcommand = re.sub(r"[\\`]", "", arg).lower()
        sub_args = []
        for raw in args[i + 1:]:
            a = raw.strip("\"'")
            if not a:
                continue
            s = re.sub(r"[\\`]", "", a)
            sub_args.append(s if (s.startswith("-") or s == ".") else re.sub(r"^[\\`]+(?=\.[\\/])", "", a))
        return subcommand, sub_args
    return "", []


def names_a_path(arg, cwd):
    """Tell a checkout argument that is a file or folder from a branch or tag."""
    if arg.startswith("-"):
        return False
    return bool(FILE_EXTENSION.search(arg)) or os.path.exists(os.path.join(cwd, arg))


def is_dangerous_git(subcommand, sub_args, cwd=""):
    """Return True when the git subcommand and arguments match a destructive operation."""
    if subcommand in GIT_BLOCKED_SUBCOMMANDS:
        return True

    if subcommand == "reset" and any(a in ("--hard", "-hard") for a in sub_args):
        return True

    if subcommand == "clean" and any(a == "--force" or re.match(r"^-[a-zA-Z]*f", a) for a in sub_args):
        return True

    if subcommand == "branch" and any(a == "--force" or re.match(r"^-[a-zA-Z]*[DfMC]", a) for a in sub_args):
        return True

    # Checkout of a branch is allowed; checkout of files rewrites the working tree without a trace.
    if subcommand == "checkout":
        if any(a in (".", "--", "-f", "--force") or re.match(r"^-[a-zA-Z]*B", a) or a.startswith(("./", ".\\")) for a in sub_args):
            return True

        # shortcut: `git -C other checkout name` is checked against cwd, resolve -C if it ever misses a file.
        creates_branch = any(a in ("-b", "--orphan") for a in sub_args)
        if not creates_branch and any(names_a_path(a, cwd) for a in sub_args):
            return True

    # Restore discards working-tree changes unless it only touches the index.
    if subcommand == "restore":
        has_staged = any(a == "--staged" or re.match(r"^-[a-rt-zA-Z]*S", a) for a in sub_args)
        has_worktree = any(a == "--worktree" or re.match(r"^-[a-rt-zA-Z]*W", a) for a in sub_args)
        if not (has_staged and not has_worktree):
            return True

    if subcommand == "switch" and any(a in ("-f", "--force", "--discard-changes") for a in sub_args):
        return True

    if subcommand == "stash" and any(a.lower() in ("drop", "clear", "pop") for a in sub_args):
        return True

    return False


def sanitize_for_split(cmd):
    cmd = HEREDOC.sub(lambda m: "<<" + m.group(1) + m.group(2), cmd)
    extra = []

    def repl(m):
        tok = m.group(0)
        if tok.startswith("#"):
            return ""
        if tok[0] == "'":
            return re.sub(r"[\r\n;&|()`]", " ", tok)
        if tok[0] == '"':
            for g1, g2 in CMD_IN_DQUOTES.findall(tok):
                extra.append((g1 or g2).replace('\\"', '"'))
            return re.sub(r"[\r\n;&|()]", " ", tok).replace("`", "")
        return tok

    lexed = LEX_TOKEN.sub(repl, cmd)
    cleaned = BACKTICK_SUB.sub(lambda m: " ; " + m.group(1) + " ; ", lexed)
    if "`" in lexed:
        cleaned += " ; " + re.sub(r"`\r?\n", " ", lexed).replace("`", "")
    return cleaned + "".join(" ; " + e for e in extra)


def strip_launchers(words):
    """Drop leading VAR=value words and launchers such as env or sudo."""
    # shortcut: a launcher option with a separate value (sudo -u bob) stops here, parse each launcher if that shows up.
    i = 0
    while i < len(words) and (ASSIGNMENT.match(words[i]) or words[i].lower() in LAUNCHERS or (i and words[i].startswith("-"))):
        i += 1
    return words[i:]


def is_dangerous_part(words, cwd):
    """Check one simple command, also looking inside `sh -c` style arguments."""
    words = strip_launchers(words)
    if not words:
        return False

    base = re.split(r"[\\/]", words[0])[-1].replace("`", "").lower()
    base = re.sub(r"\.exe$", "", base)

    # Separators inside the quoted script are already blanks here, so every git word is checked.
    if base in SHELLS and any(SHELL_RUN_FLAG.match(w) for w in words[1:]):
        inner = " ".join(words[1:]).split()
        return any(
            w == GIT_WORD and is_dangerous_git(*extract_git_subcommand_and_args(inner[i + 1:]), cwd)
            for i, w in enumerate(inner)
        )

    return base == GIT_WORD and is_dangerous_git(*extract_git_subcommand_and_args(words[1:]), cwd)


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print("{}")
        return

    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        print("{}")
        return

    # Only the first word of each simple command counts, so a folder named git in an argument never matches.
    cwd = data.get("cwd") or ""
    for part in re.split(r"&&|\|\||[;&|\r\n()]", sanitize_for_split(cmd)):
        words = [w.strip("\"'") for w in WORD_TOKEN.findall(part.strip())]
        if is_dangerous_part([w for w in words if w], cwd):
            deny(REASON_GIT)

    print("{}")


if __name__ == "__main__":
    main()
