const fs = require('fs');

const GIT_OPTIONS_WITH_ARG = new Set([
  '-c', '-C', '--git-dir', '--work-tree', '--namespace', '--super-prefix', '--exec-path', '--config-env'
]);
const LAUNCHERS = new Set(['env', 'sudo', 'command', 'exec', 'nohup', 'time']);
const SHELLS = new Set(['sh', 'bash', 'zsh', 'dash', 'pwsh', 'powershell', 'cmd']);
const ASSIGNMENT = /^[A-Za-z_]\w*=/;
const SHELL_RUN_FLAG = /^(?:-(?:[a-z]*c|command)|\/[ck](?:$|["']))/i;

const BRANCH_MUTATING_FLAGS = new Set([
  '-d', '-D', '-f', '-m', '-M', '-c', '-C', '-u',
  '--delete', '--force', '--move', '--copy', '--set-upstream-to', '--unset-upstream', '--edit-description'
]);
const BRANCH_VALUE_FLAGS = new Set([
  '--contains', '--no-contains', '--merged', '--no-merged', '--points-at',
  '--sort', '--format', '--abbrev', '--color', '--column'
]);
const BRANCH_LIST_FLAGS = new Set(['-l', '--list']);
const WORKTREE_BLOCKED_SUBS = new Set(['add', 'remove', 'prune', 'move', 'lock', 'unlock', 'repair']);

const HEREDOC = /<<-?\s*['"]?(\w+)['"]?([^\n]*)\n[\s\S]*?\n\1[ \t]*(?=\n|$)/g;
const PS_HERE_SQ = /@'[ \t]*\r?\n(?:[\s\S]*?\r?\n)?[ \t]*'@/g;
const PS_HERE_DQ = /@"[ \t]*\r?\n(?:([\s\S]*?)\r?\n)?[ \t]*"@/g;
const LEX_TOKEN = /\\.|"(?:\\.|[^"\\])*"|'[^']*'|(?:^|(?<=[\s;&|()]))#[^\r\n]*/g;
const BACKTICK_SUB = /`([^`\r\n]*\S+\s+\S+[^`\r\n]*)`/g;
const DQUOTE_SUB = /\$\(([^)\r\n]+)\)|`([^`\r\n]*\S+\s+\S+[^`\r\n]*)`/g;
const WORD_TOKEN = /(?:\\.|"(?:\\.|[^"\\])*"|'[^']*'|\S)+/g;

