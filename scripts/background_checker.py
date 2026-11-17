"""Background update checker for just-develop Git state, installed skills, plugins, and optional local repos."""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

if os.name == 'nt':
    import msvcrt
else:
    import fcntl

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GIT_TTL_SECONDS = 8 * 3600
ASSETS_TTL_SECONDS = 24 * 3600
MAX_CHANGELOG_ITEMS = 30

CATEGORY_LABELS = {
    'hooks': 'Hook e sicurezze',
    'scripts': 'Script e controlli',
    'sync': 'Sincronizzazione',
    'flow': 'Flusso di lavoro',
    'skills': 'Skill',
    'docs': 'Documentazione',
    'tests': 'Test',
    'mcp': 'Configurazione MCP',
}
TYPE_LABELS = {
    'feat': 'Novita',
    'fix': 'Correzioni',
    'refactor': 'Pulizia interna',
    'docs': 'Documentazione',
    'test': 'Test',
    'chore': 'Manutenzione',
}
CONVENTIONAL_RE = re.compile(r'^(?P<type>[a-z]+)(?:\((?P<scope>[a-z0-9-]+)\))?:\s*(?P<desc>.+)$')


def resolve_state_dir(cli_state_dir=None):
    if cli_state_dir:
        return os.path.abspath(os.path.expanduser(cli_state_dir))
    env_dir = os.environ.get('JUST_DEVELOP_STATE_DIR')
    if env_dir:
        return os.path.abspath(os.path.expanduser(env_dir))
    return os.path.join(os.path.expanduser('~'), '.just-develop-local')


def resolve_repo_root():
    env_repo = os.environ.get('JUST_DEVELOP_REPO')
    if env_repo:
        return os.path.abspath(os.path.expanduser(env_repo))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_json_atomic(path, data):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    fd, tmp = tempfile.mkstemp(dir=parent, prefix='.tmp-', suffix='.json')
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


def read_json_safe(path):
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


