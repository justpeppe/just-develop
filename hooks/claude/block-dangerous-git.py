import json
import os
import re
import sys

EXT_INI = ".i" + "ni"
EXT_ENV = ".e" + "nv"
ENV_FILE_RE = re.compile(r"^\." + "e" + "nv(.*)$")
SAFE_ENV_SUFFIXES = {".example", ".sample", ".template", ".dist"}

REASON_GIT = (
    "I comandi git distruttivi o di cambio/creazione branch ('push', 'merge', 'reset --hard', "
    "'clean -f', 'branch -D/-f/<nome>', 'checkout', 'switch', 'restore', 'stash drop/pop/clear', "
    "'worktree add/remove/prune') sono bloccati agli agenti: vanno eseguiti manualmente dallo sviluppatore."
)
REASON_SECRET = (
    f"BLOCKED: accesso a file di segreti ({EXT_INI}/{EXT_ENV} di progetto) bloccato da shell. "
    "Usa il relativo *.example/*.sample per la struttura."
)

GIT_WORD = "git"
GIT_BLOCKED_SUBCOMMANDS = {"push", "merge", "checkout", "switch"}

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
COMMIT_OPTIONS_WITH_ARG = {
    "-F", "--file", "-C", "--reuse-message", "-c", "--reedit-message", "--fixup", "--squash",
    "--author", "--date", "-t", "--template", "--cleanup", "-u", "--untracked-files", "--pathspec-from-file",
}

LAUNCHERS = {"env", "sudo", "command", "exec", "nohup", "time"}
SHELLS = {"sh", "bash", "zsh", "dash", "pwsh", "powershell", "cmd"}
ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
SHELL_RUN_FLAG = re.compile(r'^(?:-(?:[a-z]*c|command)|/[ck](?:$|["\']))', re.IGNORECASE)

BRANCH_MUTATING_FLAGS = {
    "-d", "-D", "-f", "-m", "-M", "-c", "-C", "-u",
    "--delete", "--force", "--move", "--copy", "--set-upstream-to", "--unset-upstream", "--edit-description",
}
BRANCH_VALUE_FLAGS = {
    "--contains", "--no-contains", "--merged", "--no-merged", "--points-at",
    "--sort", "--format", "--abbrev", "--color", "--column",
}
BRANCH_LIST_FLAGS = {"-l", "--list"}
WORKTREE_BLOCKED_SUBS = {"add", "remove", "prune", "move", "lock", "unlock", "repair"}

SAFE_GLOB_VALUE = re.compile(r"^[a-zA-Z0-9.*?_~+\-/\\\[\]{},]+$")
PS_NEGATIVE_OPS = {
    "-ne", "-cne", "-ine", "-notin", "-cnotin", "-inotin",
    "-notlike", "-cnotlike", "-inotlike", "-notmatch", "-cnotmatch", "-inotmatch",
    "-notcontains", "-cnotcontains", "-inotcontains",
}
PS_FILE_READERS = {
    "get-content", "gc", "cat", "type", "more", "less", "head", "tail",
    "open", "read", "readalltext", "readalllines", "import-csv", "import-clixml",
    "import-module", "convertfrom-json", "convertfrom-stringdata",
}
RG_VALUE_FLAGS = {
    "-e", "--regexp", "-f", "--file", "-g", "--glob", "--iglob",
    "-t", "--type", "-T", "--type-not", "--type-add", "-A", "-B", "-C", "--context",
    "-m", "--max-count", "--max-filesize", "--encoding", "-j", "--threads",
    "--sort", "--sortr", "--color", "--colors", "--path-separator",
}
SLS_VALUE_FLAGS = {"-pattern", "-path", "-literalpath", "-include", "-exclude", "-context", "-encoding", "-culture"}

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?([^\n]*)\n.*?\n\1[ \t]*(?=\n|$)", re.DOTALL)
PS_HERE_SQ = re.compile(r"@'[ \t]*\r?\n(?:.*?\r?\n)?[ \t]*'@", re.DOTALL)
PS_HERE_DQ = re.compile(r'@"[ \t]*\r?\n(?:(.*?)\r?\n)?[ \t]*"@', re.DOTALL)
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


def is_git_command(word):
    """Return True when word invokes the git binary (bare, .exe, or full path)."""
    base = re.split(r"[\\/]", word)[-1].replace("`", "").lower()
    return re.sub(r"\.exe$", "", base) == GIT_WORD


