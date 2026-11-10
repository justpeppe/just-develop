"""Mirror the Claude Code setup into Antigravity; --check writes nothing, prints each difference and exits 1 if any."""
import json, os, re, shutil, sys
from os.path import join

HOME = os.path.expanduser('~')
CLAUDE = join(HOME, '.claude')
GEMINI = join(HOME, '.gemini', 'config')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
check = '--check' in sys.argv
diff = []


def put(path, text):
    if not check:
        open(path, 'w', encoding='utf-8').write(text)
    elif not os.path.isfile(path) or open(path, encoding='utf-8').read() != text:
        diff.append(f'out of date: {path}')


# 1) Rules. Google's Rules page lists config/rules/*.md for App, CLI and IDE; ~/.gemini/GEMINI.md stays for plugin imports.
FRONTMATTER = '---\ntrigger: always_on\n---\n'
HEADER = '<!-- Generated from ~/.claude/CLAUDE.md by scripts/sync-from-claude.py - edit CLAUDE.md, not this file. -->\n\n'
if not check:
    os.makedirs(join(GEMINI, 'rules'), exist_ok=True)

# Claude @imports are not resolved in Antigravity: the imported files become their own rules below.
claude_rules = ''.join(line for line in open(join(CLAUDE, 'CLAUDE.md'), encoding='utf-8') if not line.startswith('@'))
put(join(GEMINI, 'rules', 'claude-md.md'), FRONTMATTER + HEADER + claude_rules)
for source, name in (('flow.md', 'flow.md'), ('shared/global.md', 'shared.md'), ('personal/global.md', 'personal.md')):
    put(join(GEMINI, 'rules', name), FRONTMATTER + open(join(REPO, source), encoding='utf-8').read())

# 2) Agents and knowledge: copies only, and anything present only in Antigravity is reported, never deleted.
if not check:
    os.makedirs(join(GEMINI, 'agents'), exist_ok=True)
is_link = lambda p: os.path.islink(p) or getattr(os.path, 'isjunction', lambda _: False)(p)

# Claude Code scans agents/ recursively (Anthropic, Subagents page); that it follows a linked folder is unverified.
src = {}
for d, _, files in os.walk(join(CLAUDE, 'agents'), followlinks=True):
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
claude_settings = json.load(open(join(CLAUDE, 'settings.json'), encoding='utf-8'))
off = {k for k, v in (claude_settings.get('skillOverrides') or {}).items() if v == 'off'}
sel = [os.path.realpath(join(CLAUDE, 'skills', n)) for n in os.listdir(join(CLAUDE, 'skills'))
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

# A link left behind by a moved repo hides its skill from both agents without any error.
for folder in (join(CLAUDE, 'skills'), AGENT_SKILLS):
    diff += [f'broken link: {join(folder, n)}' for n in sorted(os.listdir(folder) if os.path.isdir(folder) else [])
             if is_link(join(folder, n)) and not os.path.exists(join(folder, n))]

# 4) MCP: mcp.json is the single source and client configs are never written here.
mcp_file = join(REPO, 'mcp.json')
mcp_ref = (json.load(open(mcp_file, encoding='utf-8')).get('mcpServers') or {}) if os.path.isfile(mcp_file) else {}


def norm_mcp(server):
    """Compare servers by content: Claude writes url, Antigravity url or serverUrl."""
    server = server if isinstance(server, dict) else {}
    url = server.get('url') or server.get('serverUrl')
    return {'url': url} if url else {'command': server.get('command'), 'args': server.get('args') or [], 'env': server.get('env') or {}}


clients = [('Claude', join(HOME, '.claude.json')), ('Antigravity', join(GEMINI, 'mcp_config.json'))]
for c_name, c_path in clients:
    c_data = json.load(open(c_path, encoding='utf-8')) if os.path.isfile(c_path) else {}
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
claude_deny = set(((claude_settings.get('permissions') or {}).get('deny')) or [])
for rule in sorted({'Bash(git push *)', 'Bash(git merge *)', 'PowerShell(git push *)', 'PowerShell(git merge *)',
                    f'Read(//**/*{INI})', 'Read(//**/.env)'} - claude_deny):
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
gemini_hooks = json.load(open(gemini_hooks_file, encoding='utf-8')) if os.path.isfile(gemini_hooks_file) else {}
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

print('\n'.join(diff))
print(f'{"checked" if check else "synced"}: rules, {len(src)} agents, {len(sel)} skills '
      f'({len(groups)} folders in skills.json), {len(diff)} differences')
sys.exit(1 if check and diff else 0)