function sanitizeForSplit(cmd) {
  const extra = [];
  let pre = cmd.replace(HEREDOC, (_, tag, rest) => '<<' + tag + rest);
  pre = pre.replace(PS_HERE_SQ, "@''@");
  pre = pre.replace(PS_HERE_DQ, (_, body) => {
    for (const sub of (body || '').matchAll(DQUOTE_SUB)) {
      extra.push((sub[1] || sub[2]).replace(/\\"/g, '"'));
    }
    return '@""@';
  });

  const lexed = pre.replace(LEX_TOKEN, (m) => {
    if (m[0] === '#') return '';
    if (m[0] === "'") return m.replace(/[\r\n;&|()`]/g, ' ');
    if (m[0] === '"') {
      for (const sub of m.matchAll(DQUOTE_SUB)) {
        extra.push((sub[1] || sub[2]).replace(/\\"/g, '"'));
      }
      return m.replace(/[\r\n;&|()]/g, ' ').replace(/`/g, '');
    }
    return m;
  });
  let cleaned = lexed.replace(BACKTICK_SUB, (_, inner) => ' ; ' + inner + ' ; ');
  if (lexed.includes('`')) cleaned += ' ; ' + lexed.replace(/`\r?\n/g, ' ').replace(/`/g, '');
  return cleaned + extra.map((e) => ' ; ' + e).join('');
}

function isGitCommand(word) {
  const base = word.split(/[\\/]/).pop().replace(/`/g, '').toLowerCase().replace(/\.exe$/, '');
  return base === 'git';
}

function extractGitSubcommand(args) {
  let i = 0;
  while (i < args.length) {
    const arg = args[i];
    if (!arg) { i += 1; continue; }
    if (GIT_OPTIONS_WITH_ARG.has(arg)) { i += 2; continue; }
    if (arg.startsWith('-')) { i += 1; continue; }
    const subArgs = args.slice(i + 1).map((a) => {
      const s = a.replace(/[`\\]/g, '');
      return (s.startsWith('-') || s === '.') ? s : a;
    });
    return { sub: arg.replace(/[`\\]/g, '').toLowerCase(), subArgs };
  }
  return { sub: '', subArgs: [] };
}

function isBranchMutating(subArgs) {
  if (!subArgs.length) return false;
  let hasList = false;
  const positional = [];
  let i = 0;
  while (i < subArgs.length) {
    const a = subArgs[i];
    if (BRANCH_MUTATING_FLAGS.has(a) || [...BRANCH_MUTATING_FLAGS].some((f) => a.startsWith(f + '='))) {
      return true;
    }
    if (/^-[a-zA-Z]*[dDfMmCc]/.test(a)) return true;
    if (BRANCH_LIST_FLAGS.has(a)) { hasList = true; i += 1; continue; }
    if (BRANCH_VALUE_FLAGS.has(a)) { i += 2; continue; }
    if (a.startsWith('-')) { i += 1; continue; }
    positional.push(a);
    i += 1;
  }
  return positional.length > 0 && !hasList;
}

function dangerousGitRule({ sub, subArgs }) {
  if (sub === 'push') return 'git push';
  if (sub === 'merge') return 'git merge';
  if (sub === 'reset' && subArgs.some((a) => a === '--hard' || a === '-hard')) return 'git reset --hard';
  if (sub === 'clean' && subArgs.some((a) => a === '--force' || /^-[a-z]*f/i.test(a))) return 'git clean -f';
  if (sub === 'branch' && isBranchMutating(subArgs)) return 'git branch create/delete/move';

  if (sub === 'checkout') {
    const helpOnly = subArgs.length > 0 && subArgs.every((a) => a === '-h' || a === '--help');
    if (!helpOnly) return 'git checkout';
  }
  if (sub === 'switch') {
    const helpOnly = subArgs.length > 0 && subArgs.every((a) => a === '-h' || a === '--help');
    if (!helpOnly) return 'git switch';
  }
  if (sub === 'worktree' && subArgs.some((a) => WORKTREE_BLOCKED_SUBS.has(a.toLowerCase()) || a === '-b' || a === '-B')) {
    return 'git worktree mutate';
  }

  if (sub === 'restore') {
    const hasStaged = subArgs.some((a) => a === '--staged' || /^-[a-rt-zA-Z]*S/.test(a));
    const hasWorktree = subArgs.some((a) => a === '--worktree' || /^-[a-rt-zA-Z]*W/.test(a));
    if (!hasStaged || hasWorktree) return 'git restore';
  }
  if (sub === 'stash' && subArgs.some((a) => ['drop', 'clear', 'pop'].includes(a.toLowerCase()))) {
    return 'git stash drop/clear/pop';
  }
  return null;
}

function stripLaunchers(words) {
  let i = 0;
  while (i < words.length && (ASSIGNMENT.test(words[i]) || LAUNCHERS.has(words[i].toLowerCase()) || (i > 0 && words[i].startsWith('-')))) {
    i += 1;
  }
  return words.slice(i);
}

function stripOuterQuotes(s) {
  if (s.length >= 2 && ((s[0] === '"' && s.endsWith('"')) || (s[0] === "'" && s.endsWith("'")))) {
    return s.slice(1, -1);
  }
  return s;
}

function extractShellInnerTokens(rawRest) {
  const chunks = [];
  for (const rw of rawRest) {
    const cleaned = rw.replace(/^\/[ck](?=$|["'])/i, '');
    if (!cleaned) continue;
    chunks.push(stripOuterQuotes(cleaned));
  }
  const joined = chunks.filter(Boolean).join(' ').replace(/(&&|\|\||[;|\r\n{}()])/g, ' $1 ');
  const out = [];
  for (const tok of joined.match(WORD_TOKEN) || []) {
    if (['&&', '||', ';', '|', '(', ')', '{', '}'].includes(tok)) {
      out.push(tok);
      continue;
    }
    if (tok === '&') continue;
    const cleaned = stripOuterQuotes(tok.replace(/^&+/, '').trim()).replace(/^["']+|["']+$/g, '');
    if (cleaned) out.push(cleaned);
  }
  return out;
}

function matchDangerousCommand(command) {
  for (const part of sanitizeForSplit(command).split(/&&|\|\||[;&|\r\n()]/)) {
    const rawMatches = part.trim().match(WORD_TOKEN);
    if (!rawMatches) continue;
    const rawWords = rawMatches.filter((w) => w.replace(/^["']|["']$/g, '').length > 0);
    const cleanedWords = rawWords.map((w) => w.replace(/^["']|["']$/g, ''));
    const words = stripLaunchers(cleanedWords);
    if (!words.length) continue;
    const rawRest = rawWords.slice((cleanedWords.length - words.length) + 1);

    const base = words[0].split(/[\\/]/).pop().replace(/`/g, '').toLowerCase().replace(/\.exe$/, '');
    const rest = words.slice(1);

    if (SHELLS.has(base) && rest.some((w) => SHELL_RUN_FLAG.test(w))) {
      const inner = extractShellInnerTokens(rawRest);
      const segs = [];
      let cur = [];
      for (const tok of inner) {
        if (['&&', '||', ';', '|', '(', ')', '{', '}'].includes(tok)) {
          if (cur.length) { segs.push(cur); cur = []; }
        } else {
          cur.push(tok);
        }
      }
      if (cur.length) segs.push(cur);
      for (const seg of segs) {
        for (let i = 0; i < seg.length; i += 1) {
          const hit = isGitCommand(seg[i]) ? dangerousGitRule(extractGitSubcommand(seg.slice(i + 1))) : null;
          if (hit) return hit;
        }
      }
      continue;
    }

    if (base === 'push' && rest.some((a) => a === '--force' || a === '-f' || a.startsWith('--force-with-lease'))) {
      return 'push --force';
    }
    if (base === 'reset' && rest.some((a) => a === '--hard' || a === '-hard')) {
      return 'reset --hard';
    }
    if (!isGitCommand(words[0])) continue;

    const hit = dangerousGitRule(extractGitSubcommand(rest));
    if (hit) return hit;
  }
  return null;
}

function respond(decision, reason) {
  const res = { decision };
  if (reason) res.reason = reason;
  process.stdout.write(JSON.stringify(res));
  process.exit(0);
}

try {
  const input = fs.readFileSync(0, 'utf-8');
  if (!input || !input.trim()) {
    respond('allow');
  }

  const payload = JSON.parse(input);
  const command = payload?.toolCall?.args?.CommandLine || payload?.tool_input?.command || '';

  if (!command) {
    respond('allow');
  }

  const hit = matchDangerousCommand(command);

  // Log only denied invocations (no command text) so secrets never land in the log file.
  if (hit) {
    try {
      fs.appendFileSync(__dirname + '/block-dangerous-git.log', new Date().toISOString() + ' deny ' + hit + '\n');
    } catch (logError) {
      // The decision below does not depend on the log.
    }
    respond('deny', `BLOCKED: '${hit}' e' bloccato agli agenti (inclusi branch/push/merge/comandi distruttivi): lo esegue lo sviluppatore.`);
  }

  respond('allow');
} catch (err) {
  respond('allow');
}