def is_branch_mutating(sub_args):
    """Allow read-only branch listing/filters; block creating, deleting, renaming, or editing branches."""
    if not sub_args:
        return False
    has_list = False
    positional = []
    i = 0
    while i < len(sub_args):
        a = sub_args[i]
        if a in BRANCH_MUTATING_FLAGS or any(a.startswith(f + "=") for f in BRANCH_MUTATING_FLAGS):
            return True
        if re.match(r"^-[a-zA-Z]*[dDfMmCc]", a):
            return True
        if a in BRANCH_LIST_FLAGS:
            has_list = True
            i += 1
            continue
        if a in BRANCH_VALUE_FLAGS:
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        positional.append(a)
        i += 1
    return bool(positional and not has_list)


def is_dangerous_git(subcommand, sub_args):
    """Return True when the git subcommand and arguments match a destructive or branch-mutating operation."""
    if subcommand in GIT_BLOCKED_SUBCOMMANDS:
        return not (sub_args and all(a in ("-h", "--help") for a in sub_args))

    if subcommand == "reset" and any(a in ("--hard", "-hard") for a in sub_args):
        return True

    if subcommand == "clean" and any(a == "--force" or re.match(r"^-[a-zA-Z]*f", a) for a in sub_args):
        return True

    if subcommand == "branch" and is_branch_mutating(sub_args):
        return True

    if subcommand == "worktree" and any(a.lower() in WORKTREE_BLOCKED_SUBS or a in ("-b", "-B") for a in sub_args):
        return True

    # Restore discards working-tree changes unless it only touches the index.
    if subcommand == "restore":
        has_staged = any(a == "--staged" or re.match(r"^-[a-rt-zA-Z]*S", a) for a in sub_args)
        has_worktree = any(a == "--worktree" or re.match(r"^-[a-rt-zA-Z]*W", a) for a in sub_args)
        if not (has_staged and not has_worktree):
            return True

    if subcommand == "stash" and any(a.lower() in ("drop", "clear", "pop") for a in sub_args):
        return True

    return False


def sanitize_for_split(cmd):
    """Neutralize heredocs, PowerShell here-strings, and comments while exposing inner command substitutions."""
    extra = []
    cmd = HEREDOC.sub(lambda m: "<<" + m.group(1) + m.group(2), cmd)
    cmd = PS_HERE_SQ.sub("@''@", cmd)

    def dq_here(m):
        body = m.group(1) or ""
        for g1, g2 in CMD_IN_DQUOTES.findall(body):
            extra.append((g1 or g2).replace('\\"', '"'))
        return '@""@'

    cmd = PS_HERE_DQ.sub(dq_here, cmd)

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
    i = 0
    while i < len(words) and (ASSIGNMENT.match(words[i]) or words[i].lower() in LAUNCHERS or (i and words[i].startswith("-"))):
        i += 1
    return words[i:]


def extract_shell_inner_tokens(raw_rest):
    """Unwrap cmd /c"...", powershell -Command "& 'git' ..." and tokenize inner commands."""
    chunks = []
    for rw in raw_rest:
        cleaned = re.sub(r'^/[ck](?=$|["\'])', '', rw, flags=re.IGNORECASE)
        if not cleaned:
            continue
        chunks.append(strip_outer_quotes(cleaned))
    joined = ' '.join(c for c in chunks if c)
    joined = re.sub(r'(&&|\|\||[;|\r\n{}()])', r' \1 ', joined)
    out = []
    for tok in WORD_TOKEN.findall(joined):
        if tok in ('&&', '||', ';', '|', '(', ')', '{', '}'):
            out.append(tok)
            continue
        if tok == '&':
            continue
        cleaned = strip_outer_quotes(tok.lstrip('&').strip()).strip("\"'")
        if cleaned:
            out.append(cleaned)
    return out


def is_dangerous_part(raw_words):
    """Check one simple command, also looking inside shell wrappers (sh -c, cmd /c, pwsh)."""
    words = strip_launchers([w.strip("\"'") for w in raw_words])
    if not words:
        return False
    offset = len(raw_words) - len(words)
    raw_rest = raw_words[offset + 1:]

    base = re.split(r"[\\/]", words[0])[-1].replace("`", "").lower()
    base = re.sub(r"\.exe$", "", base)

    if base in SHELLS and any(SHELL_RUN_FLAG.match(w) for w in words[1:]):
        inner = extract_shell_inner_tokens(raw_rest)
        segs, cur = [], []
        for tok in inner:
            if tok in ('&&', '||', ';', '|', '(', ')', '{', '}'):
                if cur:
                    segs.append(cur)
                    cur = []
            else:
                cur.append(tok)
        if cur:
            segs.append(cur)
        for seg in segs:
            for i, w in enumerate(seg):
                if is_git_command(w) and is_dangerous_git(*extract_git_subcommand_and_args(seg[i + 1:])):
                    return True
        return False

    return is_git_command(words[0]) and is_dangerous_git(*extract_git_subcommand_and_args(words[1:]))


