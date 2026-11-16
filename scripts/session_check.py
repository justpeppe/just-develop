"""SessionStart hook: read cached update-state.json without network I/O and spawn detached background checks when stale."""
import argparse
import json
import os
import subprocess
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import background_checker as bg

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def is_subpath(child, parent):
    if not child or not parent:
        return False
    c = os.path.normcase(os.path.realpath(child))
    p = os.path.normcase(os.path.realpath(parent))
    return c == p or c.startswith(p + os.sep)


def spawn_background_check(mode, state_dir):
    worker = os.environ.get('JUST_DEVELOP_BG_WORKER') or os.path.join(SCRIPTS_DIR, 'background_checker.py')
    if not os.path.isfile(worker):
        return
    cmd = [sys.executable, '-X', 'utf8', '-I', worker, '--mode', mode, '--state-dir', state_dir]
    kwargs = {
        'stdin': subprocess.DEVNULL,
        'stdout': subprocess.DEVNULL,
        'stderr': subprocess.DEVNULL,
        'close_fds': True,
    }
    if os.name == 'nt':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs['start_new_session'] = True
    try:
        subprocess.Popen(cmd, **kwargs)
    except Exception:
        pass


def build_git_notices(git_state):
    if not isinstance(git_state, dict) or not git_state:
        return [], []
    status = git_state.get('status') or 'ok'
    behind = int(git_state.get('behind') or 0)
    main_behind = int(git_state.get('main_behind') or 0)
    def_branch = git_state.get('default_branch') or 'main'
    cur_branch = git_state.get('branch') or 'HEAD'
    conflict_kind = git_state.get('conflict_kind')
    conflict_files = git_state.get('conflict_files') or []
    changelog = git_state.get('changelog') or []
    sync_diffs = git_state.get('sync_diffs') or []
    case_collisions = git_state.get('case_collisions') or []
    sibling_overlaps = git_state.get('sibling_overlaps') or []

    user_lines = []
    agent_lines = []

    if behind > 0:
        user_lines.append(
            f"Aggiornamento disponibile per just-develop: '{cur_branch}' e' indietro di {behind} commit rispetto a origin/{def_branch}."
        )
        agent_lines.append(
            f"just-develop ha {behind} nuovi commit su origin/{def_branch}. Ricorda allo sviluppatore di eseguire manualmente il pull/merge nel terminale (gli agenti non eseguono pull/merge)."
        )
    elif main_behind > 0:
        user_lines.append(
            f"just-develop: il branch locale '{def_branch}' e' indietro di {main_behind} commit rispetto a origin/{def_branch}."
        )
        agent_lines.append(
            f"just-develop: il branch locale '{def_branch}' e' indietro di {main_behind} commit rispetto a origin/{def_branch}."
        )

    if conflict_kind:
        files_str = ', '.join(conflict_files[:6])
        if len(conflict_files) > 6:
            files_str += f" (+{len(conflict_files) - 6})"
        if conflict_kind == 'dirty_worktree':
            msg = f"Attenzione: modifiche locali non committate si sovrappongono ai file in arrivo ({files_str}). Fai commit o stash prima di aggiornare."
        elif conflict_kind == 'merge_tree':
            msg = f"Attenzione: rilevati possibili conflitti di merge con origin/{def_branch} su: {files_str}."
        else:
            msg = f"Attenzione: rilevati conflitti (modifiche locali e merge) con origin/{def_branch} su: {files_str}."
        user_lines.append(msg)
        agent_lines.append(msg)

    if status != 'ok' and changelog:
        summary_parts = []
        for grp in changelog[:4]:
            cat = grp.get('category') or 'Altro'
            items = grp.get('items') or []
            if items:
                summary_parts.append(f"- {cat}: {'; '.join(items[:3])}")
        if summary_parts:
            block = "Novita in arrivo:\n" + "\n".join(summary_parts)
            user_lines.append(block)
            agent_lines.append(block)

    if sync_diffs:
        diff_msg = f"Allineamento Claude/Antigravity da sincronizzare ({len(sync_diffs)} differenze). Esegui python -X utf8 -I scripts/sync-from-claude.py."
        user_lines.append(diff_msg)
        agent_lines.append(diff_msg)

    if case_collisions:
        pairs = '; '.join(' vs '.join(g) for g in case_collisions[:4] if isinstance(g, list))
        if pairs:
            cmsg = f"Attenzione: collisione maiuscole/minuscole tra branch remoti ({pairs})."
            user_lines.append(cmsg)
            agent_lines.append(cmsg)

    if sibling_overlaps:
        parts = []
        for ov in sibling_overlaps[:4]:
            if not isinstance(ov, dict):
                continue
            br = ov.get('branch') or '?'
            files = ov.get('conflict_files') or ov.get('overlap_files') or []
            parts.append(f"{br} ({', '.join(files[:3])})" if files else br)
        if parts:
            smsg = f"Attenzione: branch fratelli non ancora integrati toccano gli stessi file: {'; '.join(parts)}."
            user_lines.append(smsg)
            agent_lines.append(smsg)

    return user_lines, agent_lines


