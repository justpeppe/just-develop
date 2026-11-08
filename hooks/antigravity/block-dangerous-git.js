const fs = require('fs');
const path = require('path');

const GIT_OPTIONS_WITH_ARG = new Set([
  '-c', '-C', '--git-dir', '--work-tree', '--namespace', '--super-prefix', '--exec-path', '--config-env'
]);
const LAUNCHERS = new Set(['env', 'sudo', 'command', 'exec', 'nohup', 'time']);
const SHELLS = new Set(['sh', 'bash', 'zsh', 'dash', 'pwsh', 'powershell']);
const ASSIGNMENT = /^[A-Za-z_]\w*=/;
const SHELL_RUN_FLAG = /^-(?:[a-z]*c|command)$/i;

// A letter after the last dot keeps tags and release branches such as v1.2.0 out.
const FILE_EXTENSION = /\.[a-zA-Z][a-zA-Z0-9]*$/;

const HEREDOC = /<<-?\s*['"]?(\w+)['"]?([^\n]*)\n[\s\S]*?\n\1[ \t]*(?=\n|$)/g;
const LEX_TOKEN = /\\.|"(?:\\.|[^"\\])*"|'[^']*'|(?:^|(?<=[\s;&|()]))#[^\r\n]*/g;
const BACKTICK_SUB = /`([^`\r\n]*\S+\s+\S+[^`\r\n]*)`/g;
const DQUOTE_SUB = /\$\(([^)\r\n]+)\)|`([^`\r\n]*\S+\s+\S+[^`\r\n]*)`/g;
const WORD_TOKEN = /(?:\\.|"(?:\\.|[^"\\])*"|'[^']*'|\S)+/g;

function sanitizeForSplit(cmd) {
  const noHeredoc = cmd.replace(HEREDOC, (_, tag, rest) => '<<' + tag + rest);
  const extra = [];
  const lexed = noHeredoc.replace(LEX_TOKEN, (m) => {
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

function namesAPath(arg, cwd) {
  if (arg.startsWith('-')) return false;
  return FILE_EXTENSION.test(arg) || fs.existsSync(path.resolve(cwd || '.', arg));
}

function dangerousGitRule({ sub, subArgs }, cwd) {
  if (sub === 'push') return 'git push';
  if (sub === 'merge') return 'git merge';
  if (sub === 'reset' && subArgs.some((a) => a === '--hard' || a === '-hard')) return 'git reset --hard';
  if (sub === 'clean' && subArgs.some((a) => a === '--force' || /^-[a-z]*f/i.test(a))) return 'git clean -f';
  if (sub === 'branch' && subArgs.some((a) => a === '--force' || /^-[a-zA-Z]*[DfMC]/.test(a))) return 'git branch -D';

  // Checkout of a branch is allowed; checkout of files rewrites the working tree without a trace.
  if (sub === 'checkout') {
    const forced = subArgs.some((a) =>
      a === '.' || a === '--' || a === '-f' || a === '--force' || /^-[a-zA-Z]*B/.test(a) ||
      a.startsWith('./') || a.startsWith('.\\')
    );

    // shortcut: `git -C other checkout name` is checked against Cwd, resolve -C if it ever misses a file.
    const createsBranch = subArgs.some((a) => a === '-b' || a === '--orphan');
    if (forced || (!createsBranch && subArgs.some((a) => namesAPath(a, cwd)))) return 'git checkout';
  }

  if (sub === 'restore') {
    const hasStaged = subArgs.some((a) => a === '--staged' || /^-[a-rt-zA-Z]*S/.test(a));
    const hasWorktree = subArgs.some((a) => a === '--worktree' || /^-[a-rt-zA-Z]*W/.test(a));
    if (!hasStaged || hasWorktree) return 'git restore';
  }
  if (sub === 'switch' && subArgs.some((a) => a === '-f' || a === '--force' || a === '--discard-changes')) {
    return 'git switch --discard-changes';
  }
  if (sub === 'stash' && subArgs.some((a) => ['drop', 'clear', 'pop'].includes(a.toLowerCase()))) {
    return 'git stash drop/clear/pop';
  }
  return null;
}

function stripLaunchers(words) {
  // shortcut: a launcher option with a separate value (sudo -u bob) stops here, parse each launcher if that shows up.
  let i = 0;
  while (i < words.length && (ASSIGNMENT.test(words[i]) || LAUNCHERS.has(words[i].toLowerCase()) || (i > 0 && words[i].startsWith('-')))) {
    i += 1;
  }
  return words.slice(i);
}

function matchDangerousCommand(command, cwd) {
  for (const part of sanitizeForSplit(command).split(/&&|\|\||[;&|\r\n()]/)) {
    const rawWords = part.trim().match(WORD_TOKEN);
    if (!rawWords) continue;
    const words = stripLaunchers(rawWords.map((w) => w.replace(/^["']|["']$/g, '')).filter(Boolean));
    if (!words.length) continue;

    const base = words[0].split(/[\\/]/).pop().replace(/`/g, '').toLowerCase().replace(/\.exe$/, '');
    const rest = words.slice(1);

    // Separators inside the quoted script are already blanks here, so every git word is checked.
    if (SHELLS.has(base) && rest.some((w) => SHELL_RUN_FLAG.test(w))) {
      const inner = rest.join(' ').split(/\s+/);
      for (let i = 0; i < inner.length; i += 1) {
        const hit = inner[i] === 'git' ? dangerousGitRule(extractGitSubcommand(inner.slice(i + 1)), cwd) : null;
        if (hit) return hit;
      }
      continue;
    }

    if (base === 'push' && rest.some((a) => a === '--force' || a === '-f' || a.startsWith('--force-with-lease'))) {
      return 'push --force';
    }
    if (base === 'reset' && rest.some((a) => a === '--hard' || a === '-hard')) {
      return 'reset --hard';
    }
    if (base !== 'git') continue;

    const hit = dangerousGitRule(extractGitSubcommand(rest), cwd);
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

  const hit = matchDangerousCommand(command, payload?.toolCall?.args?.Cwd || '');

  // Proof that the host runs the hook; it keeps no command text, and a failed write must not change the decision.
  // shortcut: the file only grows, one short line per command; rotate it if it ever gets large.
  try {
    fs.appendFileSync(__dirname + '/block-dangerous-git.log', new Date().toISOString() + ' ' + (hit || 'allow') + '\n');
  } catch (logError) {
    // The decision below does not depend on the log.
  }

  if (hit) {
    respond('deny', `BLOCKED: '${command}' matches dangerous git pattern '${hit}'. Do not look for another route: stop and ask the user.`);
  }

  respond('allow');
} catch (err) {
  // Google's hooks page does not document what a crash does, so an unreadable payload is allowed as before.
  respond('allow');
}
