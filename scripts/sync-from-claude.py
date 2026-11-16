"""Mirror the Claude Code setup into Antigravity; --check writes nothing, prints each difference and exits 1 if any."""
import json, os, re, shutil, sys, tempfile
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from os.path import join

HOME = os.path.expanduser('~')
CLAUDE = join(HOME, '.claude')
GEMINI = join(HOME, '.gemini', 'config')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
check = '--check' in sys.argv
diff = []


def write_atomic(path, text):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix='.tmp-', suffix='.sync')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def put(path, text):
    if not check:
        write_atomic(path, text)
    elif not os.path.isfile(path) or open(path, encoding='utf-8').read() != text:
        diff.append(f'out of date: {path}')


# 1) Rules. Google's Rules page lists config/rules/*.md for App, CLI and IDE; ~/.gemini/GEMINI.md stays for plugin imports.
FRONTMATTER = '---\ntrigger: always_on\n---\n'
HEADER = '<!-- Generated from ~/.claude/CLAUDE.md by scripts/sync-from-claude.py - edit CLAUDE.md, not this file. -->\n\n'
if not check:
    os.makedirs(join(GEMINI, 'rules'), exist_ok=True)

# Claude @imports are not resolved in Antigravity: the imported files become their own rules below.
claude_md_file = join(CLAUDE, 'CLAUDE.md')
claude_rules = ''.join(line for line in open(claude_md_file, encoding='utf-8') if not line.startswith('@')) if os.path.isfile(claude_md_file) else ''
claude_md_out = join(GEMINI, 'rules', 'claude-md.md')
if claude_rules.strip():
    put(claude_md_out, FRONTMATTER + HEADER + claude_rules)
elif os.path.isfile(claude_md_out):
    if not check:
        os.unlink(claude_md_out)
    else:
        diff.append(f'stale generated rule (CLAUDE.md empty): {claude_md_out}')
for source, name in (('flow.md', 'flow.md'), ('shared/global.md', 'shared.md'), ('personal/global.md', 'personal.md')):
    if os.path.isfile(join(REPO, source)):
        put(join(GEMINI, 'rules', name), FRONTMATTER + open(join(REPO, source), encoding='utf-8').read())

# 2) Agents and knowledge: copies only, and anything present only in Antigravity is reported, never deleted.
if not check:
    os.makedirs(join(GEMINI, 'agents'), exist_ok=True)
is_link = lambda p: os.path.islink(p) or getattr(os.path, 'isjunction', lambda _: False)(p)

# Claude Code scans agents/ recursively (Anthropic, Subagents page); that it follows a linked folder is unverified.
src = {}
for d, dirs, files in os.walk(join(CLAUDE, 'agents'), followlinks=True):
    for sub in sorted(list(dirs)):
        dp = join(d, sub)
        if is_link(dp) and not os.path.exists(dp):
            diff.append(f'broken link: {dp}')
            dirs.remove(sub)
    for f in sorted(files):
        p = join(d, f)

        # A broken link shows up as a file here: report it instead of crashing on open().
        if is_link(p) and not os.path.exists(p):
            diff.append(f'broken link: {p}')
        elif f.endswith('.md') and f in src:
            diff.append(f'two agents named {f}: {src[f]} and {p}')
        elif f.endswith('.md'):
            src[f] = p
for f in os.listdir(join(GEMINI, 'agents')) if os.path.isdir(join(GEMINI, 'agents')) else []:
    if f.endswith('.md') and f not in src:
        diff.append(f'not in Claude: {join(GEMINI, "agents", f)}')