def build_asset_notices(assets_state, cwd):
    if not isinstance(assets_state, dict) or not assets_state:
        return [], []
    user_lines = []
    agent_lines = []

    skills = assets_state.get('skills') if isinstance(assets_state.get('skills'), dict) else {}
    upd_skills = [', '.join(v.get('names') or []) for v in skills.values() if isinstance(v, dict) and v.get('updated')]
    if upd_skills:
        line = f"Skill esterne aggiornabili ({'; '.join(upd_skills)}). Esegui `npx skills update`."
        user_lines.append(line)
        agent_lines.append(line)

    plugins = assets_state.get('plugins') if isinstance(assets_state.get('plugins'), dict) else {}
    upd_plugins = [k for k, v in sorted(plugins.items()) if isinstance(v, dict) and v.get('updated')]
    if upd_plugins:
        line = f"Plugin Claude aggiornabili: {', '.join(upd_plugins)}."
        user_lines.append(line)
        agent_lines.append(line)

    extra_repos = assets_state.get('extra_repos') if isinstance(assets_state.get('extra_repos'), dict) else {}
    for path, r in sorted(extra_repos.items()):
        if not isinstance(r, dict):
            continue
        behind = int(r.get('behind') or 0)
        if behind > 0:
            line = f"Repo {r.get('name') or path}: {behind} commit da integrare da origin/{r.get('default_branch') or 'main'}."
            user_lines.append(line)
            if is_subpath(cwd, path):
                agent_lines.append(line)

    return user_lines, agent_lines


def format_output(client, user_lines, agent_lines):
    user_msg = "\n".join(user_lines).strip()
    agent_ctx = "\n".join(agent_lines).strip()
    if not user_msg and not agent_ctx:
        return {}

    if client == 'antigravity':
        return {
            'injectSteps': [{
                'systemMessage': {
                    'systemMessage': agent_ctx or user_msg,
                    'metadata': {'user_markdown': user_msg or agent_ctx},
                }
            }]
        }

    out = {}
    if user_msg:
        out['systemMessage'] = user_msg
    if agent_ctx:
        out['hookSpecificOutput'] = {
            'hookEventName': 'SessionStart',
            'additionalContext': agent_ctx,
        }
    return out


def main():
    parser = argparse.ArgumentParser(description='Fast cache-only SessionStart hook.')
    parser.add_argument('--client', choices=('claude', 'antigravity'), default='claude')
    parser.add_argument('--state-dir', default=None)
    parser.add_argument('--clear-git', action='store_true')
    args = parser.parse_args()

    if args.clear_git:
        bg.clear_git_state(args.state_dir)
        return 0

    payload = {}
    try:
        if sys.stdin is not None and not sys.stdin.isatty():
            raw = sys.stdin.read()
            if raw and raw.strip():
                data = json.loads(raw)
                if isinstance(data, dict):
                    payload = data
    except Exception:
        payload = {}

    cwd = payload.get('cwd') or os.getcwd()
    state_dir = bg.resolve_state_dir(args.state_dir)
    repo_root = bg.resolve_repo_root()
    state = bg.read_json_safe(os.path.join(state_dir, 'update-state.json'))

    now = time.time()
    git_state = state.get('git') if isinstance(state.get('git'), dict) else {}
    assets_state = state.get('assets') if isinstance(state.get('assets'), dict) else {}

    need_git = (now - float(git_state.get('checked_at') or 0)) >= bg.GIT_TTL_SECONDS
    need_assets = (now - float(assets_state.get('checked_at') or 0)) >= bg.ASSETS_TTL_SECONDS
    if need_git and need_assets:
        spawn_background_check('all', state_dir)
    elif need_git:
        spawn_background_check('git', state_dir)
    elif need_assets:
        spawn_background_check('assets', state_dir)

    git_user, git_agent = build_git_notices(git_state)
    asset_user, asset_agent = build_asset_notices(assets_state, cwd)

    in_just_develop = is_subpath(cwd, repo_root)
    user_lines = git_user + asset_user
    agent_lines = (git_agent if in_just_develop else []) + asset_agent

    out = format_output(args.client, user_lines, agent_lines)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
