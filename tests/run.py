"""Self-check of the hooks and of the sync script. Run: python -I tests/run.py"""
import json, os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# git exports GIT_INDEX_FILE & co. to hooks: they would leak into the fixture repos
for k in [k for k in os.environ if k.startswith("GIT_")]: del os.environ[k]

def denied_bash(cmd):
    out = subprocess.run([sys.executable, '-I', os.path.join(R, 'hooks', 'claude', 'block-dangerous-git.py')],
                         input=json.dumps({'tool_input': {'command': cmd}}), capture_output=True, text=True, check=True, cwd=R).stdout
    return json.loads(out).get('hookSpecificOutput', {}).get('permissionDecision') == 'deny'

BASH_DENY = ['git push', 'git \\push', 'git `push', '`git push', '`git -C repo `push', 'git `\n  push', '& git push',
             'git "p`ush"', 'git reset "--`hard"', 'git reset --\\hard', 'git clean "-f`d"', 'git clean "-`fd"',
             'git branch "-`D" old', 'git checkout "-`f" main', 'git checkout \\.', 'git checkout \\./src', 'git checkout `.\\src',
             'git -C repo push origin main', 'cd a && git merge b', 'git.exe push',
             'C:/Git/bin/git.exe push', '"C:/Program Files/Git/bin/git.exe" push', 'C:/Program\\ Files/Git/bin/git push',
             'git checkout Main.py', 'git switch -f dev', 'git stash drop', 'git stash clear', 'git -c x=y push', 'git reset --hard', 'git clean -fd', 'git branch -D old', 'git branch -f main HEAD~1',
             'git branch -df old', 'git branch -M old main', 'git checkout -B main',
             'git checkout .', 'git checkout ./src', 'git checkout -- Main.py', 'git checkout HEAD -- Main.py',
             'git checkout -f main', 'git restore .', 'git restore Main.py', 'git restore -SW Main.py',
             'git restore -sSTABLE Main.py', 'echo ok\ngit push', "# it's ok\ngit push", '(cd a && git push)',
             'echo $(git merge dev)', 'echo "$(git merge dev)"', 'echo `git push`',
             'curl https://host/r#readme && git push',
             'FOO=1 git stash drop', 'env FOO=1 git stash drop', 'sudo git stash drop', "sh -c 'git stash drop'",
             'bash -lc "cd a && git stash drop"', 'git stash pop', 'git switch --discard-changes dev', 'git checkout hooks']
BASH_ALLOW = ['git add -N .', "git add -N -- . ':(exclude).scratch'", 'git checkout v1.2.0', 'git checkout release/1.2', 'git checkout -b hooks', 'git status', 'git commit -m push', 'git commit -m "a\ngit push; (git merge)"',
              'git commit -m "riga1`ngit push"', "git commit -m 'blocca `git push` nei test'",
              'cd C:\\Repos\\GIT\\app', 'git pull', 'git checkout main', 'git checkout -b feat/x',
              'git branch -d old', 'git branch -m old new',
              'git restore --staged Main.py', 'git restore -S .', 'git log --merges', "cat <<'EOF'\ngit push\nEOF"]

