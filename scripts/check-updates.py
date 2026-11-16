"""Synchronous CLI update check for just-develop Git state, installed skills, plugins, and optional local repos."""
import argparse
import json
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import background_checker as bg

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def print_human_report(res):
    if res.get('locked'):
        print('Controllo gia in corso in background; letta la cache piu recente.')
    state = res.get('state') or {}
    git_s = state.get('git') or {}
    assets_s = state.get('assets') or {}

    print('=== just-develop (Git) ===')
    if git_s.get('status') in ('no_git', 'no_remote'):
        print(f"Stato: {git_s.get('status')}")
    elif git_s.get('status') == 'error':
        print(f"Errore: {git_s.get('error')}")
    else:
        print(
            f"Branch: {git_s.get('branch') or '?'} | "
            f"ahead={git_s.get('ahead', 0)} behind={git_s.get('behind', 0)} su origin/{git_s.get('default_branch') or 'main'} | "
            f"stato={git_s.get('status')}"
        )
        if git_s.get('main_behind', 0) > 0:
            print(f"Branch locale {git_s.get('default_branch')}: indietro di {git_s['main_behind']} commit")
        if git_s.get('conflict_kind'):
            print(f"Conflitti potenziali ({git_s['conflict_kind']}): {', '.join(git_s.get('conflict_files') or [])}")
        for grp in git_s.get('case_collisions') or []:
            print(f"Collisione maiuscole/minuscole su branch remoti: {' vs '.join(grp)}")
        for ov in git_s.get('sibling_overlaps') or []:
            files = ov.get('conflict_files') or ov.get('overlap_files') or []
            print(f"Sovrapposizione con branch fratello {ov.get('branch')}: {', '.join(files)}")
        for grp in git_s.get('changelog') or []:
            print(f"  - {grp['category']}: {'; '.join(grp['items'])}")
        for d in git_s.get('sync_diffs') or []:
            print(f"  [sync] {d}")
        if (git_s.get('behind') or 0) > 0:
            print("Azione manuale suggerita: esegui `git pull --rebase` o `git merge` nel terminale.")

    print('\n=== Skill esterne ===')
    skills = assets_s.get('skills') or {}
    if not skills:
        print('Nessuna skill tracciata trovata.')
    else:
        for url, entry in sorted(skills.items()):
            names = ', '.join(entry.get('names') or [])
            if entry.get('error'):
                print(f"  [errore] {names} ({url}): {entry['error']}")
            elif entry.get('updated'):
                print(f"  [aggiornabile] {names} ({url}) -> esegui `npx skills update`")
            else:
                print(f"  [ok] {names}")

    print('\n=== Plugin Claude ===')
    plugins = assets_s.get('plugins') or {}
    if not plugins:
        print('Nessun plugin abilitato tracciato.')
    else:
        for key, entry in sorted(plugins.items()):
            if entry.get('error'):
                print(f"  [errore] {key}: {entry['error']}")
            elif entry.get('updated'):
                print(f"  [aggiornabile] {key} ({entry.get('installed_version')} -> {entry.get('latest_version') or (entry.get('latest_sha') or '')[:8]})")
            else:
                print(f"  [ok] {key}")

    extra = assets_s.get('extra_repos') or {}
    if extra:
        print('\n=== Repo locali aggiuntivi ===')
        for path, r in sorted(extra.items()):
            if r.get('error'):
                print(f"  [errore] {r['name']} ({path}): {r['error']}")
            elif r.get('behind', 0) > 0:
                print(f"  [aggiornabile] {r['name']} ({path}): indietro di {r['behind']} su origin/{r['default_branch']}")
            else:
                print(f"  [ok] {r['name']} ({r['status']})")


def main():
    parser = argparse.ArgumentParser(description='Synchronous update check for just-develop and assets.')
    parser.add_argument('--state-dir', default=None)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    res = bg.run_check(mode='all', state_dir=args.state_dir)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print_human_report(res)
    return 0


if __name__ == '__main__':
    sys.exit(main())