def is_secret_token(raw):
    token = raw.strip("\"'` ").strip()
    if not token:
        return False
    lower = token.lower()
    base = re.split(r"[\\/]", lower)[-1]
    if not base:
        return False
    if lower.endswith(EXT_INI) or lower.endswith(EXT_ENV):
        return True
    m = ENV_FILE_RE.match(base)
    return bool(m and m.group(1) not in SAFE_ENV_SUFFIXES)


def strip_outer_quotes(s):
    if len(s) >= 2 and ((s[0] == '"' and s.endswith('"')) or (s[0] == "'" and s.endswith("'"))):
        return s[1:-1]
    return s


def is_self_contained_exclusion(raw_word):
    t = strip_outer_quotes(raw_word.strip())
    val = None
    if t.startswith((":!", ":^")):
        val = t[2:]
    elif m := re.match(r"^:\([a-z,]*exclude[a-z,]*\)(.+)$", t, re.I):
        val = m.group(1)
    elif m := re.match(r"^--exclude=(.+)$", t, re.I):
        val = strip_outer_quotes(m.group(1))
    elif m := re.match(r"^(?:--i?glob|-g)=(.+)$", t, re.I):
        inner = strip_outer_quotes(m.group(1))
        if inner.startswith("!"):
            val = inner[1:]
    return bool(val and SAFE_GLOB_VALUE.match(val))


def check_candidate_piece(piece):
    if not piece:
        return None
    if is_secret_token(piece):
        return piece
    eq_idx = piece.find("=")
    if eq_idx != -1 and is_secret_token(piece[eq_idx + 1:]):
        return piece
    colon_idx = piece.rfind(":")
    if colon_idx > 1 and is_secret_token(piece[colon_idx + 1:]):
        return piece
    if colon_idx == 1 and not re.match(r"^[a-zA-Z]:[\\/]", piece) and is_secret_token(piece[2:]):
        return piece
    return None


def token_hits_secret(raw):
    for part in raw.split(","):
        if check_candidate_piece(part.strip()):
            return part.strip()
    return None


def strip_pure_git_commit_message(cmd):
    if "`" in cmd or "$(" in cmd or "<(" in cmd or ">(" in cmd:
        return cmd
    sanitized = LEX_TOKEN.sub(
        lambda m: "" if m.group(0).startswith("#") else (
            re.sub(r"[\r\n;&|()<>]", " ", m.group(0)) if m.group(0)[0] in ('"', "'") else m.group(0)
        ),
        cmd,
    )
    if "<" in sanitized or ">" in sanitized:
        return cmd
    parts = [p.strip() for p in re.split(r"&&|\|\||[;&|\r\n()]", sanitized) if p.strip()]
    if len(parts) != 1:
        return cmd

    raw_words = WORD_TOKEN.findall(cmd.strip())
    if not raw_words:
        return cmd
    unq = [w.strip("\"'") for w in raw_words]
    if not is_git_command(unq[0]):
        return cmd

    i = 1
    while i < len(unq):
        a = unq[i]
        if a in GIT_OPTIONS_WITH_ARG:
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        break
    if i >= len(unq) or unq[i].lower() != "commit":
        return cmd

    kept = raw_words[:i + 1]
    j = i + 1
    while j < len(raw_words):
        a = unq[j]
        if a == "--":
            kept.extend(raw_words[j:])
            break
        if a in COMMIT_OPTIONS_WITH_ARG:
            kept.append(raw_words[j])
            if j + 1 < len(raw_words):
                kept.append(raw_words[j + 1])
            j += 2
            continue
        if a == "--message" or re.match(r"^-[a-zA-Z]*m$", a):
            j += 2
            continue
        if a.startswith("--message=") or (a.startswith("-m") and len(a) > 2 and not a.startswith("--")):
            j += 1
            continue
        kept.append(raw_words[j])
        j += 1
    return " ".join(kept)