class FileLock:
    """Non-blocking exclusive OS kernel lock compatible with Windows (msvcrt) and POSIX (fcntl)."""

    def __init__(self, path):
        self.path = path
        self.fd = None
        self.locked = False

    def acquire(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        self.fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            if os.name == 'nt':
                if os.fstat(self.fd).st_size == 0:
                    os.write(self.fd, b'\0')
                os.lseek(self.fd, 0, os.SEEK_SET)
                msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.locked = True
            return True
        except OSError:
            os.close(self.fd)
            self.fd = None
            return False

    def release(self):
        if self.fd is None:
            return
        try:
            if self.locked:
                if os.name == 'nt':
                    os.lseek(self.fd, 0, os.SEEK_SET)
                    msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self.fd, fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None
            self.locked = False


def run_git(args, cwd=None, timeout=15):
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GCM_INTERACTIVE'] = 'never'
    cmd = ['git'] + (['-C', cwd] if cwd else []) + args
    return subprocess.run(cmd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)


def git_supports_merge_tree_write_tree():
    try:
        p = run_git(['--version'], timeout=5)
        m = re.search(r'(\d+)\.(\d+)', p.stdout or '')
        if not m:
            return False
        return (int(m.group(1)), int(m.group(2))) >= (2, 38)
    except Exception:
        return False


def norm_path_ci(path):
    return os.path.normcase(path) if os.name == 'nt' else path


def parse_porcelain_dirty_paths(repo_root):
    p = run_git(['-c', 'core.quotepath=false', 'status', '--porcelain', '-z', '-uall', '--', ':(exclude).scratch'], cwd=repo_root, timeout=10)
    if p.returncode != 0 or not p.stdout:
        return set()
    tokens = p.stdout.split('\0')
    dirty = set()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        i += 1
        if not tok:
            continue
        if len(tok) >= 4 and tok[2] == ' ':
            xy = tok[:2]
            path = tok[3:].replace('\\', '/')
            if path:
                dirty.add(path)
            if ('R' in xy or 'C' in xy) and i < len(tokens):
                old_path = tokens[i].replace('\\', '/')
                if old_path:
                    dirty.add(old_path)
                i += 1
    return dirty


def parse_diff_names_z(repo_root, rev_range):
    p = run_git(['-c', 'core.quotepath=false', 'diff', '--name-only', '-z', rev_range], cwd=repo_root, timeout=10)
    if p.returncode != 0 or not p.stdout:
        return set()
    return {t.replace('\\', '/') for t in p.stdout.split('\0') if t}


def format_changelog(subjects):
    grouped = {}
    for subj in subjects:
        s = subj.strip()
        if not s:
            continue
        m = CONVENTIONAL_RE.match(s)
        if m:
            scope = m.group('scope') or ''
            ctype = m.group('type')
            desc = m.group('desc').strip()
            label = CATEGORY_LABELS.get(scope) or TYPE_LABELS.get(ctype) or (scope or 'Altro')
        else:
            label = 'Altro'
            desc = s
        grouped.setdefault(label, [])
        if desc not in grouped[label]:
            grouped[label].append(desc)
    return [{'category': k, 'items': v} for k, v in grouped.items()]


def find_default_remote_branch(repo_root):
    p = run_git(['for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin'], cwd=repo_root, timeout=5)
    if p.returncode != 0:
        return None, None
    refs = [r.strip() for r in p.stdout.splitlines() if r.strip() and r.strip().lower() != 'origin/head']
    by_lower = {r.lower(): r for r in refs}
    for cand in ('origin/main', 'origin/master'):
        if cand in by_lower:
            full = by_lower[cand]
            return full, full.split('/', 1)[1]
    sym = run_git(['symbolic-ref', '--short', '-q', 'refs/remotes/origin/HEAD'], cwd=repo_root, timeout=5)
    if sym.returncode == 0 and sym.stdout.strip():
        full = sym.stdout.strip()
        return full, full.split('/', 1)[1] if '/' in full else full
    return None, None


def find_local_branch_ci(repo_root, target_name):
    p = run_git(['for-each-ref', '--format=%(refname:short)', 'refs/heads'], cwd=repo_root, timeout=5)
    if p.returncode != 0:
        return None
    low = target_name.lower()
    for line in p.stdout.splitlines():
        name = line.strip()
        if name.lower() == low:
            return name
    return None


def parse_left_right_count(repo_root, left, right):
    p = run_git(['rev-list', '--left-right', '--count', f'{left}...{right}'], cwd=repo_root, timeout=5)
    if p.returncode != 0:
        return 0, 0
    parts = p.stdout.strip().split()
    if len(parts) != 2:
        return 0, 0
    return int(parts[0]), int(parts[1])


def check_sync_diffs(repo_root):
    sync_script = os.path.join(repo_root, 'scripts', 'sync-from-claude.py')
    if not os.path.isfile(sync_script):
        return []
    try:
        p = subprocess.run(
            [sys.executable, '-X', 'utf8', '-I', sync_script, '--check'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=15,
        )
        if p.returncode == 0:
            return []
        lines = [line.strip() for line in p.stdout.splitlines() if line.strip()]
        diffs = [line for line in lines if not line.startswith(('note:', 'checked:'))]
        return diffs or [f'sync-from-claude.py --check exit {p.returncode}']
    except Exception as exc:
        return [f'errore esecuzione sync-from-claude.py: {exc}']


def extract_merge_tree_conflicts(repo_root, left_ref, right_ref, exclude_scratch=False):
    mt = run_git(['-c', 'core.quotepath=false', 'merge-tree', '--write-tree', '--name-only', left_ref, right_ref], cwd=repo_root, timeout=15)
    if mt.returncode == 0:
        return []
    conflicts = []
    for line in mt.stdout.splitlines()[1:]:
        if line == '':
            break
        cpath = line.strip()
        if cpath and not (exclude_scratch and cpath.startswith('.scratch/')):
            conflicts.append(cpath)
    return conflicts


def find_remote_case_collisions(repo_root):
    by_lower = {}
    p = run_git(['for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin'], cwd=repo_root, timeout=5)
    if p.returncode == 0:
        for line in p.stdout.splitlines():
            ref = line.strip()
            if not ref or ref.lower() == 'origin/head':
                continue
            by_lower.setdefault(ref.lower(), set()).add(ref)
    ls = run_git(['ls-remote', '--heads', 'origin'], cwd=repo_root, timeout=10)
    if ls.returncode == 0:
        for line in ls.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1].startswith('refs/heads/'):
                ref = 'origin/' + parts[1][len('refs/heads/'):]
                by_lower.setdefault(ref.lower(), set()).add(ref)
    return [sorted(refs) for refs in sorted(by_lower.values(), key=lambda s: sorted(s)[0].lower()) if len(refs) > 1]


def find_sibling_overlaps(repo_root, remote_ref, dirty_paths, current_branch=''):
    p = run_git(['for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin'], cwd=repo_root, timeout=5)
    if p.returncode != 0:
        return []
    up = run_git(['rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'], cwd=repo_root, timeout=5)
    upstream_ref = up.stdout.strip() if up.returncode == 0 else ''
    self_remote_ref = f'origin/{current_branch}' if current_branch and current_branch != 'HEAD' else ''

    dirty_by_norm = {norm_path_ci(x): x for x in dirty_paths}
    head_paths = {x for x in parse_diff_names_z(repo_root, f'{remote_ref}...HEAD') if not x.startswith('.scratch/')}
    local_by_norm = dict(dirty_by_norm)
    for x in head_paths:
        local_by_norm.setdefault(norm_path_ci(x), x)

    use_merge_tree = git_supports_merge_tree_write_tree()
    overlaps = []
    for line in sorted(p.stdout.splitlines()):
        ref = line.strip()
        if not ref or ref == upstream_ref or ref == self_remote_ref or ref == remote_ref:
            continue
        if not ref.lower().startswith(('origin/feat/', 'origin/fix/', 'origin/refactor/', 'origin/docs/', 'origin/test/', 'origin/chore/')):
            continue
        anc = run_git(['merge-base', '--is-ancestor', ref, remote_ref], cwd=repo_root, timeout=5)
        if anc.returncode == 0:
            continue

        sib_paths = {x for x in parse_diff_names_z(repo_root, f'{remote_ref}...{ref}') if not x.startswith('.scratch/')}
        sib_by_norm = {norm_path_ci(x): x for x in sib_paths}
        overlap_files = sorted(local_by_norm[k] for k in (set(local_by_norm) & set(sib_by_norm)))

        if use_merge_tree:
            mt_conflicts = extract_merge_tree_conflicts(repo_root, 'HEAD', ref, exclude_scratch=True)
        else:
            mt_conflicts = sorted(sib_by_norm[k] for k in (set(sib_by_norm) & {norm_path_ci(x) for x in head_paths}))

        if overlap_files or mt_conflicts:
            overlaps.append({
                'branch': ref,
                'overlap_files': overlap_files,
                'conflict_files': sorted(set(mt_conflicts)),
            })
    return overlaps


def check_git_repo(repo_root):
    now = time.time()
    result = {
        'checked_at': now,
        'repo_root': repo_root,
        'status': 'ok',
        'branch': '',
        'default_branch': '',
        'ahead': 0,
        'behind': 0,
        'main_behind': 0,
        'conflict_kind': None,
        'conflict_files': [],
        'changelog': [],
        'sync_diffs': check_sync_diffs(repo_root),
        'case_collisions': [],
        'sibling_overlaps': [],
        'error': '',
    }
    if not os.path.isdir(os.path.join(repo_root, '.git')) and not os.path.isfile(os.path.join(repo_root, '.git')):
        result['status'] = 'no_git'
        return result

    try:
        rem = run_git(['remote'], cwd=repo_root, timeout=5)
        remotes = {r.strip() for r in rem.stdout.splitlines() if r.strip()}
        if 'origin' not in remotes:
            result['status'] = 'no_remote'
            return result

        fetch = run_git(['fetch', '--prune', 'origin', '--quiet'], cwd=repo_root, timeout=10)
        if fetch.returncode != 0:
            result['status'] = 'error'
            result['error'] = (fetch.stderr or fetch.stdout or 'git fetch failed').strip()
            return result

        br_p = run_git(['symbolic-ref', '--short', '-q', 'HEAD'], cwd=repo_root, timeout=5)
        branch = br_p.stdout.strip() if br_p.returncode == 0 else 'HEAD'
        result['branch'] = branch

        remote_ref, default_branch = find_default_remote_branch(repo_root)
        if not remote_ref:
            result['status'] = 'error'
            result['error'] = 'branch remoto principale non trovato su origin'
            return result
        result['default_branch'] = default_branch

        ahead, behind = parse_left_right_count(repo_root, 'HEAD', remote_ref)
        result['ahead'] = ahead
        result['behind'] = behind

        local_default = find_local_branch_ci(repo_root, default_branch)
        if local_default and local_default != branch:
            _, m_behind = parse_left_right_count(repo_root, local_default, remote_ref)
            result['main_behind'] = m_behind

        dirty_paths = parse_porcelain_dirty_paths(repo_root)
        result['case_collisions'] = find_remote_case_collisions(repo_root)
        result['sibling_overlaps'] = find_sibling_overlaps(repo_root, remote_ref, dirty_paths, branch)

        if behind > 0:
            log_p = run_git(['log', '--format=%s', f'HEAD..{remote_ref}', '-n', str(MAX_CHANGELOG_ITEMS)], cwd=repo_root, timeout=10)
            if log_p.returncode == 0:
                result['changelog'] = format_changelog(log_p.stdout.splitlines())

            incoming_paths = parse_diff_names_z(repo_root, f'HEAD...{remote_ref}')
            dirty_by_norm = {norm_path_ci(p): p for p in dirty_paths}
            incoming_by_norm = {norm_path_ci(p): p for p in incoming_paths}
            overlap = sorted(dirty_by_norm[k] for k in (set(dirty_by_norm) & set(incoming_by_norm)))

            if git_supports_merge_tree_write_tree():
                mt_conflicts = extract_merge_tree_conflicts(repo_root, 'HEAD', remote_ref)
            else:
                local_changed = parse_diff_names_z(repo_root, f'{remote_ref}...HEAD')
                mt_conflicts = sorted(norm_path_ci(p) for p in local_changed if norm_path_ci(p) in incoming_by_norm)

            if overlap and mt_conflicts:
                result['conflict_kind'] = 'dirty_worktree+merge_tree'
                result['conflict_files'] = sorted(set(overlap) | set(mt_conflicts))
            elif overlap:
                result['conflict_kind'] = 'dirty_worktree'
                result['conflict_files'] = overlap
            elif mt_conflicts:
                result['conflict_kind'] = 'merge_tree'
                result['conflict_files'] = sorted(set(mt_conflicts))

        if result['conflict_kind']:
            result['status'] = 'conflict'
        elif behind > 0 and ahead > 0:
            result['status'] = 'diverged'
        elif behind > 0:
            result['status'] = 'behind'
        elif ahead > 0:
            result['status'] = 'ahead'
        else:
            result['status'] = 'ok'
    except Exception as exc:
        result['status'] = 'error'
        result['error'] = str(exc)
    return result


def check_skills_updates(prev_skills):
    home = os.path.expanduser('~')
    lock_path = os.path.join(home, '.agents', '.skill-lock.json')
    skills_dir = os.path.join(home, '.agents', 'skills')
    lock_data = read_json_safe(lock_path)
    lock_skills = lock_data.get('skills') if isinstance(lock_data.get('skills'), dict) else {}

    existing = set()
    if os.path.isdir(skills_dir):
        for name in os.listdir(skills_dir):
            full = os.path.join(skills_dir, name)
            if os.path.exists(full):
                existing.add(name)

    by_url = {}
    for name, info in sorted(lock_skills.items()):
        if name not in existing or not isinstance(info, dict):
            continue
        url = (info.get('sourceUrl') or '').strip()
        if not url:
            continue
        bucket = by_url.setdefault(url, {'names': [], 'lock_hashes': {}})
        bucket['names'].append(name)
        bucket['lock_hashes'][name] = info.get('skillFolderHash') or ''

    out = {}
    for url, meta in sorted(by_url.items()):
        prev = prev_skills.get(url) if isinstance(prev_skills.get(url), dict) else {}
        prev_head = prev.get('head')
        prev_hashes = prev.get('lock_hashes') if isinstance(prev.get('lock_hashes'), dict) else {}
        entry = {
            'names': sorted(meta['names']),
            'lock_hashes': meta['lock_hashes'],
            'head': prev_head,
            'remote_head': None,
            'updated': False,
            'error': '',
        }
        try:
            p = run_git(['ls-remote', url, 'HEAD'], timeout=15)
            if p.returncode != 0:
                entry['error'] = (p.stderr or p.stdout or f'git ls-remote exit {p.returncode}').strip()
            else:
                first_line = (p.stdout.strip().splitlines() or [''])[0]
                remote_head = first_line.split()[0] if first_line.split() else ''
                entry['remote_head'] = remote_head or None
                if remote_head:
                    if not prev_head or meta['lock_hashes'] != prev_hashes:
                        entry['head'] = remote_head
                        entry['updated'] = False
                    else:
                        entry['head'] = prev_head
                        entry['updated'] = (remote_head != prev_head)
        except Exception as exc:
            entry['error'] = str(exc)
        out[url] = entry
    return out


def check_plugins_updates():
    home = os.path.expanduser('~')
    claude_dir = os.path.join(home, '.claude')
    settings = read_json_safe(os.path.join(claude_dir, 'settings.json'))
    enabled_map = settings.get('enabledPlugins') if isinstance(settings.get('enabledPlugins'), dict) else {}

    installed_path = os.path.join(claude_dir, 'plugins', 'installed_plugins.json')
    installed_data = read_json_safe(installed_path)
    plugins_map = installed_data.get('plugins') if isinstance(installed_data.get('plugins'), dict) else {}
    marketplaces_dir = os.path.join(claude_dir, 'plugins', 'marketplaces')

    mkt_cache = {}
    out = {}
    for key, entries in sorted(plugins_map.items()):
        if enabled_map.get(key) is False:
            continue
        if isinstance(entries, list):
            rec = next((e for e in entries if isinstance(e, dict)), None)
        elif isinstance(entries, dict):
            rec = entries
        else:
            rec = None
        if not rec or '@' not in key:
            continue
        plugin_name, mkt_name = key.split('@', 1)
        mkt_dir = os.path.join(marketplaces_dir, mkt_name)
        if not os.path.isdir(mkt_dir):
            continue

        if mkt_name not in mkt_cache:
            mkt_info = {'remote_ref': None, 'remote_sha': None, 'manifest': {}, 'error': ''}
            try:
                rem = run_git(['remote'], cwd=mkt_dir, timeout=5)
                if 'origin' in {r.strip() for r in rem.stdout.splitlines() if r.strip()}:
                    f = run_git(['fetch', '--quiet'], cwd=mkt_dir, timeout=20)
                    if f.returncode == 0:
                        rref, _ = find_default_remote_branch(mkt_dir)
                        mkt_info['remote_ref'] = rref
                        if rref:
                            sha_p = run_git(['rev-parse', rref], cwd=mkt_dir, timeout=5)
                            if sha_p.returncode == 0:
                                mkt_info['remote_sha'] = sha_p.stdout.strip()
                            show_p = run_git(['show', f'{rref}:.claude-plugin/marketplace.json'], cwd=mkt_dir, timeout=5)
                            if show_p.returncode == 0:
                                try:
                                    manifest = json.loads(show_p.stdout)
                                    for mp in (manifest.get('plugins') or []):
                                        if isinstance(mp, dict) and mp.get('name'):
                                            mkt_info['manifest'][mp['name']] = mp
                                except Exception:
                                    pass
                    else:
                        mkt_info['error'] = (f.stderr or 'fetch failed').strip()
            except Exception as exc:
                mkt_info['error'] = str(exc)
            mkt_cache[mkt_name] = mkt_info

        mkt_info = mkt_cache[mkt_name]
        inst_ver = rec.get('version') or ''
        inst_sha = rec.get('gitCommitSha') or ''
        remote_mp = mkt_info['manifest'].get(plugin_name) or {}
        latest_ver = remote_mp.get('version') or ''
        latest_sha = mkt_info['remote_sha'] or ''

        updated = False
        if latest_ver and inst_ver and latest_ver != inst_ver:
            updated = True
        elif not latest_ver and latest_sha and inst_sha and latest_sha != inst_sha:
            updated = True

        out[key] = {
            'name': plugin_name,
            'marketplace': mkt_name,
            'installed_version': inst_ver,
            'installed_sha': inst_sha,
            'latest_version': latest_ver,
            'latest_sha': latest_sha,
            'updated': updated,
            'error': mkt_info['error'],
        }
    return out


def check_extra_repos(state_dir):
    cfg = read_json_safe(os.path.join(state_dir, 'update-config.json'))
    repos = cfg.get('extra_repos') if isinstance(cfg.get('extra_repos'), list) else []
    out = {}
    for item in repos:
        if isinstance(item, str):
            path = os.path.abspath(os.path.expanduser(item))
            name = os.path.basename(path)
        elif isinstance(item, dict) and item.get('path'):
            path = os.path.abspath(os.path.expanduser(item['path']))
            name = item.get('name') or os.path.basename(path)
        else:
            continue
        entry = {'name': name, 'path': path, 'behind': 0, 'ahead': 0, 'default_branch': '', 'status': 'ok', 'error': ''}
        if not os.path.isdir(path):
            entry['status'] = 'missing'
            out[path] = entry
            continue
        try:
            rem = run_git(['remote'], cwd=path, timeout=5)
            if 'origin' not in {r.strip() for r in rem.stdout.splitlines() if r.strip()}:
                entry['status'] = 'no_remote'
                out[path] = entry
                continue
            f = run_git(['fetch', '--prune', '--quiet'], cwd=path, timeout=20)
            if f.returncode != 0:
                entry['status'] = 'error'
                entry['error'] = (f.stderr or 'fetch failed').strip()
                out[path] = entry
                continue
            rref, def_br = find_default_remote_branch(path)
            if not rref:
                entry['status'] = 'error'
                entry['error'] = 'branch remoto principale non trovato'
                out[path] = entry
                continue
            ahead, behind = parse_left_right_count(path, 'HEAD', rref)
            entry['ahead'] = ahead
            entry['behind'] = behind
            entry['default_branch'] = def_br
            entry['status'] = 'behind' if behind > 0 else ('ahead' if ahead > 0 else 'ok')
        except Exception as exc:
            entry['status'] = 'error'
            entry['error'] = str(exc)
        out[path] = entry
    return out


def check_assets(prev_assets, state_dir):
    prev_skills = prev_assets.get('skills') if isinstance(prev_assets.get('skills'), dict) else {}
    skills = check_skills_updates(prev_skills)
    plugins = check_plugins_updates()
    extra_repos = check_extra_repos(state_dir)

    summary = []
    for url, s in sorted(skills.items()):
        if s.get('updated'):
            summary.append(f"Skill aggiornabili ({', '.join(s['names'])}) da {url}")
    for key, p in sorted(plugins.items()):
        if p.get('updated'):
            ver = p.get('latest_version') or (p.get('latest_sha') or '')[:8]
            summary.append(f"Plugin aggiornabile: {key} -> {ver}")
    for path, r in sorted(extra_repos.items()):
        if r.get('behind', 0) > 0:
            summary.append(f"Repo locale {r['name']}: {r['behind']} commit da integrare su origin/{r['default_branch']}")

    return {
        'checked_at': time.time(),
        'skills': skills,
        'plugins': plugins,
        'extra_repos': extra_repos,
        'updates_summary': summary,
    }


def clear_git_state(state_dir=None):
    sdir = resolve_state_dir(state_dir)
    state_path = os.path.join(sdir, 'update-state.json')
    lock_path = os.path.join(sdir, 'update.lock')
    flag_path = os.path.join(sdir, 'clear-git.flag')
    if not os.path.isfile(state_path) and not os.path.isfile(lock_path):
        return {}

    lock = FileLock(lock_path)
    acquired = lock.acquire()
    if not acquired:
        deadline = time.time() + 1.5
        while time.time() < deadline:
            time.sleep(0.05)
            acquired = lock.acquire()
            if acquired:
                break
    if not acquired:
        os.makedirs(sdir, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=sdir, prefix='.tmp-', suffix='.flag')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(str(time.time()))
            os.replace(tmp, flag_path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        return read_json_safe(state_path) if os.path.isfile(state_path) else {}

    try:
        try:
            os.unlink(flag_path)
        except OSError:
            pass
        if not os.path.isfile(state_path):
            return {}
        state = read_json_safe(state_path)
        state['schema_version'] = 1
        state['git'] = {}
        write_json_atomic(state_path, state)
        return state
    finally:
        lock.release()


def run_check(mode='auto', state_dir=None, repo_root=None):
    sdir = resolve_state_dir(state_dir)
    repo = os.path.abspath(repo_root) if repo_root else resolve_repo_root()
    state_path = os.path.join(sdir, 'update-state.json')
    flag_path = os.path.join(sdir, 'clear-git.flag')
    lock = FileLock(os.path.join(sdir, 'update.lock'))

    if not lock.acquire():
        return {'locked': True, 'state': read_json_safe(state_path)}

    try:
        state = read_json_safe(state_path)
        state['schema_version'] = 1
        now = time.time()

        prev_git = state.get('git') if isinstance(state.get('git'), dict) else {}
        prev_assets = state.get('assets') if isinstance(state.get('assets'), dict) else {}

        do_git = mode in ('git', 'all') or (mode == 'auto' and (now - float(prev_git.get('checked_at') or 0)) >= GIT_TTL_SECONDS)
        do_assets = mode in ('assets', 'all') or (mode == 'auto' and (now - float(prev_assets.get('checked_at') or 0)) >= ASSETS_TTL_SECONDS)

        git_started_at = time.time()
        if do_git:
            state['git'] = check_git_repo(repo)
        if do_assets:
            state['assets'] = check_assets(prev_assets, sdir)

        if os.path.isfile(flag_path):
            try:
                flag_ts = float(open(flag_path, encoding='utf-8').read().strip() or '0')
            except Exception:
                flag_ts = time.time()
            try:
                os.unlink(flag_path)
            except OSError:
                pass
            if not do_git or flag_ts >= git_started_at:
                state['git'] = {}
                write_json_atomic(state_path, state)

        if do_git or do_assets:
            write_json_atomic(state_path, state)
        return {'locked': False, 'state': state}
    finally:
        lock.release()


def main():
    parser = argparse.ArgumentParser(description='Background update checker for just-develop.')
    parser.add_argument('--mode', choices=('auto', 'git', 'assets', 'all'), default='auto')
    parser.add_argument('--state-dir', default=None)
    parser.add_argument('--clear-git', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    if args.clear_git:
        state = clear_git_state(args.state_dir)
        if args.json:
            print(json.dumps(state, ensure_ascii=False))
        return 0

    res = run_check(mode=args.mode, state_dir=args.state_dir)
    if args.json:
        print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
