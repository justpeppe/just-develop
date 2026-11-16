"""Self-check of hooks, sync, pipe/lock safety, budgets, docs, and anti-leak. Run: python -X utf8 -I tests/run.py"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Git exports GIT_INDEX_FILE & co. to hooks: clear them so fixture repos stay isolated.
for _k in [k for k in os.environ if k.startswith('GIT_')]:
    del os.environ[_k]

INI = '.i' + 'ni'
ENV = '.e' + 'nv'


def run_json_hook(cmd, payload, cwd=None):
    out = subprocess.run(
        cmd,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=True,
        cwd=cwd,
    ).stdout
    return json.loads(out)


def resolve_sh():
    found = shutil.which('sh')
    if found:
        return found
    git_bin = shutil.which('git')
    candidates = [r'C:\Program Files\Git\bin\sh.exe', r'C:\Program Files (x86)\Git\bin\sh.exe']
    if git_bin:
        git_root = os.path.dirname(os.path.dirname(os.path.realpath(git_bin)))
        candidates.insert(0, os.path.join(git_root, 'bin', 'sh.exe'))
        candidates.insert(1, os.path.join(git_root, 'usr', 'bin', 'sh.exe'))
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return None


def check_git_and_secret_guardrails(fails):
    py_hook = os.path.join(R, 'hooks', 'claude', 'block-dangerous-git.py')
    js_sec = os.path.join(R, 'hooks', 'antigravity', 'block-secrets-read.js')

    def denied_bash(cmd):
        res = run_json_hook([sys.executable, '-X', 'utf8', '-I', py_hook], {'tool_input': {'command': cmd}}, cwd=R)
        return res.get('hookSpecificOutput', {}).get('permissionDecision') == 'deny'

    def sec_denied(payload):
        res = run_json_hook(['node', js_sec], payload)
        return res.get('decision') == 'deny'

    BASH_DENY = [
        'git push', 'git \\push', 'git `push', '`git push', '`git -C repo `push', 'git `\n  push', '& git push',
        'git "p`ush"', 'git reset "--`hard"', 'git reset --\\hard', 'git clean "-f`d"', 'git clean "-`fd"',
        'git branch "-`D" old', 'git checkout "-`f" main', 'git checkout \\.', 'git checkout \\./src', 'git checkout `.\\src',
        'git -C repo push origin main', 'cd a && git merge b', 'git.exe push',
        'C:/Git/bin/git.exe push', '"C:/Program Files/Git/bin/git.exe" push', 'C:/Program\\ Files/Git/bin/git push',
        'git checkout Main.py', 'git checkout -b x', 'git checkout hooks', 'git checkout main', 'git checkout v1.2.0',
        'git checkout release/1.2', 'git switch -c x', 'git switch dev', 'git switch -f dev', 'git switch --discard-changes dev',
        'git branch demo', 'git branch -d old', 'git branch -m old new', 'git worktree add -b x ../wt', 'git worktree remove ../wt',
        'git stash drop', 'git stash clear', 'git stash pop', 'git -c x=y push', 'git reset --hard', 'git clean -fd',
        'git branch -D old', 'git branch -f main HEAD~1', 'git branch -df old', 'git branch -M old main', 'git checkout -B main',
        'git checkout .', 'git checkout ./src', 'git checkout -- Main.py', 'git checkout HEAD -- Main.py',
        'git checkout -f main', 'git restore .', 'git restore Main.py', 'git restore -SW Main.py', 'git restore -sSTABLE Main.py',
        'echo ok\ngit push', "# it's ok\ngit push", '(cd a && git push)', 'echo $(git merge dev)', 'echo "$(git merge dev)"',
        'echo `git push`', 'curl https://host/r#readme && git push', 'FOO=1 git stash drop', 'env FOO=1 git stash drop',
        'sudo git stash drop', "sh -c 'git stash drop'", 'bash -lc "cd a && git stash drop"',
        'cmd /c "git stash drop"', 'cmd.exe /d /s /c "git branch demo"', 'cmd /c "git checkout -b x"', 'cmd /c "git push"',
        'cmd /c"git push"', 'cmd /k"git branch x"',
        'powershell -Command "& \'git\' push"', 'powershell -Command "&\'git\' checkout -b x"',
        'powershell -Command "& \'C:\\Program Files\\Git\\bin\\git.exe\' push"',
        'Write-Output @"\n$(git merge dev)\n"@', 'Write-Output @"\n`git push`\n"@',
    ]
    BASH_ALLOW = [
        'git add -N .', "git add -N -- . ':(exclude).scratch'", 'git status', 'git branch', 'git branch -a',
        'git branch -v', 'git branch --list', 'git branch --show-current', 'git branch --contains main',
        'git worktree list', 'git checkout --help', 'git switch --help', 'git pull',
        'git commit -m push', 'git commit -m "a\ngit push; (git merge)"', 'git commit -m "riga1`ngit push"',
        "git commit -m 'blocca `git push` nei test'", 'cd C:\\Repos\\GIT\\app',
        'git restore --staged Main.py', 'git restore -S .', 'git log --merges',
        "cat <<'EOF'\ngit push\nEOF", "Set-Content out.txt @'\ngit push\n'@", 'Write-Output @"\ngit merge dev\n"@',
    ]

    AGY_CMD_DENY = [
        'git push', 'git `push', '`git push', '`git -C repo `push', 'git `\n  push', 'git "p`ush"', 'git \\push',
        'git -C x merge', 'push --force', 'reset --hard', 'git reset "--`hard"', 'git -C "C:/my repo" clean -fd',
        'git clean "-f`d"', 'git --no-pager -C repo branch -D old', 'git branch "-`D" old', 'git -C repo branch -f main',
        'git branch -df old', 'git branch -M old main', 'git -c k=v reset --hard',
        'git checkout Main.py', 'git checkout -b x', 'git checkout hooks', 'git checkout main', 'git checkout v1.2.0',
        'git checkout release/1.2', 'git switch -c x', 'git switch dev', 'git switch -f dev', 'git switch --discard-changes dev',
        'git branch demo', 'git branch -d old', 'git branch -m old new', 'git worktree add -b x ../wt', 'git worktree remove ../wt',
        'git checkout .', 'git restore Main.py', 'git stash drop', 'git stash pop',
        'echo ok\ngit push', "# it's ok\ngit merge x", '(cd repo && git push)', 'echo "$(git merge x)"', 'echo `git push`',
        'curl https://host/r#readme && git push', 'FOO=1 git stash drop', 'env FOO=1 git stash drop', 'sudo git stash drop',
        "sh -c 'git stash drop'", 'bash -lc "cd a && git stash drop"',
        'cmd /c "git stash drop"', 'cmd.exe /d /s /c "git branch demo"', 'cmd /c "git checkout -b x"', 'cmd /c "git push"',
        'cmd /c"git push"', 'cmd /k"git branch x"',
        'powershell -Command "& \'git\' push"', 'powershell -Command "&\'git\' checkout -b x"',
        'powershell -Command "& \'C:\\Program Files\\Git\\bin\\git.exe\' push"',
        'Write-Output @"\n$(git merge dev)\n"@', 'Write-Output @"\n`git push`\n"@',
    ]
    AGY_CMD_ALLOW = [
        'git status', 'git branch', 'git branch -a', 'git branch -v', 'git branch --list', 'git branch --show-current',
        'git branch --contains main', 'git worktree list', 'git checkout --help', 'git switch --help', 'git log --merges',
        'git restore --staged Main.py', 'git stash', 'git commit -m "evita git push, push --force e reset --hard"',
        'git commit -m "riga1\ngit checkout Main.py"', 'git commit -m "riga1`ngit push"',
        "git commit -m 'blocca `git push` nei test'", "Set-Content out.txt @'\ngit push\n'@", 'Write-Output @"\ngit merge dev\n"@',
    ]

    SEC_CMD_DENY = [
        f'Get-Content C:\\app\\settings{INI}',
        f'python -c "print(open(\'settings{INI}\').read())"',
        f'python -c "--exclude=open(\'settings{INI}\').read()"',
        f'git show HEAD:{ENV}',
        f'git commit -m "$(Get-Content settings{INI})"',
        f'git commit -m "`cat {ENV}`"',
        f'git commit -F settings{INI} -m "ok"',
        f'git commit --author "-m" settings{INI}',
        f'git commit -m "ok" -- -m settings{INI}',
        f'git commit -m "ok" && type settings{INI}',
        f'git commit -m "ok" https://x#y && type settings{INI}',
        f'git commit -m "ok" < settings{INI}',
        f'grep --exclude=*{INI} foo settings{INI}',
        f'python x.py -Exclude settings{INI}',
        f'git grep foo settings{INI}',
        f'findstr foo settings{INI}',
        f'git log -p -- {ENV}',
        f'write-output (Get-Content {ENV})',
        f'echo (cat {ENV})',
        f'Where-Object {{ $_ -eq "a{INI}" }}',
        f'Where-Object {{ (Get-Content settings{INI}) -ne "x" }}',
        f'Select-String -Pattern foo -Path settings{INI}',
        f'Select-String -Pattern:foo settings{INI}',
        f'Select-String -Path a.txt, settings{INI} foo',
        f'rg -efoo settings{INI}',
        f'findstr /C:foo settings{INI} bar.txt',
        f'Where-Object {{ [IO.File]::ReadAllText("{ENV}") -ne "x" }}',
        f'git log -U1 -- {ENV}',
        f'Get-ChildItem -Path settings{INI}',
        f'Get-Content a.txt,settings{INI}',
    ]
    SEC_CMD_ALLOW = [
        f'git show HEAD:{ENV}.example',
        f'git grep -n foo -- ":!*{INI}"',
        f'git grep -n foo -- ":(exclude)*{INI}"',
        f'grep -R --exclude="*{INI}" foo .',
        f'rg --glob=!*{INI} foo',
        f'rg --glob="!*{INI}" foo',
        f'rg -g=!*{INI} foo',
        f'git commit -m "nota su {INI} e {ENV}"',
        f'git -C repo commit -am "riga1\nfix config{INI} e {ENV}.local"',
        f'echo settings{INI}',
        f'git log --grep="settings{INI}"',
        f'git grep "settings{INI}"',
        f'findstr /s "settings{INI}" *.py',
        f'Get-ChildItem | Where-Object {{ $_.Extension -ne "{INI}" }}',
        f'Where-Object {{ $_.Name -notlike "*{INI}" }}',
        f'Select-String -Pattern "x{INI}" -Path *.pas',
        f'Select-String "settings{INI}" *.pas',
        f'# commento su settings{INI} e {ENV}\nWrite-Output ok',
        f'Get-Content foo{INI}.example,bar{ENV}.sample',
        f'Get-ChildItem -Exclude *{INI},*{ENV}',
    ]

    with tempfile.TemporaryDirectory() as td_agy:
        hk = os.path.join(td_agy, 'block-dangerous-git.js')
        shutil.copy(os.path.join(R, 'hooks', 'antigravity', 'block-dangerous-git.js'), hk)
        agy_denied = lambda p: run_json_hook(['node', hk], p, cwd=R).get('decision') == 'deny'

        big_jsonl = os.path.join(td_agy, 'big.jsonl')
        small_jsonl = os.path.join(td_agy, 'small.jsonl')
        big_log = os.path.join(td_agy, 'big.log')
        big_txt = os.path.join(td_agy, 'big.txt')
        open(big_jsonl, 'w', encoding='utf-8').write('{"a":1}\n' * 15000)
        open(small_jsonl, 'w', encoding='utf-8').write('{"a":1}\n')
        open(big_log, 'w', encoding='utf-8').write('line\n' * 30000)
        open(big_txt, 'w', encoding='utf-8').write('line\n' * 30000)

        SEC_FILE_DENY = [
            {'toolCall': {'name': 'view_file', 'args': {'AbsolutePath': f'C:/app/settings{INI}'}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:\\app\\config{INI}'}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:/app/{ENV}'}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:/app/{ENV}.local'}}},
            {'toolCall': {'name': 'find_by_name', 'args': {'Pattern': f'*{INI}'}}},
            {'toolCall': {'name': 'call_mcp_tool', 'args': {'ToolName': 'some_read', 'Arguments': {'path': f'srvc:\\app\\db{INI}'}}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': big_jsonl}}},
            {'toolCall': {'name': 'view_file', 'args': {'AbsolutePath': big_jsonl}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': big_jsonl, 'StartLine': 1, 'EndLine': 101}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': big_jsonl, 'StartLine': '1'}}},
        ]
        SEC_FILE_ALLOW = [
            {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:/app/settings{INI}.example'}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:/app/{ENV}.example'}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:/app/{ENV}.sample'}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:/app/{ENV}.template'}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': f'C:/app/{ENV}.dist'}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': big_jsonl, 'StartLine': 1, 'EndLine': 50}}},
            {'toolCall': {'name': 'view_file', 'args': {'AbsolutePath': big_jsonl, 'StartLine': '1', 'EndLine': '50'}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': small_jsonl}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': big_log}}},
            {'toolCall': {'name': 'read_file', 'args': {'Path': big_txt}}},
        ]

        SEC_DENY = SEC_FILE_DENY + [{'toolCall': {'name': 'run_command', 'args': {'CommandLine': c}}} for c in SEC_CMD_DENY]
        SEC_ALLOW = SEC_FILE_ALLOW + [{'toolCall': {'name': 'run_command', 'args': {'CommandLine': c}}} for c in SEC_CMD_ALLOW]

        with ThreadPoolExecutor(max_workers=16) as ex:
            fails += [f'bash deny: {c!r}' for c, r in zip(BASH_DENY, ex.map(denied_bash, BASH_DENY)) if not r]
            fails += [f'bash allow: {c!r}' for c, r in zip(BASH_ALLOW, ex.map(denied_bash, BASH_ALLOW)) if r]
            fails += [f'py sec deny: {c!r}' for c, r in zip(SEC_CMD_DENY, ex.map(denied_bash, SEC_CMD_DENY)) if not r]
            fails += [f'py sec allow: {c!r}' for c, r in zip(SEC_CMD_ALLOW, ex.map(denied_bash, SEC_CMD_ALLOW)) if r]
            agy_c_deny_p = [{'toolCall': {'name': 'run_command', 'args': {'CommandLine': c}}} for c in AGY_CMD_DENY]
            agy_c_allow_p = [{'toolCall': {'name': 'run_command', 'args': {'CommandLine': c}}} for c in AGY_CMD_ALLOW]
            fails += [f'agy cmd deny: {c!r}' for c, r in zip(AGY_CMD_DENY, ex.map(agy_denied, agy_c_deny_p)) if not r]
            fails += [f'agy cmd allow: {c!r}' for c, r in zip(AGY_CMD_ALLOW, ex.map(agy_denied, agy_c_allow_p)) if r]
            fails += [f'sec deny: {p!r}' for p, r in zip(SEC_DENY, ex.map(sec_denied, SEC_DENY)) if not r]
            fails += [f'sec allow: {p!r}' for p, r in zip(SEC_ALLOW, ex.map(sec_denied, SEC_ALLOW)) if r]

        # Log only on deny without command text; failed log write must not bypass deny.
        log = os.path.join(td_agy, 'block-dangerous-git.log')
        if os.path.isfile(log):
            os.remove(log)
        agy_denied({'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git status --secret-marker'}}})
        if os.path.isfile(log):
            fails.append('agy log: allowed command must not write log file')
        agy_denied({'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git stash drop --secret-marker'}}})
        if not os.path.isfile(log) or 'secret-marker' in open(log, encoding='utf-8').read():
            fails.append('agy log: must record deny without command text')
        os.remove(log)
        if os.name != 'nt':
            os.chmod(td_agy, 0o500)
            if not agy_denied({'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git stash drop'}}}):
                fails.append('agy: a failed log write allowed a dangerous command')
            os.chmod(td_agy, 0o700)


def check_sync_from_claude(fails):
    def link(target, path):
        if os.name == 'nt':
            import _winapi
            _winapi.CreateJunction(target, path)
        else:
            os.symlink(target, path)

    unlink = os.rmdir if os.name == 'nt' else os.unlink

    with tempfile.TemporaryDirectory() as h:
        h = os.path.realpath(h)
        mk = lambda *p: os.makedirs(os.path.join(h, *p), exist_ok=True) or os.path.join(h, *p)
        skill = lambda *p: open(os.path.join(mk(*p), 'SKILL.md'), 'w', encoding='utf-8').close()

        for n in ('a', 'g'):
            skill('.agents', 'skills', n)
        for n in ('b', 'c', 'd'):
            skill('ext', 'skills', n)
        skill('.claude', 'skills', 'e')
        skill('.claude', 'skills', 'f')
        mk('.claude', 'skills', 'nofile')
        for n, t in (('a', '.agents/skills/a'), ('b', 'ext/skills/b'), ('link-c', 'ext/skills/c'), ('link-c2', 'ext/skills/c')):
            link(os.path.join(h, t), os.path.join(h, '.claude', 'skills', n))
        open(os.path.join(h, '.claude', 'CLAUDE.md'), 'w', encoding='utf-8').write('x\n')
        open(os.path.join(mk('.claude', 'agents'), 'r.md'), 'w', encoding='utf-8').write('---\nname: r\ntools: Read\nmodel: sonnet\n---\nbody\n')

        open(os.path.join(mk('repo-agents'), 'k.md'), 'w', encoding='utf-8').write('---\nname: k\ndisallowedTools: Write\neffort: high\n---\nbody\n')
        link(os.path.join(h, 'repo-agents'), os.path.join(h, '.claude', 'agents', 'linked'))
        open(os.path.join(h, 'repo-agents', 'only-claude.md'), 'w', encoding='utf-8').write('---\nname: only-claude\nantigravity:  "false" \n---\nbody\n')

        fx = mk('repo')
        mk('repo', 'scripts')
        mk('repo', 'shared')
        mk('repo', 'personal')
        mk('repo', 'skills')
        shutil.copy(os.path.join(R, 'scripts', 'sync-from-claude.py'), os.path.join(fx, 'scripts'))
        for rel in ('flow.md', 'shared/global.md', 'personal/global.md'):
            shutil.copy(os.path.join(R, rel), os.path.join(fx, rel))
        local = {'command': 'demo-server', 'args': ['--x'], 'env': {'ROOT': '/a'}}
        remote = {'type': 'http', 'url': 'https://example.test/mcp'}
        json.dump({'mcpServers': {'local': local, 'remote': remote}}, open(os.path.join(fx, 'mcp.json'), 'w', encoding='utf-8'))

        sj_path = os.path.join(h, '.claude', 'settings.json')
        s_base = {
            'skillOverrides': {'f': 'off'},
            'enabledPlugins': {'ponytail@ponytail': False},
            'permissions': {'deny': [
                'Bash(git push *)', 'Bash(git merge *)', 'PowerShell(git push *)', 'PowerShell(git merge *)',
                'Bash(agy *)', 'PowerShell(agy *)', f'Read(//**/*{INI})', f'Read(//**/{ENV})',
            ]},
            'hooks': {'PreToolUse': [{'matcher': 'Bash|PowerShell', 'hooks': [{'command': 'python block-dangerous-git.py', 'onFailure': 'block'}]}]},
        }
        json.dump(s_base, open(sj_path, 'w', encoding='utf-8'))
        mk('.gemini', 'config', 'skills', 'old')

        run = lambda *a: subprocess.run(
            [sys.executable, '-X', 'utf8', '-I', os.path.join(fx, 'scripts', 'sync-from-claude.py'), *a],
            env={**os.environ, 'HOME': h, 'USERPROFILE': h},
            capture_output=True,
            text=True,
            encoding='utf-8',
        )
        sync = lambda *a: run(*a).returncode
        sj = os.path.join(h, '.gemini', 'config', 'skills.json')

        if sync('--check') != 1 or os.listdir(os.path.join(h, '.gemini', 'config')) != ['skills']:
            fails.append('sync --check: must fail and write nothing')
        if sync() != 0:
            fails.append('sync: exit != 0')
        if '  - read_file\n' not in open(os.path.join(h, '.gemini', 'config', 'agents', 'r.md'), encoding='utf-8').read():
            fails.append('sync: agent missing read_file tool')
        k = os.path.join(h, '.gemini', 'config', 'agents', 'k.md')
        if not os.path.isfile(k):
            fails.append('sync: agent in a linked folder not copied')
        else:
            copied = open(k, encoding='utf-8').read()
            if 'disallowedTools:' in copied or 'effort:' in copied:
                fails.append('sync: Claude-only agent fields copied')
        if os.path.exists(os.path.join(h, '.gemini', 'config', 'agents', 'only-claude.md')):
            fails.append('sync: copied an agent marked antigravity: false')
        for rule in ('claude-md.md', 'flow.md', 'shared.md', 'personal.md'):
            if not os.path.isfile(os.path.join(h, '.gemini', 'config', 'rules', rule)):
                fails.append(f'sync: rule {rule} missing')
        want = {'entries': [
            {'path': f'{h}/.agents/skills'.replace('\\', '/'), 'include_only': ['a']},
            {'path': f'{h}/.claude/skills'.replace('\\', '/'), 'include_only': ['e']},
            {'path': f'{h}/ext/skills'.replace('\\', '/'), 'include_only': ['b', 'c']},
        ]}
        if not os.path.exists(sj) or json.load(open(sj, encoding='utf-8')) != want:
            fails.append('sync: skills.json differs')
        if not os.path.isdir(os.path.join(h, '.gemini', 'config', 'skills', 'old')):
            fails.append('sync: deleted config/skills')

        # Extra rules (e.g. delphi.md) and Antigravity-only agents/knowledge survive sync; claude-md.md skipped on @import-only.
        extra_rule = os.path.join(h, '.gemini', 'config', 'rules', 'delphi.md')
        open(extra_rule, 'w', encoding='utf-8').write('---\ntrigger: glob\n---\nkeep\n')
        gemini_md = os.path.join(h, '.gemini', 'GEMINI.md')
        open(gemini_md, 'w', encoding='utf-8').write('imports\n')
        own_agent = os.path.join(h, '.gemini', 'config', 'agents', 'mine.md')
        own_note = os.path.join(mk('.gemini', 'config', 'knowledge'), 'note.md')
        for p in (own_agent, own_note):
            open(p, 'w', encoding='utf-8').write('keep\n')
        sync()
        if not os.path.isfile(extra_rule):
            fails.append('sync: deleted extra rule delphi.md')
        if open(gemini_md, encoding='utf-8').read() != 'imports\n':
            fails.append('sync: overwrote ~/.gemini/GEMINI.md')
        if not os.path.isfile(own_agent):
            fails.append('sync: deleted an agent present only in Antigravity')
        if not os.path.isfile(own_note):
            fails.append('sync: deleted knowledge present only in Antigravity')
        if sync('--check') != 1:
            fails.append('sync --check: must flag an agent present only in Antigravity')
        os.remove(own_agent)
        shutil.rmtree(os.path.join(h, '.gemini', 'config', 'knowledge'))

        cj = os.path.join(h, '.claude.json')
        gj = os.path.join(h, '.gemini', 'config', 'mcp_config.json')
        hj = os.path.join(h, '.gemini', 'config', 'hooks.json')
        cfg_j = os.path.join(h, '.gemini', 'config', 'config.json')
        c_base = {'mcpServers': {'local': {'type': 'stdio', **local}, 'remote': remote}}
        g_base = {'mcpServers': {'local': local, 'remote': {'serverUrl': remote['url']}}}
        h_base = {
            'git-guardrails': {'enabled': True, 'PreToolUse': [{'matcher': 'run_command', 'hooks': [{'command': 'node block-dangerous-git.js'}]}]},
            'secrets-guardrails': {'enabled': True, 'PreToolUse': [{'matcher': 'run_command|read_file|view_file|grep_search|list_dir|find_by_name|call_mcp_tool|mcp_.*|read_resource', 'hooks': [{'command': 'node block-secrets-read.js'}]}]},
        }
        json.dump(c_base, open(cj, 'w', encoding='utf-8'))
        json.dump(g_base, open(gj, 'w', encoding='utf-8'))
        json.dump(h_base, open(hj, 'w', encoding='utf-8'))
        json.dump({'plugins': {'ponytail': {'enabled': False}}}, open(cfg_j, 'w', encoding='utf-8'))
        os.rmdir(os.path.join(h, '.gemini', 'config', 'skills', 'old'))
        os.remove(os.path.join(h, '.agents', 'skills', 'g', 'SKILL.md'))
        if sync('--check') != 0:
            fails.append(f'sync --check: must pass when aligned: {run("--check").stdout}')

        # @import-only CLAUDE.md removes stale claude-md.md and --check flags it before cleanup.
        open(os.path.join(h, '.claude', 'CLAUDE.md'), 'w', encoding='utf-8').write('\n'.join(['@shared/global.md', '@flow.md']) + '\n')
        if sync('--check') != 1:
            fails.append('sync --check: must flag stale claude-md.md when CLAUDE.md is @import-only')
        if sync() != 0 or os.path.exists(os.path.join(h, '.gemini', 'config', 'rules', 'claude-md.md')):
            fails.append('sync: must remove claude-md.md when CLAUDE.md is @import-only')
        if sync('--check') != 0:
            fails.append('sync --check: must pass with extra rule delphi.md and @import-only CLAUDE.md')

        # 2-hop broken link into REPO/skills/* is cleaned automatically; external broken links are still flagged.
        temp_sk = mk('repo', 'skills', 'branch-only')
        open(os.path.join(temp_sk, 'SKILL.md'), 'w', encoding='utf-8').close()
        ag_link = os.path.join(h, '.agents', 'skills', 'branch-only')
        cl_link = os.path.join(h, '.claude', 'skills', 'branch-only')
        link(temp_sk, ag_link)
        link(ag_link, cl_link)
        shutil.rmtree(temp_sk)
        if sync('--check') != 1:
            fails.append('sync --check: must report broken internal skill link before cleanup')
        if sync() != 0 or os.path.lexists(ag_link) or os.path.lexists(cl_link):
            fails.append('sync: must clean broken 2-hop junctions targeting REPO/skills/*')
        if sync('--check') != 0:
            fails.append('sync --check: must pass after cleaning internal broken junctions')

        moved, broken = mk('moved'), os.path.join(h, '.agents', 'skills', 'moved')
        link(moved, broken)
        os.rmdir(moved)
        sync()
        if not os.path.lexists(broken) or sync('--check') != 1:
            fails.append('sync: must preserve and flag external broken skill link')
        unlink(broken)

        # Broken agent link and duplicate agent names.
        gone_target, gone = mk('gone-target'), os.path.join(h, 'repo-agents', 'gone.md')
        link(gone_target, gone)
        os.rmdir(gone_target)
        out = run('--check')
        if out.returncode != 1 or 'broken link:' not in out.stdout:
            fails.append('sync --check: must report a broken agent link without crashing')
        unlink(gone)
        twin = os.path.join(h, 'repo-agents', 'r.md')
        open(twin, 'w', encoding='utf-8').write('---\nname: r2\n---\nbody\n')
        if 'two agents named r.md' not in run('--check').stdout:
            fails.append('sync --check: must flag two agents with the same file name')
        os.remove(twin)

        # Missing ~/.claude/settings.json must not crash sync.
        os.remove(sj_path)
        if sync() != 0:
            fails.append('sync: crashed when settings.json was absent')
        json.dump(s_base, open(sj_path, 'w', encoding='utf-8'))
        sync()

        # Guardrail checks: agy deny, ponytail disabled, ponytail-review duplicate, hooks.
        no_agy = [r for r in s_base['permissions']['deny'] if 'agy' not in r]
        json.dump({**s_base, 'permissions': {'deny': no_agy}}, open(sj_path, 'w', encoding='utf-8'))
        if sync('--check') != 1:
            fails.append('sync --check: must flag missing agy deny rules')
        dup_pt = mk('.agents', 'skills', 'ponytail-review')
        open(os.path.join(dup_pt, 'SKILL.md'), 'w', encoding='utf-8').close()
        json.dump(s_base, open(sj_path, 'w', encoding='utf-8'))
        if 'duplicate ponytail-review' not in run('--check').stdout:
            fails.append('sync --check: must flag duplicate ponytail-review in ~/.agents/skills')
        shutil.rmtree(dup_pt)
        json.dump({**s_base, 'enabledPlugins': {'ponytail@ponytail': True}}, open(sj_path, 'w', encoding='utf-8'))
        if sync('--check') != 1:
            fails.append('sync --check: must flag enabled ponytail@ponytail in Claude settings')
        json.dump(s_base, open(sj_path, 'w', encoding='utf-8'))
        json.dump({'plugins': {'ponytail': {'enabled': True}}}, open(cfg_j, 'w', encoding='utf-8'))
        if sync('--check') != 1:
            fails.append('sync --check: must flag enabled ponytail in Antigravity config.json')
        json.dump({'plugins': {'ponytail': {'enabled': False}}}, open(cfg_j, 'w', encoding='utf-8'))
        json.dump({**h_base, 'secrets-guardrails': {**h_base['secrets-guardrails'], 'enabled': False}}, open(hj, 'w', encoding='utf-8'))
        if sync('--check') != 1:
            fails.append('sync --check: must flag disabled guardrail in Antigravity hooks.json')
        json.dump(h_base, open(hj, 'w', encoding='utf-8'))
        no_block = [{'matcher': 'Bash|PowerShell', 'hooks': [{'command': 'python block-dangerous-git.py'}]}]
        json.dump({**s_base, 'hooks': {'PreToolUse': no_block}}, open(sj_path, 'w', encoding='utf-8'))
        if sync('--check') != 1:
            fails.append('sync --check: must flag missing onFailure=block')

        for n in ('a', 'b', 'link-c', 'link-c2'):
            unlink(os.path.join(h, '.claude', 'skills', n))


def check_git_hooks(fails):
    sh_bin = resolve_sh()
    if not sh_bin:
        fails.append('git hooks: sh binary not found (checked PATH and Git for Windows)')
    else:
        with tempfile.TemporaryDirectory() as d:
            hook_cm = os.path.join(R, 'hooks', 'git', 'commit-msg')

            def check_cm(item):
                idx, text = item
                path = os.path.join(d, f'MSG_{idx}')
                with open(path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(text)
                return subprocess.run([sh_bin, hook_cm, path], capture_output=True).returncode == 0

            good_msgs = (
                'feat(flow): aggiunge il setup\n',
                'fix(hooks): blocca il push\n\n# commento di git\n',
                'merge: porta il lavoro su main\n',
                "Merge branch 'dev'\n",
                "Merge branch 'office/feat/hooks'\n\n# Conflicts:\n#\tflow.md\n",
                "Merge branch 'office/feat/hooks'\n\nConflicts:\n\tflow.md\n",
                "Merge branches 'a' and 'b'\n\nConflicts:\n\tflow.md\n",
                "Merge pull request #4 from justpeppe/office/feat/hooks\n\nAdd background sync\n",
                "Merge remote-tracking branch 'origin/main'\n",
                "Merge tag 'v1.0.0'\n\nRelease 1.0\n",
                'Revert "feat(flow): x"\n',
                'Revert "feat(flow): aggiunge sync"\n\nThis reverts commit 1234567890abcdef1234567890abcdef12345678.\n',
            )
            bad_msgs = (
                'feat: senza ambito\n',
                'aggiunge cose\n',
                'feat(flow): ' + 'x ' * 16 + '\n',
                'feat(flow): ok\n\ncorpo\n',
                'merge: porta su main\n\ncorpo libero\n',
                'merge: ' + 'x ' * 16 + '\n',
                'feat(flow): ok\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n',
                'feat(flow): x Co-Authored-By: y\n',
                'Merge stuff\n',
                'Revert qualcosa\n',
            )
            hooks = ('pre-commit', 'commit-msg', 'post-merge', 'post-checkout', 'post-rewrite')

            def check_hook_syntax(hook):
                hp = os.path.join(R, 'hooks', 'git', hook)
                if not os.path.isfile(hp):
                    return f'hooks/git/{hook}: missing'
                if b'\r\n' in open(hp, 'rb').read():
                    return f'hooks/git/{hook}: contains CRLF (must be LF)'
                if subprocess.run([sh_bin, '-n', hp], capture_output=True).returncode != 0:
                    return f'hooks/git/{hook}: sh -n syntax check failed'
                if os.name != 'nt' and not os.access(hp, os.X_OK):
                    return f'hooks/git/{hook}: not executable'
                return None

            with ThreadPoolExecutor(max_workers=8) as ex:
                good_res = list(ex.map(check_cm, enumerate(good_msgs)))
                bad_res = list(ex.map(check_cm, enumerate(bad_msgs, len(good_msgs))))
                hook_res = list(ex.map(check_hook_syntax, hooks))

            fails += [f'commit-msg: must accept {g!r}' for g, ok in zip(good_msgs, good_res) if not ok]
            fails += [f'commit-msg: must reject {b!r}' for b, ok in zip(bad_msgs, bad_res) if ok]
            fails += [err for err in hook_res if err]

            # post-checkout guard: file checkout ($3=0) and orphan ($2=000...) exit 0 cleanly.
            pc_hook = os.path.join(R, 'hooks', 'git', 'post-checkout')
            for args in (['a', 'b', '0'], ['a', '0' * 40, '1']):
                if subprocess.run([sh_bin, pc_hook, *args], cwd=R, capture_output=True).returncode != 0:
                    fails.append(f'post-checkout guard failed for args={args}')


def check_pipe_lock_and_mergetree(fails):
    scripts_dir = os.path.join(R, 'scripts')
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import background_checker as bg

    with tempfile.TemporaryDirectory() as td:
        td = os.path.realpath(td)
        sdir = os.path.join(td, 'state')
        os.makedirs(sdir, exist_ok=True)

        # session_check.py pipe/EOF safety + cwd filtering + AGY injectSteps format.
        fake_worker = os.path.join(td, 'sleep_worker.py')
        open(fake_worker, 'w', encoding='utf-8').write('import time\ntime.sleep(4.0)\n')
        t0 = time.monotonic()
        r_sc = subprocess.run(
            [sys.executable, '-X', 'utf8', '-I', os.path.join(scripts_dir, 'session_check.py'), '--client', 'claude', '--state-dir', sdir],
            input=json.dumps({'cwd': td}),
            env={**os.environ, 'JUST_DEVELOP_BG_WORKER': fake_worker},
            cwd=R,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        dt = time.monotonic() - t0
        if dt >= 2.5 or json.loads(r_sc.stdout) != {}:
            fails.append(f'session_check: slow/bad spawn ({dt:.2f}s, {r_sc.stdout!r})')

        bg.write_json_atomic(os.path.join(sdir, 'update-state.json'), {
            'schema_version': 1,
            'git': {'checked_at': time.time(), 'status': 'behind', 'behind': 2, 'default_branch': 'main', 'branch': 'main'},
            'assets': {'checked_at': time.time()},
        })
        r_out = run_json_hook(
            [sys.executable, '-X', 'utf8', '-I', os.path.join(scripts_dir, 'session_check.py'), '--client', 'claude', '--state-dir', sdir],
            {'cwd': td},
            cwd=R,
        )
        r_in = run_json_hook(
            [sys.executable, '-X', 'utf8', '-I', os.path.join(scripts_dir, 'session_check.py'), '--client', 'claude', '--state-dir', sdir],
            {'cwd': R},
            cwd=R,
        )
        r_agy = run_json_hook(
            [sys.executable, '-X', 'utf8', '-I', os.path.join(scripts_dir, 'session_check.py'), '--client', 'antigravity', '--state-dir', sdir],
            {'cwd': R},
            cwd=R,
        )
        if 'hookSpecificOutput' in r_out or 'systemMessage' not in r_out:
            fails.append(f'session_check: outside cwd leaked additionalContext: {r_out}')
        if 'hookSpecificOutput' not in r_in:
            fails.append(f'session_check: inside repo missing additionalContext: {r_in}')
        if not (r_agy.get('injectSteps') or [{}])[0].get('systemMessage', {}).get('metadata', {}).get('user_markdown'):
            fails.append(f'session_check: AGY output missing user_markdown: {r_agy}')

        # clear_git_state without update-state.json returns {} and creates no files.
        empty_sdir = os.path.join(td, 'empty-state')
        os.makedirs(empty_sdir, exist_ok=True)
        cleared_empty = bg.clear_git_state(empty_sdir)
        if cleared_empty != {} or os.listdir(empty_sdir):
            fails.append(f'clear_git_state: expected empty no-op, got {cleared_empty}, {os.listdir(empty_sdir)}')

        # OS kernel FileLock across processes and clear-git.flag invalidation under contention.
        lock_sdir = os.path.join(td, 'lock-state')
        os.makedirs(lock_sdir, exist_ok=True)
        bg.write_json_atomic(os.path.join(lock_sdir, 'update-state.json'), {
            'schema_version': 1,
            'git': {'status': 'ahead', 'ahead': 2, 'checked_at': time.time()},
            'assets': {'checked_at': time.time()},
        })
        holder = os.path.join(td, 'hold_lock.py')
        open(holder, 'w', encoding='utf-8').write(
            f"import sys\nsys.path.insert(0, {scripts_dir!r})\nimport background_checker as bg\n"
            f"lk = bg.FileLock({os.path.join(lock_sdir, 'update.lock')!r})\n"
            "assert lk.acquire()\nprint('LOCKED', flush=True)\nsys.stdin.read(1)\nlk.release()\n"
        )
        with subprocess.Popen(
            [sys.executable, '-X', 'utf8', '-I', holder],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as p1:
            try:
                if p1.stdout.readline().strip() != 'LOCKED':
                    fails.append('background_checker: lock holder failed to acquire')
                else:
                    r2 = subprocess.run(
                        [sys.executable, '-X', 'utf8', '-I', os.path.join(scripts_dir, 'background_checker.py'), '--mode', 'git', '--state-dir', lock_sdir, '--json'],
                        env={**os.environ, 'JUST_DEVELOP_REPO': td},
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    if json.loads(r2.stdout).get('locked') is not True:
                        fails.append('background_checker: second run did not see kernel lock')
                    bg.clear_git_state(lock_sdir)
                    if not os.path.isfile(os.path.join(lock_sdir, 'clear-git.flag')):
                        fails.append('clear_git_state: missing clear-git.flag while lock was held')
            finally:
                if p1.stdin and not p1.stdin.closed:
                    p1.stdin.close()
                p1.wait(timeout=5)
        r_flag = bg.run_check(mode='auto', state_dir=lock_sdir, repo_root=td)
        persisted_git = bg.read_json_safe(os.path.join(lock_sdir, 'update-state.json')).get('git')
        if os.path.isfile(os.path.join(lock_sdir, 'clear-git.flag')) or r_flag.get('state', {}).get('git') != {} or persisted_git != {}:
            fails.append(f'run_check: clear-git.flag did not invalidate git state: {r_flag}, persisted={persisted_git}')
        r3 = subprocess.run(
            [sys.executable, '-X', 'utf8', '-I', os.path.join(scripts_dir, 'background_checker.py'), '--mode', 'git', '--state-dir', lock_sdir, '--json'],
            env={**os.environ, 'JUST_DEVELOP_REPO': td},
            capture_output=True,
            text=True,
            check=True,
        )
        if json.loads(r3.stdout).get('locked') is not False:
            fails.append('background_checker: kernel lock not released after exit')

        # Cross-PC dirty worktree (.scratch excluded) + git merge-tree conflict detection.
        bare = os.path.join(td, 'bare.git')
        w1, w2 = os.path.join(td, 'w1'), os.path.join(td, 'w2')
        subprocess.run(['git', 'init', '--bare', '-b', 'main', bare], check=True, capture_output=True)
        subprocess.run(['git', 'clone', bare, w1], check=True, capture_output=True)
        subprocess.run(['git', '-C', w1, 'config', 'user.email', 't@example.com'], check=True)
        subprocess.run(['git', '-C', w1, 'config', 'user.name', 'Test'], check=True)
        open(os.path.join(w1, 'a.txt'), 'w', encoding='utf-8').write('v1\n')
        os.makedirs(os.path.join(w1, '.scratch'), exist_ok=True)
        open(os.path.join(w1, '.scratch', 'spec.md'), 'w', encoding='utf-8').write('s1\n')
        subprocess.run(['git', '-C', w1, 'add', '.'], check=True)
        subprocess.run(['git', '-C', w1, 'commit', '-m', 'chore(init): v1'], check=True, capture_output=True)
        subprocess.run(['git', '--git-dir', bare, 'fetch', w1, 'main:main'], check=True, capture_output=True)

        subprocess.run(['git', 'clone', bare, w2], check=True, capture_output=True)
        subprocess.run(['git', '-C', w2, 'config', 'user.email', 't@example.com'], check=True)
        subprocess.run(['git', '-C', w2, 'config', 'user.name', 'Test'], check=True)

        open(os.path.join(w1, 'a.txt'), 'w', encoding='utf-8').write('v2-remote\n')
        open(os.path.join(w1, '.scratch', 'spec.md'), 'w', encoding='utf-8').write('s2-remote\n')
        subprocess.run(['git', '-C', w1, 'add', '.'], check=True)
        subprocess.run(['git', '-C', w1, 'commit', '-m', 'feat(core): v2'], check=True, capture_output=True)
        subprocess.run(['git', '--git-dir', bare, 'fetch', w1, 'main:main'], check=True, capture_output=True)

        open(os.path.join(w2, '.scratch', 'spec.md'), 'w', encoding='utf-8').write('s2-local\n')
        res_scratch = bg.check_git_repo(w2)
        if res_scratch.get('status') != 'behind' or res_scratch.get('conflict_kind') is not None:
            fails.append(f'merge-tree: dirty .scratch triggered conflict: {res_scratch}')

        open(os.path.join(w2, 'a.txt'), 'w', encoding='utf-8').write('v2-local\n')
        res_dirty = bg.check_git_repo(w2)
        if res_dirty.get('conflict_kind') != 'dirty_worktree' or 'a.txt' not in (res_dirty.get('conflict_files') or []):
            fails.append(f'merge-tree: failed to flag dirty_worktree on a.txt: {res_dirty}')

        subprocess.run(['git', '-C', w2, 'add', 'a.txt'], check=True)
        subprocess.run(['git', '-C', w2, 'commit', '-m', 'fix(core): local'], check=True, capture_output=True)
        res_mt = bg.check_git_repo(w2)
        if res_mt.get('conflict_kind') != 'merge_tree' or 'a.txt' not in (res_mt.get('conflict_files') or []):
            fails.append(f'merge-tree: failed to flag committed conflict on a.txt: {res_mt}')

        # Untracked file in a new subdirectory must appear in parse_porcelain_dirty_paths (-uall).
        sub_dir = os.path.join(w2, 'newsub')
        os.makedirs(sub_dir, exist_ok=True)
        open(os.path.join(sub_dir, 'nested.txt'), 'w', encoding='utf-8').write('sub\n')
        dirty_sub = bg.parse_porcelain_dirty_paths(w2)
        if 'newsub/nested.txt' not in dirty_sub or 'newsub/' in dirty_sub:
            fails.append(f'parse_porcelain_dirty_paths: failed -uall subdir check: {sorted(dirty_sub)}')

        # Sibling overlaps: excludes pushed current branch without -u, detects sibling overlap and remote case collisions.
        subprocess.run(['git', '-C', w1, 'checkout', '-b', 'office/feat/alpha'], check=True, capture_output=True)
        open(os.path.join(w1, 'b.txt'), 'w', encoding='utf-8').write('from-office\n')
        subprocess.run(['git', '-C', w1, 'add', 'b.txt'], check=True)
        subprocess.run(['git', '-C', w1, 'commit', '-m', 'feat(ui): office'], check=True, capture_output=True)
        subprocess.run(['git', '--git-dir', bare, 'fetch', w1, 'office/feat/alpha:refs/heads/office/feat/alpha'], check=True, capture_output=True)

        w3 = os.path.join(td, 'w3')
        subprocess.run(['git', 'clone', bare, w3], check=True, capture_output=True)
        subprocess.run(['git', '-C', w3, 'config', 'user.email', 't@example.com'], check=True)
        subprocess.run(['git', '-C', w3, 'config', 'user.name', 'Test'], check=True)
        subprocess.run(['git', '-C', w3, 'checkout', '-b', 'home/fix/beta'], check=True, capture_output=True)
        open(os.path.join(w3, 'b.txt'), 'w', encoding='utf-8').write('from-home\n')
        subprocess.run(['git', '-C', w3, 'add', 'b.txt'], check=True)
        subprocess.run(['git', '-C', w3, 'commit', '-m', 'fix(ui): home'], check=True, capture_output=True)
        subprocess.run(['git', '--git-dir', bare, 'fetch', w3, 'home/fix/beta:refs/heads/home/fix/beta'], check=True, capture_output=True)

        res_sib = bg.check_git_repo(w3)
        overlaps = res_sib.get('sibling_overlaps') or []
        if [o.get('branch') for o in overlaps] != ['origin/office/feat/alpha'] or 'b.txt' not in (overlaps[0].get('overlap_files') or []):
            fails.append(f'sibling_overlaps: expected only origin/office/feat/alpha on b.txt, got {res_sib}')
        direct_sib = bg.find_sibling_overlaps(w3, 'origin/main', {'b.txt'}, 'home/fix/beta')
        if [o.get('branch') for o in direct_sib] != ['origin/office/feat/alpha']:
            fails.append(f'find_sibling_overlaps: failed self-branch exclusion without -u: {direct_sib}')

        subprocess.run(['git', '--git-dir', bare, 'pack-refs', '--all', '--prune'], check=True, capture_output=True)
        alpha_sha = subprocess.run(['git', '--git-dir', bare, 'rev-parse', 'refs/heads/office/feat/alpha'], capture_output=True, text=True, check=True).stdout.strip()
        packed_path = os.path.join(bare, 'packed-refs')
        packed_lines = open(packed_path, encoding='utf-8').read().splitlines()
        hdrs = [ln for ln in packed_lines if ln.startswith('#')]
        refs = sorted([ln for ln in packed_lines if ln and not ln.startswith(('#', '^'))] + [f'{alpha_sha} refs/heads/Office/feat/alpha'], key=lambda ln: ln.split(' ', 1)[1])
        open(packed_path, 'w', encoding='utf-8', newline='\n').write('\n'.join(hdrs + refs) + '\n')
        cc_direct = bg.find_remote_case_collisions(w3)
        res_cc = bg.check_git_repo(w3)
        expected_cc = [['origin/Office/feat/alpha', 'origin/office/feat/alpha']]
        if cc_direct != expected_cc or res_cc.get('case_collisions') != expected_cc:
            fails.append(f'case_collisions: expected {expected_cc}, got direct={cc_direct}, repo={res_cc}')

        # check-updates.py offline smoke test.
        no_rem = os.path.join(td, 'local-only')
        subprocess.run(['git', 'init', '-b', 'main', no_rem], check=True, capture_output=True)
        cu = subprocess.run(
            [sys.executable, '-X', 'utf8', '-I', os.path.join(scripts_dir, 'check-updates.py'), '--state-dir', sdir, '--json'],
            env={**os.environ, 'HOME': td, 'USERPROFILE': td, 'JUST_DEVELOP_REPO': no_rem},
            capture_output=True,
            text=True,
            check=True,
        )
        if json.loads(cu.stdout).get('state', {}).get('git', {}).get('status') != 'no_remote':
            fails.append(f'check-updates.py unexpected output: {cu.stdout}')


def check_budgets_docs_and_antileak(fails):
    gitattr_path = os.path.join(R, '.gitattributes')
    if not os.path.isfile(gitattr_path) or 'hooks/git/* text eol=lf' not in open(gitattr_path, encoding='utf-8').read():
        fails.append('.gitattributes: missing or missing hooks/git/* text eol=lf rule')
    flow_sz = os.path.getsize(os.path.join(R, 'flow.md'))
    if flow_sz > 3000:
        fails.append(f'flow.md exceeds 3000 B budget: {flow_sz} B')
    for rule in ('flow.md', 'shared/global.md', 'personal/global.md'):
        sz = os.path.getsize(os.path.join(R, rule))
        if sz >= 24000:
            fails.append(f'{rule}: over the Antigravity 24000 B rule limit ({sz} B)')

    ls_out = subprocess.run(
        ['git', '-C', R, 'ls-files', '--cached', '--others', '--exclude-standard'],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    active_files = [
        f for f in ls_out
        if not f.startswith('.scratch/') and os.path.isfile(os.path.join(R, f))
    ]

    # docs/index.mdx must catalog every active file in the repo.
    idx_txt = open(os.path.join(R, 'docs', 'index.mdx'), encoding='utf-8').read()
    for f in active_files:
        if f'`{f}`' not in idx_txt:
            fails.append(f'docs/index.mdx missing catalog row for: {f}')

    # docs/docs.json and docs/SUMMARY.md links must resolve on disk.
    docs_json = json.load(open(os.path.join(R, 'docs', 'docs.json'), encoding='utf-8'))
    for grp in (docs_json.get('navigation') or {}).get('groups') or []:
        for page in grp.get('pages') or []:
            if not any(os.path.isfile(os.path.join(R, 'docs', page + ext)) for ext in ('.mdx', '.md')):
                fails.append(f'docs/docs.json broken page reference: {page}')

    summary_txt = open(os.path.join(R, 'docs', 'SUMMARY.md'), encoding='utf-8').read()
    for target in re.findall(r'\]\(([^)]+)\)', summary_txt):
        if target.startswith(('http://', 'https://', '#')):
            continue
        clean_target = target.split('#', 1)[0]
        if clean_target and not os.path.isfile(os.path.join(R, 'docs', clean_target)):
            fails.append(f'docs/SUMMARY.md broken link: {target}')

    # docs/skills.md must cite every skill in skills/.
    skills_doc = open(os.path.join(R, 'docs', 'skills.md'), encoding='utf-8').read()
    for d in sorted(os.listdir(os.path.join(R, 'skills'))):
        if os.path.isfile(os.path.join(R, 'skills', d, 'SKILL.md')):
            if f'`{d}`' not in skills_doc and f'skills/{d}/SKILL.md' not in skills_doc:
                fails.append(f'docs/skills.md missing skill: {d}')

    # Banned terms and emoji check limited to operational docs/skills (not DECISIONS.md, .scratch/, or tests/run.py).
    banned_terms = (
        'Review: single', 'Review: flash', '3.8 Flash', 'flow-prompts.md', 'righe 1..N',
        'Livello 1', 'Livello 2', 'Livello 3', 'Livello 4', 'Livelli di Zoom', 'Doc a 4 Livelli', 'Questa pagina documenta',
    )
    op_files = [f for f in active_files if f not in ('DECISIONS.md', 'tests/run.py') and f.endswith(('.md', '.mdx'))]
    for f in op_files:
        txt = open(os.path.join(R, f), encoding='utf-8').read()
        for term in banned_terms:
            if term in txt:
                fails.append(f'{f} contains banned term: {term}')
        if any(ord(ch) >= 0x1F000 or ch in ('\u2753', '\u27a1', '\u2022', '\ufffd') for ch in txt):
            fails.append(f'{f} contains forbidden emoji or bullet character')

    # Local git identity check when origin points to justpeppe/just-develop.
    remote_url = subprocess.run(['git', '-C', R, 'remote', 'get-url', 'origin'], capture_output=True, text=True).stdout.strip()
    eff_email = subprocess.run(['git', '-C', R, 'config', '--get', 'user.email'], capture_output=True, text=True).stdout.strip()
    local_name = subprocess.run(['git', '-C', R, 'config', '--local', '--get', 'user.name'], capture_output=True, text=True).stdout.strip()

    leak_terms = []
    leak_file = os.path.join(os.path.expanduser('~'), '.just-develop-local', 'leak-terms.txt')
    if os.path.isfile(leak_file):
        for line in open(leak_file, encoding='utf-8'):
            s = line.strip()
            if s and not s.startswith('#'):
                leak_terms.append(s)

    corp_email_domain = '@' + 'xdev' + 'el.com'
    if eff_email and corp_email_domain in eff_email.lower():
        fails.append(f'git user.email uses corporate domain: {eff_email}')

    if 'justpeppe/just-develop' in remote_url and eff_email:
        if local_name == 'justpeppe' and eff_email != 'trimarchig2002@gmail.com':
            fails.append(f'git user.email mismatch for justpeppe: {eff_email}')
        if any(t.lower() in eff_email.lower() for t in leak_terms):
            fails.append(f'git user.email matches private leak-terms: {eff_email}')

    # Anti-leak scan over all non-binary active files (excluding .scratch/).
    path_leak_re = re.compile(r'C:[\\/]+(?:Users|Works|Delphi)[\\/]+', re.I)
    email_re = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
    sec_ext_re = re.compile(
        r'(?:^|[\s"\'\\/=:(*])(?:[A-Za-z0-9_.*-]*)\.(?:' + 'i' + 'ni|' + 'e' + r'nv)(?:\.[A-Za-z0-9_-]+)?(?=$|[\s"\'),;:\]`>])',
        re.I,
    )
    allowed_emails = {'trimarchig2002@gmail.com', 'noreply@anthropic.com'}
    safe_suffixes = ('.example', '.sample', '.template', '.dist')

    for f in active_files:
        if f.endswith(('.png', '.jpg', '.jpeg', '.ico', '.7z', '.zip')):
            continue
        txt = open(os.path.join(R, f), encoding='utf-8', errors='replace').read()
        if path_leak_re.search(txt):
            fails.append(f'anti-leak: private Windows root path in {f}')
        for em in email_re.findall(txt):
            if em.lower() in allowed_emails or '@example.' in em.lower():
                continue
            fails.append(f'anti-leak: unexpected email {em} in {f}')
        if f not in ('tests/run.py', 'SETUP.md'):
            for m in sec_ext_re.findall(txt):
                if any(m.lower().endswith(s) for s in safe_suffixes):
                    continue
                fails.append(f'anti-leak: literal secret extension in {f}: {m.strip()}')
        if leak_terms and f != 'tests/run.py':
            low = txt.lower()
            for term in leak_terms:
                if term.lower() in low:
                    fails.append(f'anti-leak: local blocked term {term!r} found in {f}')


def main():
    fails = []
    check_git_and_secret_guardrails(fails)
    check_sync_from_claude(fails)
    check_git_hooks(fails)
    check_pipe_lock_and_mergetree(fails)
    check_budgets_docs_and_antileak(fails)
    if os.path.exists(os.path.join(R, 'hooks', 'antigravity', 'block-dangerous-git.log')):
        fails.append('hooks/antigravity/block-dangerous-git.log must not exist in repo')
    print('\n'.join(fails) or 'ok')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