def is_safe_inspect_command(part):
    if "`" in part or "$(" in part or "<" in part or ">(" in part:
        return False
    raw_words = WORD_TOKEN.findall(part.strip())
    if not raw_words:
        return False
    unquoted = [w.strip("\"'").strip() for w in raw_words]
    cmd = re.sub(r"\.exe$", "", re.split(r"[\\/]", unquoted[0])[-1].lower())

    if cmd in ("echo", "write-host", "write-output"):
        return "(" not in part

    if cmd in ("get-childitem", "gci", "dir", "ls"):
        if "(" in part:
            return False
        i = 1
        while i < len(unquoted):
            a = unquoted[i]
            al = a.lower()
            if al == "-exclude":
                i += 2
                continue
            if al.startswith(("-exclude=", "--exclude=")):
                i += 1
                continue
            if not is_self_contained_exclusion(a) and token_hits_secret(a):
                return False
            i += 1
        return True

    if cmd in ("where-object", "where", "?"):
        sub_tokens = [s.lower() for w in unquoted for s in re.split(r"[\s()\[\]{}\"'`,;|<>:.]+", w) if s]
        if any(s in PS_FILE_READERS for s in sub_tokens):
            return False
        for idx, tok in enumerate(unquoted):
            frags = [tok] + [s for s in re.split(r"[\s()\[\]{}\"'`,;|<>]+", tok) if s]
            if any(token_hits_secret(frag) for frag in frags):
                prev = unquoted[idx - 1].lower() if idx > 0 else ""
                if prev not in PS_NEGATIVE_OPS:
                    return False
        return True

    if cmd in ("select-string", "sls"):
        if "(" in part:
            return False
        target_paths = []
        pos_args = []
        saw_pattern = False
        i = 1
        while i < len(unquoted):
            a = unquoted[i]
            al = a.lower()
            if al == "-pattern":
                saw_pattern = True
                i += 2
                continue
            if al.startswith(("-pattern:", "-pattern=")):
                saw_pattern = True
                i += 1
                continue
            if al in ("-path", "-literalpath", "-include"):
                if i + 1 < len(unquoted):
                    val = unquoted[i + 1]
                    target_paths.append(val)
                    i += 2
                    while i < len(unquoted) and (val.endswith(",") or unquoted[i] == "," or unquoted[i].startswith(",")):
                        val = unquoted[i]
                        if val != ",":
                            target_paths.append(val.lstrip(","))
                        elif i + 1 < len(unquoted):
                            i += 1
                            val = unquoted[i]
                            target_paths.append(val)
                        i += 1
                    continue
                i += 2
                continue
            if al.startswith(("-path:", "-path=", "-literalpath:", "-literalpath=", "-include:", "-include=")):
                val = re.split(r"[:=]", a, 1)[1]
                target_paths.append(val)
                i += 1
                while i < len(unquoted) and (val.endswith(",") or unquoted[i] == "," or unquoted[i].startswith(",")):
                    val = unquoted[i]
                    if val != ",":
                        target_paths.append(val.lstrip(","))
                    elif i + 1 < len(unquoted):
                        i += 1
                        val = unquoted[i]
                        target_paths.append(val)
                    i += 1
                continue
            flag_name = re.split(r"[:=]", al, 1)[0]
            if flag_name in SLS_VALUE_FLAGS:
                i += 1 if (":" in al or "=" in al) else 2
                continue
            if a.startswith("-"):
                i += 1
                continue
            pos_args.append(a)
            i += 1
        if not saw_pattern and pos_args:
            pos_args = pos_args[1:]
        target_paths.extend(pos_args)
        return not any(not is_self_contained_exclusion(p) and token_hits_secret(p) for p in target_paths)

    if cmd == "rg":
        if "(" in part:
            return False
        target_paths = []
        pos_args = []
        saw_pattern = False
        past_dd = False
        i = 1
        while i < len(unquoted):
            a = unquoted[i]
            if a == "--":
                past_dd = True
                i += 1
                continue
            if past_dd:
                target_paths.append(a)
                i += 1
                continue
            if a in ("-e", "--regexp") or a.startswith(("-e=", "--regexp=")) or (a.startswith("-e") and not a.startswith("--") and len(a) > 2):
                saw_pattern = True
                i += 2 if a in ("-e", "--regexp") else 1
                continue
            if (a.startswith("-f") and not a.startswith("--") and len(a) > 2 and token_hits_secret(a[2:])) or (
                a.startswith("--file=") and token_hits_secret(a.split("=", 1)[1])
            ):
                return False
            if a in ("-g", "--glob", "--iglob"):
                val = unquoted[i + 1] if i + 1 < len(unquoted) else ""
                if not (val.startswith("!") and SAFE_GLOB_VALUE.match(val[1:])):
                    if token_hits_secret(val):
                        return False
                i += 2
                continue
            if a in RG_VALUE_FLAGS:
                if a in ("-f", "--file") and i + 1 < len(unquoted) and token_hits_secret(unquoted[i + 1]):
                    return False
                i += 2
                continue
            if a.startswith("-"):
                if not is_self_contained_exclusion(a) and token_hits_secret(a):
                    return False
                i += 1
                continue
            pos_args.append(a)
            i += 1
        if not saw_pattern and pos_args:
            pos_args = pos_args[1:]
        target_paths.extend(pos_args)
        return not any(not is_self_contained_exclusion(p) and token_hits_secret(p) for p in target_paths)

    if cmd == "git":
        i = 1
        while i < len(unquoted):
            a = unquoted[i]
            if a in GIT_OPTIONS_WITH_ARG:
                i += 2
                continue
            if a.startswith("-"):
                i += 1
                continue
            break
        if i >= len(unquoted):
            return False
        sub = unquoted[i].lower()
        if sub == "log" and not any(re.match(r"^(?:-p|-u|-L|--patch|--unified)", a, re.I) for a in unquoted):
            return True
        if sub in ("check-ignore", "status", "ls-files"):
            return True
        if sub == "rm" and "--cached" in unquoted:
            return True
        if sub == "grep":
            pos_args, pathspecs = [], []
            past_dd = False
            for a in unquoted[i + 1:]:
                if a == "--":
                    past_dd = True
                elif past_dd:
                    pathspecs.append(a)
                elif not a.startswith("-"):
                    pos_args.append(a)
            if pos_args:
                targets = pos_args[1:] + pathspecs
                return not any(not is_self_contained_exclusion(p) and token_hits_secret(p) for p in targets)

    if cmd == "findstr":
        has_explicit_pattern = False
        non_flags = []
        i = 1
        while i < len(unquoted):
            a = unquoted[i]
            al = a.lower()
            if al.startswith(("/g:", "/f:")):
                if token_hits_secret(a[3:]):
                    return False
                if al.startswith("/g:"):
                    has_explicit_pattern = True
                i += 1
                continue
            if al in ("/g", "/f"):
                if i + 1 < len(unquoted) and token_hits_secret(unquoted[i + 1]):
                    return False
                if al == "/g":
                    has_explicit_pattern = True
                i += 2
                continue
            if al.startswith("/c:"):
                has_explicit_pattern = True
                i += 1
                continue
            if al == "/c":
                has_explicit_pattern = True
                i += 2
                continue
            if a.startswith("/"):
                i += 1
                continue
            non_flags.append(a)
            i += 1
        if has_explicit_pattern:
            return len(non_flags) >= 1 and not any(token_hits_secret(f) for f in non_flags)
        if len(non_flags) >= 2:
            return not any(token_hits_secret(f) for f in non_flags[1:])

    return False