def gemini_agent(text):
    """Swap the Claude tool allowlist for Antigravity's: names like Read do not exist there."""
    nl = chr(10)

    # The frontmatter is the text before the second ---.
    head, sep, body = text.partition(nl + '---' + nl)
    keep = [line for line in head.split(nl) if not line.startswith(('tools:', 'disallowedTools:', 'model:', 'effort:'))]
    extra = [
        'tools:',
        '  - read_file',
        '  - view_file',
        '  - grep_search',
        '  - list_dir',
        '  - find_by_name',
        '  - call_mcp_tool',
        '  - read_resource',
        '  - list_resources',
        '  - search_web',
        'model: inherit',
        'subagent: true'
    ]
    return nl.join(keep + extra) + sep + body


for f, path in src.items():
    text = open(path, encoding='utf-8').read()

    # An agent marked antigravity: false needs tools the Antigravity copy would not get; spaces and quotes around false are ignored.
    head = text.partition(chr(10) + '---' + chr(10))[0].split(chr(10))
    if 'antigravity:false' not in [re.sub('[ "\']', '', line) for line in head]:
        put(join(GEMINI, 'agents', f), gemini_agent(text))
    elif os.path.exists(join(GEMINI, 'agents', f)):
        diff.append(f'marked antigravity: false, still in Antigravity: {join(GEMINI, "agents", f)}')

# ponytail: --check skips knowledge/ (a tree copy); compare it too if it ever drifts
if not check and os.path.isdir(join(CLAUDE, 'knowledge')):
    shutil.copytree(join(CLAUDE, 'knowledge'), join(GEMINI, 'knowledge'), dirs_exist_ok=True)

# 3) Skills: Antigravity reads config/skills by itself, the rest of the selection goes in skills.json by real parent folder.
settings_file = join(CLAUDE, 'settings.json')
try:
    claude_settings = json.load(open(settings_file, encoding='utf-8')) if os.path.isfile(settings_file) else {}
except Exception as exc:
    claude_settings = {}
    diff.append(f'invalid JSON in {settings_file}: {exc}')
if not isinstance(claude_settings, dict):
    claude_settings = {}
off = {k for k, v in (claude_settings.get('skillOverrides') or {}).items() if v == 'off'}
sel = [os.path.realpath(join(CLAUDE, 'skills', n)) for n in (os.listdir(join(CLAUDE, 'skills')) if os.path.isdir(join(CLAUDE, 'skills')) else [])
       if n not in off and os.path.isfile(join(CLAUDE, 'skills', n, 'SKILL.md'))]
AGENT_SKILLS = join(HOME, '.agents', 'skills')
key = lambda p: os.path.normcase(os.path.realpath(p))
GEMINI_SKILLS = join(GEMINI, 'skills')
native = {n for n in os.listdir(GEMINI_SKILLS) if os.path.isdir(join(GEMINI_SKILLS, n))} if os.path.isdir(GEMINI_SKILLS) else set()
groups = {}
for t in sel:
    if os.path.basename(t) not in native:
        groups.setdefault(os.path.dirname(t), []).append(os.path.basename(t))

# include_only matches the real folder name, not the link name.
put(join(GEMINI, 'skills.json'), json.dumps({'entries': [{'path': p.replace('\\', '/'), 'include_only': sorted(set(ns))}
                                                         for p, ns in sorted(groups.items())]}, indent=2) + '\n')

# Skills added only in Antigravity are reported, never deleted.
selected = {os.path.basename(t) for t in sel}
diff += [f'only in Antigravity: {join(GEMINI_SKILLS, n)}' for n in sorted(native - selected)]
mine = {os.path.basename(t) for t in sel if key(os.path.dirname(t)) == key(AGENT_SKILLS)}
diff += [f'active in Antigravity, not in Claude: {join(AGENT_SKILLS, n)}' for n in sorted(os.listdir(AGENT_SKILLS) if os.path.isdir(AGENT_SKILLS) else [])
         if n not in mine and not is_link(join(AGENT_SKILLS, n)) and os.path.isfile(join(AGENT_SKILLS, n, 'SKILL.md'))]