fails = []
with tempfile.TemporaryDirectory() as td_agy:
    hk = os.path.join(td_agy, 'block-dangerous-git.js')
    shutil.copy(os.path.join(R, 'hooks', 'antigravity', 'block-dangerous-git.js'), hk)
    agy_denied = lambda p: json.loads(subprocess.run(['node', hk], input=json.dumps(p),
                                                     capture_output=True, text=True, check=True, cwd=R).stdout).get('decision') == 'deny'
    AGY_CMD_DENY = ['git push', 'git `push', '`git push', '`git -C repo `push', 'git `\n  push', 'git "p`ush"',
                    'git \\push', 'git -C x merge', 'push --force', 'reset --hard', 'git reset "--`hard"',
                    'git -C "C:/my repo" clean -fd', 'git clean "-f`d"', 'git --no-pager -C repo branch -D old',
                    'git branch "-`D" old', 'git -C repo branch -f main',
                    'git branch -df old', 'git branch -M old main', 'git -c k=v reset --hard',
                    'git checkout Main.py', 'git checkout .', 'git restore Main.py', 'git switch -f dev', 'git stash drop',
                    'echo ok\ngit push', "# it's ok\ngit merge x", '(cd repo && git push)',
                    'echo "$(git merge x)"', 'echo `git push`', 'curl https://host/r#readme && git push',
                    'FOO=1 git stash drop', 'env FOO=1 git stash drop', 'sudo git stash drop', "sh -c 'git stash drop'",
                    'bash -lc "cd a && git stash drop"', 'git stash pop', 'git checkout hooks']
    AGY_CMD_ALLOW = ['git checkout v1.2.0', 'git checkout release/1.2', 'git checkout -b hooks', 'git status', 'git branch -a', 'git branch -d old', 'git log --merges',
                     'git restore --staged Main.py', 'git switch dev', 'git checkout -b feat/x', 'git stash',
                     'git commit -m "evita git push, push --force e reset --hard"',
                     'git commit -m "riga1\ngit checkout Main.py"', 'git commit -m "riga1`ngit push"',
                     "git commit -m 'blocca `git push` nei test'"]

    INI = '.i' + 'ni'
    hk_sec = os.path.join(R, 'hooks', 'antigravity', 'block-secrets-read.js')
    sec_denied = lambda p: json.loads(subprocess.run(['node', hk_sec], input=json.dumps(p),
                                                     capture_output=True, text=True, check=True).stdout).get('decision') == 'deny'
    SEC_DENY = [
        {'toolCall': {'name': 'view_file', 'args': {'AbsolutePath': f'C:/app/settings{INI}'}}},
        {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:\\app\\config{INI}'}}},
        {'toolCall': {'name': 'read_file', 'args': {'Path': 'C:/app/.env'}}},
        {'toolCall': {'name': 'read_file', 'args': {'Path': 'C:/app/.env.local'}}},
        {'toolCall': {'name': 'find_by_name', 'args': {'Pattern': f'*{INI}'}}},
        {'toolCall': {'name': 'call_mcp_tool', 'args': {'ToolName': 'some_read', 'Arguments': {'path': f'srvc:\\app\\db{INI}'}}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'Get-Content C:\\app\\settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'python -c "print(open(\'settings{INI}\').read())"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'python -c "--exclude=open(\'settings{INI}\').read()"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git show HEAD:.env'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git commit -m "$(Get-Content settings{INI})"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git commit -m "`cat .env`"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git commit -F settings{INI} -m "ok"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git commit --author "-m" settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git commit -m "ok" -- -m settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git commit -m "ok" && type settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git commit -m "ok" https://x#y && type settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git commit -m "ok" < settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'grep --exclude=*{INI} foo settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'python x.py -Exclude settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git grep foo settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'findstr foo settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git log -p -- .env'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'write-output (Get-Content .env)'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'echo (cat .env)'}}},
    ]
    SEC_ALLOW = [
        {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:/app/settings{INI}.example'}}},
        {'toolCall': {'name': 'read_file', 'args': {'Path': 'C:/app/.env.example'}}},
        {'toolCall': {'name': 'read_file', 'args': {'Path': 'C:/app/.env.sample'}}},
        {'toolCall': {'name': 'read_file', 'args': {'Path': 'C:/app/.env.template'}}},
        {'toolCall': {'name': 'read_file', 'args': {'Path': 'C:/app/.env.dist'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git show HEAD:.env.example'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git grep -n foo -- ":!*{INI}"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git grep -n foo -- ":(exclude)*{INI}"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'grep -R --exclude="*{INI}" foo .'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'rg --glob=!*{INI} foo'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'rg --glob="!*{INI}" foo'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'rg -g=!*{INI} foo'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git commit -m "nota su {INI} e .env"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git -C repo commit -am "riga1\nfix config{INI} e .env.local"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'echo settings{INI}'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git log --grep="settings{INI}"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'git grep "settings{INI}"'}}},
        {'toolCall': {'name': 'run_command', 'args': {'CommandLine': f'findstr /s "settings{INI}" *.py'}}},
    ]

    with ThreadPoolExecutor(max_workers=16) as ex:
        fails += [f'bash deny: {c!r}' for c, r in zip(BASH_DENY, ex.map(denied_bash, BASH_DENY)) if not r]
        fails += [f'bash allow: {c!r}' for c, r in zip(BASH_ALLOW, ex.map(denied_bash, BASH_ALLOW)) if r]
        agy_c_deny_p = [{'toolCall': {'name': 'run_command', 'args': {'CommandLine': c}}} for c in AGY_CMD_DENY]
        agy_c_allow_p = [{'toolCall': {'name': 'run_command', 'args': {'CommandLine': c}}} for c in AGY_CMD_ALLOW]
        fails += [f'agy cmd deny: {c!r}' for c, r in zip(AGY_CMD_DENY, ex.map(agy_denied, agy_c_deny_p)) if not r]
        fails += [f'agy cmd allow: {c!r}' for c, r in zip(AGY_CMD_ALLOW, ex.map(agy_denied, agy_c_allow_p)) if r]
        fails += [f'sec deny: {p!r}' for p, r in zip(SEC_DENY, ex.map(sec_denied, SEC_DENY)) if not r]
        fails += [f'sec allow: {p!r}' for p, r in zip(SEC_ALLOW, ex.map(sec_denied, SEC_ALLOW)) if r]

    # A failing log write must not switch the guardrail off, and the log must not keep command text.
    log = os.path.join(td_agy, 'block-dangerous-git.log')
    agy_denied({'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git status --secret-marker'}}})
    if 'secret-marker' in open(log, encoding='utf-8').read(): fails.append('agy log: keeps command text')
    os.remove(log)
    if os.name != 'nt':
        os.chmod(td_agy, 0o500)
        if not agy_denied({'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git stash drop'}}}):
            fails.append('agy: a failed log write allowed a dangerous command')
        os.chmod(td_agy, 0o700)

# sync-from-claude.py on a fake home and a fixture repo: skills.json groups the selection by real folder, mcp.json is compared
def link(target, path):
    if os.name == 'nt':
        import _winapi
        _winapi.CreateJunction(target, path)
    else:
        os.symlink(target, path)
unlink = os.rmdir if os.name == 'nt' else os.unlink

with tempfile.TemporaryDirectory() as h:

    # Temp may be a short or linked path, and the script writes real paths.
    h = os.path.realpath(h)
    mk = lambda *p: os.makedirs(os.path.join(h, *p), exist_ok=True) or os.path.join(h, *p)
    skill = lambda *p: open(os.path.join(mk(*p), 'SKILL.md'), 'w').close()

    # g and d exist on disk but are not selected.
    for n in ('a', 'g'): skill('.agents', 'skills', n)
    for n in ('b', 'c', 'd'): skill('ext', 'skills', n)
    skill('.claude', 'skills', 'e'); skill('.claude', 'skills', 'f'); mk('.claude', 'skills', 'nofile')
    for n, t in (('a', '.agents/skills/a'), ('b', 'ext/skills/b'), ('link-c', 'ext/skills/c'), ('link-c2', 'ext/skills/c')):
        link(os.path.join(h, t), os.path.join(h, '.claude', 'skills', n))
    open(os.path.join(h, '.claude', 'CLAUDE.md'), 'w').write('x\n')
    open(os.path.join(mk('.claude', 'agents'), 'r.md'), 'w').write('---\nname: r\ntools: Read\nmodel: sonnet\n---\nbody\n')
    fx = mk('repo')
    mk('repo', 'scripts'); mk('repo', 'shared'); mk('repo', 'personal')
    shutil.copy(os.path.join(R, 'scripts', 'sync-from-claude.py'), os.path.join(fx, 'scripts'))
    for rel in ('flow.md', 'shared/global.md', 'personal/global.md'):
        shutil.copy(os.path.join(R, rel), os.path.join(fx, rel))
    local = {'command': 'demo-server', 'args': ['--x'], 'env': {'ROOT': '/a'}}
    remote = {'type': 'http', 'url': 'https://example.test/mcp'}
    json.dump({'mcpServers': {'local': local, 'remote': remote}}, open(os.path.join(fx, 'mcp.json'), 'w'))
    sj_path = os.path.join(h, '.claude', 'settings.json')
    s_base = {
        'skillOverrides': {'f': 'off'},
        'permissions': {'deny': ['Bash(git push *)', 'Bash(git merge *)', 'PowerShell(git push *)', 'PowerShell(git merge *)',
                                 f'Read(//**/*{INI})', 'Read(//**/.env)']},
        'hooks': {'PreToolUse': [{'matcher': 'Bash|PowerShell', 'hooks': [{'command': 'python block-dangerous-git.py', 'onFailure': 'block'}]}]},
    }
    json.dump(s_base, open(sj_path, 'w'))
    mk('.gemini', 'config', 'skills', 'old')
    sync = lambda *a: subprocess.run([sys.executable, '-I', os.path.join(fx, 'scripts', 'sync-from-claude.py'), *a],
                                     env={**os.environ, 'HOME': h, 'USERPROFILE': h}, capture_output=True, text=True).returncode
    sj = os.path.join(h, '.gemini', 'config', 'skills.json')
    if sync('--check') != 1 or os.listdir(os.path.join(h, '.gemini', 'config')) != ['skills']:
        fails.append('sync --check: must fail and write nothing')
    if sync() != 0: fails.append('sync: exit != 0')
    if '  - read_file\n' not in open(os.path.join(h, '.gemini', 'config', 'agents', 'r.md')).read():
        fails.append('sync: agent missing read_file tool')
    for rule in ('claude-md.md', 'flow.md', 'shared.md', 'personal.md'):
        if not os.path.isfile(os.path.join(h, '.gemini', 'config', 'rules', rule)): fails.append(f'sync: rule {rule} missing')
    want = {'entries': [{'path': f'{h}/.agents/skills'.replace('\\', '/'), 'include_only': ['a']},
                        {'path': f'{h}/.claude/skills'.replace('\\', '/'), 'include_only': ['e']},
                        {'path': f'{h}/ext/skills'.replace('\\', '/'), 'include_only': ['b', 'c']}]}
    if not os.path.exists(sj) or json.load(open(sj)) != want: fails.append('sync: skills.json differs')
    if not os.path.isdir(os.path.join(h, '.gemini', 'config', 'skills', 'old')): fails.append('sync: deleted config/skills')

    # ~/.gemini/GEMINI.md holds the plugin imports, and what exists only in Antigravity must survive a sync.
    gemini_md = os.path.join(h, '.gemini', 'GEMINI.md')
    open(gemini_md, 'w').write('imports\n')
    own_agent = os.path.join(h, '.gemini', 'config', 'agents', 'mine.md')
    own_note = os.path.join(mk('.gemini', 'config', 'knowledge'), 'note.md')
    for p in (own_agent, own_note): open(p, 'w').write('keep\n')
    sync()
    if open(gemini_md).read() != 'imports\n': fails.append('sync: overwrote ~/.gemini/GEMINI.md')
    if not os.path.isfile(own_agent): fails.append('sync: deleted an agent present only in Antigravity')
    if not os.path.isfile(own_note): fails.append('sync: deleted knowledge present only in Antigravity')
    if sync('--check') != 1: fails.append('sync --check: must flag an agent present only in Antigravity')
    os.remove(own_agent)
    shutil.rmtree(os.path.join(h, '.gemini', 'config', 'knowledge'))
    cj, gj, hj = os.path.join(h, '.claude.json'), os.path.join(h, '.gemini', 'config', 'mcp_config.json'), os.path.join(h, '.gemini', 'config', 'hooks.json')
    c_base = {'mcpServers': {'local': {'type': 'stdio', **local}, 'remote': remote}}
    g_base = {'mcpServers': {'local': local, 'remote': {'serverUrl': remote['url']}}}
    h_base = {
        'git-guardrails': {'enabled': True, 'PreToolUse': [{'matcher': 'run_command', 'hooks': [{'command': 'node block-dangerous-git.js'}]}]},
        'secrets-guardrails': {'enabled': True, 'PreToolUse': [{'matcher': 'run_command|read_file|view_file|grep_search|list_dir|find_by_name|call_mcp_tool|mcp_.*|read_resource', 'hooks': [{'command': 'node block-secrets-read.js'}]}]},
    }
    json.dump(c_base, open(cj, 'w'))
    json.dump(g_base, open(gj, 'w'))
    json.dump(h_base, open(hj, 'w'))
    if sync('--check') != 1: fails.append('sync --check: must flag old and g')
    os.rmdir(os.path.join(h, '.gemini', 'config', 'skills', 'old')); os.remove(os.path.join(h, '.agents', 'skills', 'g', 'SKILL.md'))
    if sync('--check') != 0: fails.append('sync --check: must pass when aligned')

    # A skill linked from a repo that has since moved must show up as a difference.
    moved, broken = mk('moved'), os.path.join(h, '.agents', 'skills', 'moved')
    link(moved, broken); os.rmdir(moved)
    if sync('--check') != 1: fails.append('sync --check: must flag a broken skill link')
    unlink(broken)

    # Finder and Explorer drop their own files in any folder they open, and those are neither skills nor agents.
    for folder in ('skills', 'agents'):
        for name in ('.DS_Store', 'Thumbs.db'):
            stray = os.path.join(h, '.gemini', 'config', folder, name)
            open(stray, 'w').close()
            if sync('--check') != 0: fails.append(f'sync --check: must ignore {name} in Antigravity {folder}')
            os.remove(stray)

    # The skills CLI links here, so skills.json must leave it out.
    skill('.gemini', 'config', 'skills', 'a')
    sync()
    if any('a' in e['include_only'] for e in json.load(open(sj))['entries']): fails.append('sync: native skill listed in skills.json')
    if sync('--check') != 0: fails.append('sync --check: must accept a native skill selected in Claude')
    shutil.rmtree(os.path.join(h, '.gemini', 'config', 'skills', 'a'))
    sync()

    # mcp & hooks checks: mutate and verify --check flags differences
    json.dump({'mcpServers': {**c_base['mcpServers'], 'local': {**local, 'env': {'ROOT': '/b'}}}}, open(cj, 'w'))
    if sync('--check') != 1: fails.append('sync --check: must flag a different stdio server')
    json.dump({'mcpServers': {**c_base['mcpServers'], 'remote': {'type': 'http', 'url': 'https://other.test/mcp'}}}, open(cj, 'w'))
    if sync('--check') != 1: fails.append('sync --check: must flag a different remote server')
    json.dump(c_base, open(cj, 'w'))

    # Each machine keeps its own servers, so one missing from mcp.json is only a notice.
    json.dump({'mcpServers': {**c_base['mcpServers'], 'mine': local}}, open(cj, 'w'))
    if sync('--check') != 0: fails.append('sync --check: must accept an MCP server present only on this machine')
    json.dump(c_base, open(cj, 'w'))

    json.dump({**h_base, 'secrets-guardrails': {**h_base['secrets-guardrails'], 'enabled': False}}, open(hj, 'w'))
    if sync('--check') != 1: fails.append('sync --check: must flag disabled guardrail in Antigravity hooks.json')
    json.dump(h_base, open(hj, 'w'))

    no_block = [{'matcher': 'Bash|PowerShell', 'hooks': [{'command': 'python block-dangerous-git.py'}]}]
    json.dump({**s_base, 'hooks': {'PreToolUse': no_block}}, open(sj_path, 'w'))
    if sync('--check') != 1: fails.append('sync --check: must flag missing onFailure=block')
    json.dump(s_base, open(sj_path, 'w'))

    # Unlink before the cleanup follows the links.
    for n in ('a', 'b', 'link-c', 'link-c2'): unlink(os.path.join(h, '.claude', 'skills', n))

# The commit-msg hook is the only check on the message format.
if shutil.which('sh'):
    with tempfile.TemporaryDirectory() as d:
        def message_accepted(text):
            path = os.path.join(d, 'MSG')
            with open(path, 'w', encoding='utf-8') as f: f.write(text)
            return subprocess.run(['sh', os.path.join(R, 'hooks', 'git', 'commit-msg'), path], capture_output=True).returncode == 0

        for good in ('feat(flow): aggiunge il setup\n', 'fix(hooks): blocca il push\n\n# commento di git\n', 'merge: porta il lavoro su main\n', "Merge branch 'dev'\n", 'Revert "feat(flow): x"\n'):
            if not message_accepted(good): fails.append(f'commit-msg: must accept {good!r}')
        for bad in ('feat: senza ambito\n', 'aggiunge cose\n', 'feat(flow): ' + 'x ' * 16 + '\n', 'feat(flow): ok\n\ncorpo\n', 'feat(flow): ok\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n', 'feat(flow): x Co-Authored-By: y\n', 'Merge stuff\n', 'Revert qualcosa\n'):
            if message_accepted(bad): fails.append(f'commit-msg: must reject {bad!r}')

# git-scm githooks: a hook without the executable bit is ignored.
for hook in ('pre-commit', 'commit-msg'):
    if os.name != 'nt' and not os.access(os.path.join(R, 'hooks', 'git', hook), os.X_OK):
        fails.append(f'hooks/git/{hook}: not executable')

# Google's Rules page: each rule file is truncated past 24,000 bytes.
for rule in ('flow.md', 'shared/global.md', 'personal/global.md'):
    if os.path.getsize(os.path.join(R, rule)) >= 24000: fails.append(f'{rule}: over the Antigravity rule limit')

print('\n'.join(fails) or 'ok')
sys.exit(1 if fails else 0)