def find_secret_in_command(cmd):
    """Return the matched secret token if cmd attempts to read a project secret file, else None."""
    effective = strip_pure_git_commit_message(cmd)
    effective = LEX_TOKEN.sub(lambda m: "" if m.group(0).startswith("#") else m.group(0), effective)
    for part in re.split(r"&&|\|\||[;&|\r\n]", effective):
        if is_safe_inspect_command(part):
            continue
        words = WORD_TOKEN.findall(part.strip())
        if not words:
            continue
        for raw_word in words:
            if is_self_contained_exclusion(raw_word):
                continue
            unquoted = raw_word.strip("\"'` ")
            hit = token_hits_secret(unquoted)
            if hit:
                return hit
            for sub in re.split(r"[\s()\[\]{}\"'`,;|<>]+", unquoted):
                hit = check_candidate_piece(sub)
                if hit:
                    return hit
    return None


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

    for part in re.split(r"&&|\|\||[;&|\r\n()]", sanitize_for_split(cmd)):
        words = [w for w in WORD_TOKEN.findall(part.strip()) if w.strip("\"'")]
        if is_dangerous_part(words):
            deny(REASON_GIT)

    if find_secret_in_command(cmd):
        deny(REASON_SECRET)

    print("{}")


if __name__ == "__main__":
    main()
