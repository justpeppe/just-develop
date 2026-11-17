"""Extract a compact, secret-redacted retrospective and v2 debt digest from Claude Code and Antigravity transcripts."""
import argparse
from collections import Counter
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MAX_EXCERPT_LEN = 260
MAX_OPENERS = 12
MAX_CORRECTIONS = 35
MAX_ERRORS = 25

CLAUDE_WANT_RE = re.compile(r'"type"\s*:\s*"(?:user|assistant|system)"')
CORRECTION_RE = re.compile(
    r'\b(no|non|ferma|fermati|sbagliat\w*|errore|avevo detto|perch[eé] hai|invece di|'
    r'non toccare|annulla|revert|wrong|stop|why did you|don\'t|broke|broken)\b',
    re.I,
)
SECRET_PATTERNS = (
    re.compile(r'\bBearer\s+[A-Za-z0-9._\-+/=]{8,}', re.I),
    re.compile(r'\bBasic\s+[A-Za-z0-9+/=]{8,}', re.I),
    re.compile(r'\bsk-[A-Za-z0-9_-]{10,}'),
    re.compile(r'\bgh[pousr]_[A-Za-z0-9_]{10,}'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{10,}'),
    re.compile(r'\bAIza[A-Za-z0-9_-]{20,}'),
    re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}'),
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
)
URL_CRED_RE = re.compile(r'([A-Za-z][A-Za-z0-9+.-]*://[^:\s/@"\']+:)([^@\s"\']+)(@)')
KV_SECRET_RE = re.compile(
    r'(?i)(^|[^A-Za-z0-9_])([A-Za-z0-9_-]*(?:password|passwd|secret|api[_-]?key|token|auth))\s*([:=])\s*[\'"]?([^\s\'",;]{4,})[\'"]?'
)
SYS_BLOCK_RE = re.compile(r'<(?:system-reminder|command-message|command-name)>[\s\S]*?</(?:system-reminder|command-message|command-name)>', re.I)
USER_REQ_RE = re.compile(r'<USER_REQUEST>\s*([\s\S]*?)\s*</USER_REQUEST>')
META_BLOCK_RE = re.compile(r'<(?:CONTEXT_SUMMARY|ADDITIONAL_METADATA)>[\s\S]*?</(?:CONTEXT_SUMMARY|ADDITIONAL_METADATA)>')
AGY_ERR_PREFIX_RE = re.compile(r'^(?:Created At:[^\n]*\n|Completed At:[^\n]*\n)+')
STATUS_RE = re.compile(r'^(?:\*\*)?Status:(?:\*\*)?\s*(.+?)\s*$', re.I | re.M)
LINE_REF_RE = re.compile(
    r'(?:(?<!://)\b[A-Za-z0-9_./-]+\.(?:pas|py|js|html|css|mdx?):L?\d+\b|#L\d+(?:-L?\d+)?|\brighe\s+\d+\.\.\S+|\blines?\s+\d+[-–]\d+\b)',
    re.I,
)
CLOSED_STATUSES = {'resolved', 'wontfix', 'closed', 'done'}
TICKET_REQUIRED_HEADERS = ('Review:', 'Esecutore:')


def redact(text):
    """Collapse whitespace, mask likely credentials, and cap excerpt length."""
    s = str(text or '')
    for pat in SECRET_PATTERNS:
        s = pat.sub('[REDACTED]', s)
    s = URL_CRED_RE.sub(r'\1[REDACTED]\3', s)
    s = KV_SECRET_RE.sub(lambda m: f'{m.group(1)}{m.group(2)}{m.group(3)}[REDACTED]', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) > MAX_EXCERPT_LEN:
        return s[: MAX_EXCERPT_LEN - 3].rstrip() + '...'
    return s


def write_text_atomic(path, text):
    """Write UTF-8 text via temp file and os.replace so partial writes never corrupt the output."""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix='.tmp-', suffix='.md')
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