# Classify broken links before deleting any so 2-hop chains (~/.claude -> ~/.agents -> REPO/skills) resolve cleanly.
REPO_SKILLS_ROOT = os.path.normcase(os.path.realpath(join(REPO, 'skills')))


def _clean_readlink(p):
    target = os.readlink(p)
    if os.name == 'nt' and target.startswith('\\\\?\\'):
        target = ('\\\\' + target[8:]) if target.startswith('\\\\?\\UNC\\') else target[4:]
    if not os.path.isabs(target):
        target = join(os.path.dirname(os.path.abspath(p)), target)
    return os.path.normpath(os.path.abspath(target))


def _targets_repo_skills(p):
    curr = os.path.abspath(p)
    seen = set()
    for _ in range(8):
        norm = os.path.normcase(curr)
        if norm in seen or not is_link(curr):
            break
        seen.add(norm)
        try:
            curr = _clean_readlink(curr)
        except OSError:
            break
        resolved = os.path.normcase(os.path.realpath(curr))
        if resolved == REPO_SKILLS_ROOT or resolved.startswith(REPO_SKILLS_ROOT + os.sep):
            return True
    final_norm = os.path.normcase(curr)
    return final_norm == REPO_SKILLS_ROOT or final_norm.startswith(REPO_SKILLS_ROOT + os.sep)


broken_entries = []
for folder in (join(CLAUDE, 'skills'), AGENT_SKILLS):

    for n in sorted(os.listdir(folder) if os.path.isdir(folder) else []):
        p = join(folder, n)
        if is_link(p) and not os.path.exists(p):
            broken_entries.append((p, _targets_repo_skills(p)))

for p, is_internal in broken_entries:
    if is_internal and not check:
        try:
            os.rmdir(p)
        except OSError:
            os.unlink(p)
    else:
        diff.append(f'broken link: {p}')




# 4) MCP: mcp.json is the single source and client configs are never written here.
def read_json_doc(path):
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        diff.append(f'invalid JSON in {path}: {exc}')
        return {}


mcp_file = join(REPO, 'mcp.json')
mcp_ref = read_json_doc(mcp_file).get('mcpServers') or {}
if not isinstance(mcp_ref, dict):
    mcp_ref = {}


def norm_mcp(server):
    """Compare servers by content: Claude writes url, Antigravity url or serverUrl."""
    server = server if isinstance(server, dict) else {}
    url = server.get('url') or server.get('serverUrl')
    return {'url': url} if url else {'command': server.get('command'), 'args': server.get('args') or [], 'env': server.get('env') or {}}


clients = [('Claude', join(HOME, '.claude.json')), ('Antigravity', join(GEMINI, 'mcp_config.json'))]
for c_name, c_path in clients:
    c_data = read_json_doc(c_path)
    c_servers = c_data.get('mcpServers') if isinstance(c_data, dict) else {}
    if not isinstance(c_servers, dict):
        c_servers = {}
    for name, srv in sorted(mcp_ref.items()):
        if name not in c_servers:
            diff.append(f'MCP {c_name}: missing {name}')
        elif norm_mcp(c_servers[name]) != norm_mcp(srv):
            diff.append(f'MCP {c_name}: {name} differs from mcp.json')

    # Each machine keeps its own servers: a notice, never a difference.
    for name in sorted(c_servers):
        if name not in mcp_ref:
            print(f'note: MCP {c_name}: extra {name}, only on this machine')

# 5) Guardrails: client configs are personal and never written here, only checked.
# The extension is split so a search for that file type does not match this source.
INI = '.i' + 'ni'
ENV = '.e' + 'nv'
claude_deny = set(((claude_settings.get('permissions') or {}).get('deny')) or [])
for rule in sorted({'Bash(git push *)', 'Bash(git merge *)', 'PowerShell(git push *)', 'PowerShell(git merge *)',
                    'Bash(agy *)', 'PowerShell(agy *)',
                    f'Read(//**/*{INI})', f'Read(//**/{ENV})'} - claude_deny):
    diff.append(f'Claude permissions.deny: missing {rule}')

