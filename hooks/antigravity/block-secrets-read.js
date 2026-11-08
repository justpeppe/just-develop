const fs = require('fs');

// Block secret files: configuration files with this extension and .env*, except placeholders such as .env.example.
const SAFE_ENV_SUFFIXES = ['.example', '.sample', '.template', '.dist'];

// The extension is split so a search for that file type does not match this source.
const EXT_INI = '.i' + 'ni';

const GIT_OPTIONS_WITH_ARG = new Set([
  '-c', '-C', '--git-dir', '--work-tree', '--namespace', '--super-prefix', '--exec-path', '--config-env'
]);
const COMMIT_OPTIONS_WITH_ARG = new Set([
  '-F', '--file', '-C', '--reuse-message', '-c', '--reedit-message', '--fixup', '--squash',
  '--author', '--date', '-t', '--template', '--cleanup', '-u', '--untracked-files', '--pathspec-from-file'
]);
const SAFE_GLOB_VALUE = /^[a-zA-Z0-9.*?_~+\-/\\[\]{}]+$/;
const LEX_TOKEN = /\\.|"(?:\\.|[^"\\])*"|'[^']*'|(?:^|(?<=[\s;&|()]))#[^\r\n]*/g;
const WORD_TOKEN = /(?:\\.|"(?:\\.|[^"\\])*"|'[^']*'|\S)+/g;