def is_within_root(path, real_root):
    """Verify realpath of path resolves strictly inside real_root."""
    try:
        resolved = os.path.realpath(path)
    except OSError:
        return False
    norm_root = os.path.normcase(real_root)
    norm_res = os.path.normcase(resolved)
    return norm_res == norm_root or norm_res.startswith(norm_root + os.sep)


def read_text_safe(path):
    """Read UTF-8 file using context manager, returning empty string on error."""
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return ''


def parse_status_token(text):
    """Return (status_value, first_token) from a Markdown Status header."""
    m = STATUS_RE.search(text or '')
    if not m:
        return '', ''
    stat_val = m.group(1).strip().lower()
    token = re.split(r'[\s(\[:]+', stat_val)[0] if stat_val else ''
    return stat_val, token


def is_closed_status(text):
    """Return True when Markdown text has a Status header in CLOSED_STATUSES."""
    _, token = parse_status_token(text)
    return token in CLOSED_STATUSES


def find_line_refs(text, skip_closed=True):
    """Return static line references in text, or [] when skip_closed=True and ticket is closed."""
    if skip_closed and is_closed_status(text):
        return []
    return LINE_REF_RE.findall(text or '')


def read_repo_text(real_root, rel_path, staged=False):
    """Read UTF-8 text from the Git index (staged=True) or safely from disk inside real_root."""
    rel_posix = rel_path.replace('\\', '/').lstrip('./')
    if staged:
        res = subprocess.run(
            ['git', '-C', real_root, 'show', f':{rel_posix}'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
        return res.stdout if res.returncode == 0 else ''
    full = os.path.join(real_root, rel_posix)
    if not (os.path.isfile(full) and is_within_root(full, real_root)):
        return ''
    return read_text_safe(full)


def scan_line_refs(repo_root, paths=None, staged=False, skip_closed=True):
    """Scan staged or disk markdown files for static line references using LINE_REF_RE and CLOSED_STATUSES."""
    real_root = os.path.realpath(os.path.abspath(repo_root))
    if paths is None:
        if staged:
            res = subprocess.run(
                ['git', '-C', real_root, 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
            )
            candidates = [p.strip() for p in res.stdout.splitlines() if p.strip()] if res.returncode == 0 else []
        else:
            candidates = []
            for fname in ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'CODING_STANDARDS.md', 'GLOSSARY.md'):
                if os.path.isfile(os.path.join(real_root, fname)):
                    candidates.append(fname)
            for sub in ('.scratch', 'docs'):
                sdir = os.path.join(real_root, sub)
                if os.path.isdir(sdir):
                    for dp in sorted(glob.glob(os.path.join(sdir, '**', '*.md*'), recursive=True)):
                        if os.path.isfile(dp) and is_within_root(dp, real_root):
                            candidates.append(os.path.relpath(dp, real_root).replace('\\', '/'))
    else:
        candidates = list(paths)

    findings = []
    for raw_p in candidates:
        rel = raw_p.replace('\\', '/').lstrip('./')
        if not rel.lower().endswith(('.md', '.mdx')):
            continue
        if rel.endswith('_retro-digest.md') or rel.startswith('docs/agents/'):
            continue
        txt = read_repo_text(real_root, rel, staged=staged)
        if not txt:
            continue
        hits = find_line_refs(txt, skip_closed=skip_closed)
        if hits:
            findings.append((rel, hits))
    return findings


def push_unique(bucket, seen, text, cap):
    """Append redacted non-empty text up to cap while deduplicating by normalized prefix."""
    clean = redact(text)
    if not clean:
        return
    key = clean[:120].lower()
    if key in seen or len(bucket) >= cap:
        return
    seen.add(key)
    bucket.append(clean)


def record_user_turn(text, session_state, stats):
    """Count a real user turn and record opener plus correction cues."""
    clean = redact(text)
    if not clean:
        return
    stats['user_turns'] += 1
    if not session_state['opener_done']:
        session_state['opener_done'] = True
        push_unique(stats['openers'], stats['opener_seen'], clean, MAX_OPENERS)
    if CORRECTION_RE.search(clean):
        push_unique(stats['corrections'], stats['correction_seen'], clean, MAX_CORRECTIONS)


def extract_claude_text(content):
    """Extract plain user text from Claude message content, stripping injected system tags."""
    if isinstance(content, str):
        return SYS_BLOCK_RE.sub('', content).strip()
    if isinstance(content, list):
        parts = []
        for blk in content:
            if isinstance(blk, dict) and blk.get('type') == 'text':
                parts.append(SYS_BLOCK_RE.sub('', blk.get('text') or ''))
        return ' '.join(p.strip() for p in parts if p.strip())
    return ''


def scan_claude_file(jsonl_path, is_subagent, stats):
    """Stream one Claude Code JSONL transcript skipping heavy attachment/API noise."""
    if is_subagent:
        stats['claude_subagents'] += 1
    else:
        stats['claude_sessions'] += 1
    stats['claude_bytes'] += os.path.getsize(jsonl_path)
    session_state = {'opener_done': False}

    with open(jsonl_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if not CLAUDE_WANT_RE.search(line):
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            etype = obj.get('type')
            if etype == 'user' and not obj.get('isSidechain') and not obj.get('isMeta'):
                content = (obj.get('message') or {}).get('content')
                if isinstance(content, list):
                    for blk in content:
                        if isinstance(blk, dict) and blk.get('type') == 'tool_result' and blk.get('is_error'):
                            push_unique(stats['errors'], stats['error_seen'], blk.get('content'), MAX_ERRORS)
                txt = extract_claude_text(content)
                if txt:
                    record_user_turn(txt, session_state, stats)
            elif etype == 'assistant':
                content = (obj.get('message') or {}).get('content')
                if isinstance(content, list):
                    for blk in content:
                        if not isinstance(blk, dict) or blk.get('type') != 'tool_use':
                            continue
                        tname = blk.get('name') or ''
                        if tname:
                            stats['tools'][tname] += 1
                        if tname == 'Skill':
                            sk = (blk.get('input') or {}).get('skill')
                            if sk:
                                stats['skills'][str(sk)] += 1
                        elif tname.startswith('mcp__'):
                            stats['mcps'][tname] += 1
            elif etype == 'system':
                for herr in obj.get('hookErrors') or []:
                    push_unique(stats['errors'], stats['error_seen'], f'hookError: {herr}', MAX_ERRORS)
                if obj.get('preventedContinuation'):
                    push_unique(stats['errors'], stats['error_seen'], f"preventedContinuation: {obj.get('stopReason')}", MAX_ERRORS)


def scan_claude_projects(real_target, claude_dir, cutoff_ts, stats):
    """Find matching Claude Code project directories and collect memories and recent transcripts."""
    if not os.path.isdir(claude_dir):
        return
    slug_exact = re.sub(r'[^A-Za-z0-9-]', '-', real_target).lower()
    slug_collapsed = re.sub(r'[^A-Za-z0-9-]+', '-', real_target).lower()

    for name in sorted(os.listdir(claude_dir)):
        pdir = os.path.join(claude_dir, name)
        if not os.path.isdir(pdir) or name.lower() not in (slug_exact, slug_collapsed):
            continue
        mem_dir = os.path.join(pdir, 'memory')
        if os.path.isdir(mem_dir):
            for mfile in sorted(os.listdir(mem_dir)):
                full_m = os.path.join(mem_dir, mfile)
                if mfile.endswith('.md') and os.path.isfile(full_m):
                    stats['claude_memories'].append((mfile, os.path.getsize(full_m)))

        main_files = sorted(glob.glob(os.path.join(pdir, '*.jsonl')))
        sub_files = sorted(glob.glob(os.path.join(pdir, '*', 'subagents', '*.jsonl')))
        for is_sub, jf in [(False, p) for p in main_files] + [(True, p) for p in sub_files]:
            if os.path.isfile(jf) and (not cutoff_ts or os.path.getmtime(jf) >= cutoff_ts):
                scan_claude_file(jf, is_sub, stats)


def build_target_needle_re(real_target):
    """Build boundary-aware regex matching real_target across Windows JSON double-escaping, WSL, and URI forms."""
    posix = real_target.replace('\\', '/')
    escaped_once = real_target.replace('\\', '\\\\')
    # Antigravity PLANNER_RESPONSE stores JSON-serialized arg strings inside JSONL, doubling backslashes twice.
    escaped_twice = real_target.replace('\\', '\\\\\\\\')
    quoted = urllib.parse.quote(posix, safe='/:').replace(':', '%3A')
    candidates = {real_target, posix, escaped_once, escaped_twice, quoted, quoted.replace('%3A', '%3a')}
    if len(posix) >= 3 and posix[1] == ':' and posix[0].isalpha():
        candidates.add(f'/mnt/{posix[0].lower()}{posix[2:]}')
    ordered = sorted((c for c in candidates if len(c) > 2), key=len, reverse=True)
    return re.compile(r'(?:' + '|'.join(re.escape(c) for c in ordered) + r')(?=$|[^A-Za-z0-9_.-])', re.I)


def extract_agy_user_text(content):
    """Extract clean user prompt from Antigravity USER_INPUT without context summaries."""
    s = str(content or '')
    m = USER_REQ_RE.search(s)
    if m:
        return m.group(1).strip()
    return META_BLOCK_RE.sub('', s).strip()


def merge_agy_session(local, stats):
    """Fold a verified Antigravity conversation's metrics into global stats."""
    stats['agy_sessions'] += 1
    stats['agy_bytes'] += local['bytes']
    stats['user_turns'] += local['user_turns']
    stats['tools'].update(local['tools'])
    stats['skills'].update(local['skills'])
    stats['mcps'].update(local['mcps'])
    for item in local['openers']:
        push_unique(stats['openers'], stats['opener_seen'], item, MAX_OPENERS)
    for item in local['corrections']:
        push_unique(stats['corrections'], stats['correction_seen'], item, MAX_CORRECTIONS)
    for item in local['errors']:
        push_unique(stats['errors'], stats['error_seen'], item, MAX_ERRORS)


def scan_agy_conversation(tr_path, needle_re, stats):
    """Single-pass parse of an Antigravity transcript; only merges if USER_INPUT or PLANNER_RESPONSE references target."""
    local = {
        'bytes': os.path.getsize(tr_path),
        'user_turns': 0,
        'tools': Counter(),
        'skills': Counter(),
        'mcps': Counter(),
        'openers': [],
        'opener_seen': set(),
        'corrections': [],
        'correction_seen': set(),
        'errors': [],
        'error_seen': set(),
    }
    session_state = {'opener_done': False}
    matched = False

    with open(tr_path, encoding='utf-8', errors='replace') as f:
        for raw_line in f:
            is_user_or_plan = '"USER_INPUT"' in raw_line or '"PLANNER_RESPONSE"' in raw_line
            is_err_line = '"ERROR"' in raw_line or '"ERROR_MESSAGE"' in raw_line
            if not is_user_or_plan and not is_err_line:
                continue
            if is_user_or_plan and not matched and needle_re.search(raw_line):
                matched = True
            try:
                obj = json.loads(raw_line)
            except Exception:
                continue
            stype = obj.get('type')
            status = obj.get('status')
            if stype == 'USER_INPUT':
                txt = extract_agy_user_text(obj.get('content'))
                if txt:
                    record_user_turn(txt, session_state, {
                        'user_turns': 0, 'openers': local['openers'], 'opener_seen': local['opener_seen'],
                        'corrections': local['corrections'], 'correction_seen': local['correction_seen'],
                    })
                    local['user_turns'] += 1
            elif stype == 'PLANNER_RESPONSE':
                for tc in obj.get('tool_calls') or []:
                    tname = tc.get('name') or ''
                    args = tc.get('args') or {}
                    if tname:
                        local['tools'][tname] += 1
                    if tname == 'call_mcp_tool' and isinstance(args, dict):
                        srv = str(args.get('ServerName') or '').strip('"')
                        tool = str(args.get('ToolName') or '').strip('"')
                        local['mcps'][f'{srv}:{tool}'] += 1
                    elif tname in ('read_file', 'view_file') and isinstance(args, dict):
                        pval = str(args.get('Path') or args.get('AbsolutePath') or '').strip('"').replace('\\', '/')
                        if pval.lower().endswith('/skill.md'):
                            parts = [p for p in pval.split('/') if p]
                            if len(parts) >= 2 and parts[-2].lower() != 'skills':
                                local['skills'][parts[-2]] += 1
            elif status == 'ERROR' or stype == 'ERROR_MESSAGE':
                raw_err = obj.get('error') or AGY_ERR_PREFIX_RE.sub('', str(obj.get('content') or '')).strip()
                push_unique(local['errors'], local['error_seen'], raw_err, MAX_ERRORS)

    if matched:
        merge_agy_session(local, stats)


def scan_agy_brains(real_target, agy_dirs, cutoff_ts, stats):
    """Scan matching Antigravity conversation transcripts and local knowledge topics across client directories."""
    needle_re = build_target_needle_re(real_target)
    seen_convs = set()
    seen_knowledge = set()

    for brain_dir in agy_dirs:
        if not os.path.isdir(brain_dir):
            continue

        know_dir = os.path.join(os.path.dirname(brain_dir), 'knowledge')
        if os.path.isdir(know_dir):
            for topic in sorted(os.listdir(know_dir)):
                if os.path.isdir(os.path.join(know_dir, topic)) and topic not in seen_knowledge:
                    seen_knowledge.add(topic)
                    stats['agy_knowledge'].append(topic)

        for tr in sorted(glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript.jsonl'))):
            conv_id = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(tr))))
            if conv_id in seen_convs or not os.path.isfile(tr):
                continue
            seen_convs.add(conv_id)
            if not cutoff_ts or os.path.getmtime(tr) >= cutoff_ts:
                scan_agy_conversation(tr, needle_re, stats)


def collect_repo_v2_debt(real_target):
    """Inspect root agent files, open .scratch tickets, and docs/ for static line numbers and missing v2 fields."""
    debt = {
        'has_risk': False,
        'has_checks': False,
        'root_refs': [],
        'open_items': [],
        'closed_count': 0,
        'docs_total': 0,
        'docs_with_refs': 0,
    }

    for fname in ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'CODING_STANDARDS.md', 'GLOSSARY.md'):
        p = os.path.join(real_target, fname)
        if not (os.path.isfile(p) and is_within_root(p, real_target)):
            continue
        txt = read_text_safe(p)
        if fname == 'AGENTS.md':
            low = txt.lower()
            debt['has_risk'] = 'aree a rischio' in low
            debt['has_checks'] = 'verifiche' in low
        hits = find_line_refs(txt, skip_closed=False)
        if hits:
            debt['root_refs'].append((fname, len(hits), hits[:4]))

    scratch_dir = os.path.join(real_target, '.scratch')
    if os.path.isdir(scratch_dir):
        for md in sorted(glob.glob(os.path.join(scratch_dir, '**', '*.md'), recursive=True)):
            if not (os.path.isfile(md) and is_within_root(md, real_target)):
                continue
            rel = os.path.relpath(md, real_target).replace('\\', '/')
            if rel.endswith('_retro-digest.md'):
                continue
            txt = read_text_safe(md)
            stat_val, stat_token = parse_status_token(txt)
            if stat_token in CLOSED_STATUSES:
                debt['closed_count'] += 1
                continue
            is_spec_or_issue = rel.endswith('/spec.md') or '/issues/' in rel
            if not (is_spec_or_issue or stat_val):
                continue
            lrefs = find_line_refs(txt, skip_closed=False)
            missing = []
            if '/issues/' in rel:
                for hdr in TICKET_REQUIRED_HEADERS:
                    if hdr not in txt:
                        missing.append(hdr.rstrip(':'))
            if lrefs or missing or stat_val:
                debt['open_items'].append((rel, stat_val or 'no-status', len(lrefs), missing))

    docs_dir = os.path.join(real_target, 'docs')
    if os.path.isdir(docs_dir):
        for dp in sorted(glob.glob(os.path.join(docs_dir, '**', '*.md*'), recursive=True)):
            if not (os.path.isfile(dp) and is_within_root(dp, real_target)):
                continue
            rel = os.path.relpath(dp, real_target).replace('\\', '/')
            if rel.startswith('docs/agents/'):
                continue
            debt['docs_total'] += 1
            if find_line_refs(read_text_safe(dp), skip_closed=False):
                debt['docs_with_refs'] += 1

    return debt