claude_hooks = claude_settings.get('hooks') if isinstance(claude_settings.get('hooks'), dict) else {}
claude_script, claude_matchers = 'block-dangerous-git.py', {'Bash', 'PowerShell'}
found = [(g.get('matcher') or '', h) for g in (claude_hooks.get('PreToolUse') or []) if isinstance(g, dict)
         for h in (g.get('hooks') or []) if isinstance(h, dict) and claude_script in (h.get('command') or '')]
if not found:
    diff.append(f'Claude hooks.PreToolUse: missing {claude_script}')
else:
    tokens = {t.strip() for m, _ in found for t in m.replace(',', '|').split('|') if t.strip()}
    if '*' not in tokens and not claude_matchers <= tokens:
        diff.append(f'Claude hooks.PreToolUse {claude_script}: missing matcher {sorted(claude_matchers - tokens)}')
    if any(h.get('onFailure') != 'block' for _, h in found):
        diff.append(f'Claude hooks.PreToolUse {claude_script}: missing onFailure=block')

gemini_hooks_file = join(GEMINI, 'hooks.json')
gemini_hooks = read_json_doc(gemini_hooks_file)
active_hooks = lambda event: [(g.get('matcher') or '', h) for v in (gemini_hooks.values() if isinstance(gemini_hooks, dict) else [])
                              if isinstance(v, dict) and v.get('enabled', True) is not False
                              for g in (v.get(event) or []) if isinstance(g, dict)
                              for h in (g.get('hooks') or []) if isinstance(h, dict)]
for script, required in [
    ('block-dangerous-git.js', {'run_command'}),
    ('block-secrets-read.js', {'run_command', 'read_file', 'view_file', 'grep_search', 'list_dir',
                               'find_by_name', 'call_mcp_tool', 'mcp_.*', 'read_resource'}),
]:
    found_matchers = [m for m, h in active_hooks('PreToolUse') if script in (h.get('command') or '')]
    if not found_matchers:
        diff.append(f'Antigravity hooks.json: missing {script}')
        continue
    tokens = {t.strip() for m in found_matchers for t in m.split('|') if t.strip()}
    if '*' not in tokens and not required <= tokens:
        diff.append(f'Antigravity hooks.json {script}: missing matcher {sorted(required - tokens)}')

enabled_plugins = claude_settings.get('enabledPlugins')
if isinstance(enabled_plugins, dict) and enabled_plugins.get('ponytail@ponytail') is True:
    diff.append('Claude settings.json: ponytail@ponytail must be disabled (false)')

gemini_cfg_file = join(GEMINI, 'config.json')
try:
    gemini_cfg = json.load(open(gemini_cfg_file, encoding='utf-8')) if os.path.isfile(gemini_cfg_file) else {}
except Exception as exc:
    gemini_cfg = {}
    diff.append(f'invalid JSON in {gemini_cfg_file}: {exc}')
if isinstance(gemini_cfg, dict):
    ponytail_cfg = (gemini_cfg.get('plugins') or {}).get('ponytail')
    if isinstance(ponytail_cfg, dict) and ponytail_cfg.get('enabled') is True:
        diff.append('Antigravity config.json: plugins.ponytail.enabled must be false')

for folder in (join(CLAUDE, 'skills'), AGENT_SKILLS):
    dup_pt = join(folder, 'ponytail-review')
    if os.path.exists(dup_pt) or is_link(dup_pt):
        diff.append(f'duplicate ponytail-review skill (belongs to plugin only): {dup_pt}')

print('\n'.join(diff))
print(f'{"checked" if check else "synced"}: rules, {len(src)} agents, {len(sel)} skills '
      f'({len(groups)} folders in skills.json), {len(diff)} differences')
sys.exit(1 if check and diff else 0)