function isSecretToken(raw) {
  const token = raw.replace(/^["'`]+|["'`]+$/g, '').trim();
  if (!token) return false;
  const lower = token.toLowerCase();
  const base = lower.split(/[\\/]/).pop();
  if (!base) return false;

  if (lower.endsWith(EXT_INI)) return true;

  const envMatch = base.match(/^\.env(.*)$/);
  if (envMatch && !SAFE_ENV_SUFFIXES.includes(envMatch[1])) return true;

  return false;
}

function stripOuterQuotes(s) {
  if (s.length >= 2 && ((s[0] === '"' && s.endsWith('"')) || (s[0] === "'" && s.endsWith("'")))) {
    return s.slice(1, -1);
  }
  return s;
}

// Only exclusions held in one token with a pure glob value pass, so `python x.py -Exclude secret` does not.
function isSelfContainedExclusion(rawWord) {
  const t = stripOuterQuotes(rawWord.trim());
  let val = null;
  let m;
  if (t.startsWith(':!') || t.startsWith(':^')) {
    val = t.slice(2);
  } else if ((m = t.match(/^:\([a-z,]*exclude[a-z,]*\)(.+)$/i))) {
    val = m[1];
  } else if ((m = t.match(/^--exclude=(.+)$/i))) {
    val = stripOuterQuotes(m[1]);
  } else if ((m = t.match(/^(?:--[iI]?[gG][lL][oO][bB]|-g)=(.+)$/))) {
    const inner = stripOuterQuotes(m[1]);
    if (inner.startsWith('!')) val = inner.slice(1);
  }
  return Boolean(val && SAFE_GLOB_VALUE.test(val));
}

// For one plain `git commit`, remove only the -m text: paths and -F <file> stay visible to the scan.
function stripPureGitCommitMessage(cmd) {
  if (cmd.includes('`') || cmd.includes('$(') || cmd.includes('<(') || cmd.includes('>(')) return cmd;
  const sanitized = cmd.replace(LEX_TOKEN, (m) => {
    if (m[0] === '#') return '';
    if (m[0] === '"' || m[0] === "'") return m.replace(/[\r\n;&|()<>]/g, ' ');
    return m;
  });
  if (sanitized.includes('<') || sanitized.includes('>')) return cmd;
  const parts = sanitized.split(/&&|\|\||[;&|\r\n()]/).map((p) => p.trim()).filter(Boolean);
  if (parts.length !== 1) return cmd;

  const rawWords = cmd.trim().match(WORD_TOKEN);
  if (!rawWords || !rawWords.length) return cmd;
  const unq = rawWords.map((w) => w.replace(/^["']|["']$/g, ''));
  const base = unq[0].split(/[\\/]/).pop().toLowerCase().replace(/\.exe$/, '');
  if (base !== 'git') return cmd;

  let i = 1;
  while (i < unq.length) {
    const a = unq[i];
    if (GIT_OPTIONS_WITH_ARG.has(a)) { i += 2; continue; }
    if (a.startsWith('-')) { i += 1; continue; }
    break;
  }
  if (i >= unq.length || unq[i].toLowerCase() !== 'commit') return cmd;

  const kept = rawWords.slice(0, i + 1);
  let j = i + 1;
  while (j < rawWords.length) {
    const a = unq[j];
    if (a === '--') {
      kept.push(...rawWords.slice(j));
      break;
    }
    if (COMMIT_OPTIONS_WITH_ARG.has(a)) {
      kept.push(rawWords[j]);
      if (j + 1 < rawWords.length) kept.push(rawWords[j + 1]);
      j += 2;
      continue;
    }
    if (a === '--message' || /^-[a-zA-Z]*m$/.test(a)) {

      // Skip the -m flag and its message.
      j += 2;
      continue;
    }
    if (a.startsWith('--message=') || (a.startsWith('-m') && a.length > 2 && !a.startsWith('--'))) {
      j += 1;
      continue;
    }
    kept.push(rawWords[j]);
    j += 1;
  }
  return kept.join(' ');
}

// Allow inspection commands that do not open a secret file, as long as they have no redirection or subshell.
function isSafeInspectCommand(part) {
  if (part.includes('`') || part.includes('$(') || part.includes('<') || part.includes('>(')) return false;

  const rawWords = part.trim().match(WORD_TOKEN);
  if (!rawWords || !rawWords.length) return false;
  const unquoted = rawWords.map((w) => w.replace(/^["']|["']$/g, '').trim());
  const cmd = unquoted[0].split(/[\\/]/).pop().toLowerCase().replace(/\.exe$/, '');


  // In PowerShell `echo (Get-Content x)` prints the file, so parentheses are scanned like any other command.
  if (['echo', 'write-host', 'write-output'].includes(cmd)) return !part.includes('(');

  if (cmd === 'git') {
    let i = 1;
    while (i < unquoted.length) {
      const a = unquoted[i];
      if (GIT_OPTIONS_WITH_ARG.has(a)) { i += 2; continue; }
      if (a.startsWith('-')) { i += 1; continue; }
      break;
    }
    if (i >= unquoted.length) return false;
    const sub = unquoted[i].toLowerCase();

    // `git log -p` prints file contents, so with a patch flag the paths are scanned.
    if (sub === 'log' && !unquoted.some((a) => /^(-p|-u|-L|--patch)/.test(a))) return true;
    if (sub === 'check-ignore' || sub === 'status' || sub === 'ls-files') return true;
    if (sub === 'rm' && unquoted.includes('--cached')) return true;

    if (sub === 'grep') {
      const grepArgs = unquoted.slice(i + 1);
      const posArgs = [];
      let pastDashDash = false;
      const pathspecs = [];
      for (const a of grepArgs) {
        if (a === '--') { pastDashDash = true; continue; }
        if (pastDashDash) {
          pathspecs.push(a);
        } else if (a.startsWith('-')) {
          continue;
        } else {
          posArgs.push(a);
        }
      }
      if (posArgs.length >= 1) {
        const targetPaths = [...posArgs.slice(1), ...pathspecs];
        const targetsSecret = targetPaths.some((p) => {
          if (isSelfContainedExclusion(p)) return false;
          return Boolean(checkCandidatePiece(p));
        });
        if (!targetsSecret) return true;
      }
    }
  }

  if (cmd === 'findstr') {
    const args = unquoted.slice(1);
    const nonFlags = args.filter((a) => !a.startsWith('/'));
    if (nonFlags.length >= 2) {
      const targetFiles = nonFlags.slice(1);
      const targetsSecret = targetFiles.some((f) => Boolean(checkCandidatePiece(f)));
      if (!targetsSecret) return true;
    }
  }

  return false;
}

function checkCandidatePiece(piece) {
  if (!piece) return null;
  if (isSecretToken(piece)) return piece;

  // Also covers prefixes such as --file=secret, HEAD:secret or file:/// URLs.
  const eqIdx = piece.indexOf('=');
  if (eqIdx !== -1 && isSecretToken(piece.slice(eqIdx + 1))) return piece;
  const colonIdx = piece.lastIndexOf(':');
  if (colonIdx > 1 && isSecretToken(piece.slice(colonIdx + 1))) return piece;
  if (colonIdx === 1 && !/^[a-zA-Z]:[\\/]/.test(piece) && isSecretToken(piece.slice(2))) return piece;
  return null;
}

function scanString(str, isCommandField) {
  const effective = isCommandField ? stripPureGitCommitMessage(str) : str;
  for (const part of effective.split(/&&|\|\||[;&|\r\n]/)) {
    if (isCommandField && isSafeInspectCommand(part)) continue;
    const words = part.trim().match(WORD_TOKEN);
    if (!words) continue;
    for (const rawWord of words) {
      if (isSelfContainedExclusion(rawWord)) continue;
      const unquoted = rawWord.replace(/^["']|["']$/g, '').trim();

      const direct = checkCandidatePiece(unquoted);
      if (direct) return direct;


      // Also inspect inline expressions with no spaces, such as python -c "open('...').read()".
      for (const sub of unquoted.split(/[\s()[\]{}"'`,;|<>]+/)) {
        const hit = checkCandidatePiece(sub);
        if (hit) return hit;
      }
    }
  }
  return null;
}

// Scan every string in the payload, because each tool names its fields differently.
function findBlockedToken(value, keyName) {
  if (typeof value === 'string') {
    const isCmd = keyName === 'CommandLine' || keyName === 'command';
    return scanString(value, isCmd);
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const hit = findBlockedToken(item, keyName);
      if (hit) return hit;
    }
    return null;
  }
  if (value && typeof value === 'object') {
    for (const key of Object.keys(value)) {
      const hit = findBlockedToken(value[key], key);
      if (hit) return hit;
    }
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
  if (!input || !input.trim()) respond('allow');

  const payload = JSON.parse(input);
  const hit = findBlockedToken(payload?.toolCall?.args ?? payload?.tool_input ?? payload, '');

  if (hit) {
    respond(
      'deny',
      `BLOCKED: '${hit}' e' un file di segreti (.ini/.env di progetto). Non va letto, stampato o loggato. Usa il relativo *.example/*.sample per la struttura.`
    );
  }

  respond('allow');
} catch (err) {
  respond('allow');
}