def format_counter(counter, limit=15):
    """Render top counter items compactly for Markdown digest sections."""
    if not counter:
        return ['(nessuna occorrenza rilevata)']
    return [f'- `{k}`: {v}' for k, v in counter.most_common(limit)]


def render_digest(real_target, days, stats, debt):
    """Build concise Markdown report keeping LLM consumption to a few KB."""
    claude_mb = stats['claude_bytes'] / (1024 * 1024)
    agy_mb = stats['agy_bytes'] / (1024 * 1024)
    lines = [
        f'# Retro & Debito v2: `{os.path.basename(real_target)}`',
        '',
        f'- **Finestra:** {"tutta la storia" if days == 0 else f"ultimi {days} giorni"}',
        f'- **Claude Code:** {stats["claude_sessions"]} sessioni (+ {stats["claude_subagents"]} subagenti, `{claude_mb:.1f} MB` analizzati a 0 token)',
        f'- **Antigravity:** {stats["agy_sessions"]} sessioni (`{agy_mb:.1f} MB` analizzati a 0 token)',
        f'- **Turni utente estratti:** {stats["user_turns"]}',
        '',
        '## Memorie e Knowledge',
    ]
    if stats['claude_memories']:
        lines += [f'- Claude `memory/{n}` ({sz} B)' for n, sz in stats['claude_memories']]
    else:
        lines.append('- Nessun file in Claude `memory/` per questo repo.')
    if stats['agy_knowledge']:
        lines.append(f'- Topic globali Antigravity `knowledge/`: {", ".join(stats["agy_knowledge"][:20])}')

    lines += ['', '## Conteggio strumenti, skill e MCP', '### Skill caricate', *format_counter(stats['skills'])]
    lines += ['', '### Chiamate MCP', *format_counter(stats['mcps'])]
    lines += ['', '### Strumenti usati', *format_counter(stats['tools'], 12)]

    lines += ['', '## Aperture sessioni recenti']
    lines += [f'- {x}' for x in stats['openers']] or ['- (nessuna)']

    lines += ['', '## Correzioni e attriti utente']
    lines += [f'- {x}' for x in stats['corrections']] or ['- (nessuna correzione rilevata)']

    lines += ['', '## Errori e blocchi ricorrenti']
    lines += [f'- {x}' for x in stats['errors']] or ['- (nessun errore rilevato)']

    lines += [
        '',
        '## Debito v2 nel repository',
        f'- `AGENTS.md`: Aree a rischio={debt["has_risk"]} | Verifiche={debt["has_checks"]}',
        f'- Ticket/spec chiusi lasciati intatti: {debt["closed_count"]}',
        f'- Pagine `docs/` da aggiornare on-touch (riferimenti di riga statici): {debt["docs_with_refs"]} / {debt["docs_total"]}',
    ]
    if debt['root_refs']:
        for fname, cnt, sample in debt['root_refs']:
            lines.append(f'- `{fname}`: {cnt} riferimenti statici di riga ({", ".join(sample)})')
    else:
        lines.append('- Nessun riferimento statico di riga nei file di regole radice.')

    if debt['open_items']:
        lines.append('- Ticket/spec aperti da convertire in v2:')
        for rel, st, lcnt, miss in debt['open_items']:
            st_disp = (st[:45].rstrip() + '...') if len(st) > 48 else st
            miss_s = ', '.join(miss) if miss else 'header v2 ok'
            lines.append(f'  - `{rel}` (status=`{st_disp}`, riga_refs={lcnt}, mancanti={miss_s})')
    else:
        lines.append('- Nessun ticket/spec aperto da convertire.')

    lines.append('')
    return '\n'.join(lines)


def main():
    """Parse CLI arguments, scan transcripts plus v2 repo debt, and write or print the digest."""
    parser = argparse.ArgumentParser(description='Condense Claude and Antigravity JSONL transcripts and v2 repo debt.')
    parser.add_argument('repo', help='Target project directory path')
    parser.add_argument('--days', type=int, default=30, help='Lookback window in days (0 = all history)')
    parser.add_argument('--out', default=None, help='Output markdown file path (atomic write; stdout if omitted)')
    parser.add_argument('--claude-dir', default=None, help='Override ~/.claude/projects directory')
    parser.add_argument('--agy-dir', action='append', default=None, help='Override Antigravity brain directory (repeatable)')
    parser.add_argument('--check-refs', action='store_true', help='Only check markdown files for static line references and exit 1 if found')
    parser.add_argument('--staged', action='store_true', help='With --check-refs, read staged git index contents instead of disk')
    args = parser.parse_args()

    real_target = os.path.realpath(os.path.abspath(args.repo))
    if not os.path.isdir(real_target):
        sys.stderr.write(f'Target directory not found: {real_target}\n')
        return 1

    if args.check_refs:
        findings = scan_line_refs(real_target, staged=args.staged)
        for rel, hits in findings:
            print(f'{rel}: {", ".join(hits[:5])}')
        return 1 if findings else 0

    home = os.path.expanduser('~')
    claude_dir = os.path.abspath(os.path.expanduser(args.claude_dir)) if args.claude_dir else os.path.join(home, '.claude', 'projects')
    if args.agy_dir:
        agy_dirs = [os.path.abspath(os.path.expanduser(d)) for d in args.agy_dir]
    else:
        agy_dirs = [
            os.path.join(home, '.gemini', 'antigravity', 'brain'),
            os.path.join(home, '.gemini', 'antigravity-ide', 'brain'),
            os.path.join(home, '.gemini', 'antigravity-cli', 'brain'),
        ]

    cutoff_ts = (time.time() - args.days * 86400) if args.days > 0 else 0.0
    stats = {
        'claude_sessions': 0,
        'claude_subagents': 0,
        'claude_bytes': 0,
        'agy_sessions': 0,
        'agy_bytes': 0,
        'user_turns': 0,
        'claude_memories': [],
        'agy_knowledge': [],
        'tools': Counter(),
        'skills': Counter(),
        'mcps': Counter(),
        'openers': [],
        'opener_seen': set(),
        'corrections': [],
        'correction_seen': set(),
        'errors': [],
        'error_seen': set(),
    }

    scan_claude_projects(real_target, claude_dir, cutoff_ts, stats)
    scan_agy_brains(real_target, agy_dirs, cutoff_ts, stats)
    debt = collect_repo_v2_debt(real_target)
    report = render_digest(real_target, args.days, stats, debt)

    if args.out:
        write_text_atomic(os.path.abspath(os.path.expanduser(args.out)), report)
    else:
        print(report)
    return 0


if __name__ == '__main__':
    sys.exit(main())
