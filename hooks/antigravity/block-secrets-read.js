const fs = require('fs');

const SAFE_ENV_SUFFIXES = ['.example', '.sample', '.template', '.dist'];
const EXT_INI = '.i' + 'ni';
const EXT_ENV = '.e' + 'nv';
const ENV_FILE_RE = new RegExp('^\\.' + 'e' + 'nv(.*)$');
const JSONL_MAX_BYTES = 100 * 1024;
const JSONL_MAX_LINES = 100;

const GIT_OPTIONS_WITH_ARG = new Set([
  '-c', '-C', '--git-dir', '--work-tree', '--namespace', '--super-prefix', '--exec-path', '--config-env'
]);
const COMMIT_OPTIONS_WITH_ARG = new Set([
  '-F', '--file', '-C', '--reuse-message', '-c', '--reedit-message', '--fixup', '--squash',
  '--author', '--date', '-t', '--template', '--cleanup', '-u', '--untracked-files', '--pathspec-from-file'
]);
const PS_NEGATIVE_OPS = new Set([
  '-ne', '-cne', '-ine', '-notin', '-cnotin', '-inotin',
  '-notlike', '-cnotlike', '-inotlike', '-notmatch', '-cnotmatch', '-inotmatch',
  '-notcontains', '-cnotcontains', '-inotcontains'
]);
const PS_FILE_READERS = new Set([
  'get-content', 'gc', 'cat', 'type', 'more', 'less', 'head', 'tail',
  'open', 'read', 'readalltext', 'readalllines', 'import-csv', 'import-clixml',
  'import-module', 'convertfrom-json', 'convertfrom-stringdata'
]);
const RG_VALUE_FLAGS = new Set([
  '-e', '--regexp', '-f', '--file', '-g', '--glob', '--iglob',
  '-t', '--type', '-T', '--type-not', '--type-add', '-A', '-B', '-C', '--context',
  '-m', '--max-count', '--max-filesize', '--encoding', '-j', '--threads',
  '--sort', '--sortr', '--color', '--colors', '--path-separator'
]);
const SLS_VALUE_FLAGS = new Set([
  '-pattern', '-path', '-literalpath', '-include', '-exclude', '-context', '-encoding', '-culture'
]);

const SAFE_GLOB_VALUE = /^[a-zA-Z0-9.*?_~+\-/\\\[\]{},]+$/;
const LEX_TOKEN = /\\.|"(?:\\.|[^"\\])*"|'[^']*'|(?:^|(?<=[\s;&|()]))#[^\r\n]*/g;
const WORD_TOKEN = /(?:\\.|"(?:\\.|[^"\\])*"|'[^']*'|\S)+/g;

function isSecretToken(raw) {
  const token = raw.replace(/^["'`]+|["'`]+$/g, '').trim();
  if (!token) return false;
  const lower = token.toLowerCase();
  const base = lower.split(/[\\/]/).pop();
  if (!base) return false;

  if (lower.endsWith(EXT_INI) || lower.endsWith(EXT_ENV)) return true;

  const envMatch = base.match(ENV_FILE_RE);
  if (envMatch && !SAFE_ENV_SUFFIXES.includes(envMatch[1])) return true;

  return false;
}

function stripOuterQuotes(s) {
  if (s.length >= 2 && ((s[0] === '"' && s.endsWith('"')) || (s[0] === "'" && s.endsWith("'")))) {
    return s.slice(1, -1);
  }
  return s;
}

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

function checkCandidatePiece(piece) {
  if (!piece) return null;
  if (isSecretToken(piece)) return piece;

  const eqIdx = piece.indexOf('=');
  if (eqIdx !== -1 && isSecretToken(piece.slice(eqIdx + 1))) return piece;
  const colonIdx = piece.lastIndexOf(':');
  if (colonIdx > 1 && isSecretToken(piece.slice(colonIdx + 1))) return piece;
  if (colonIdx === 1 && !/^[a-zA-Z]:[\\/]/.test(piece) && isSecretToken(piece.slice(2))) return piece;
  return null;
}

function tokenHitsSecret(raw) {
  for (const part of raw.split(',')) {
    const hit = checkCandidatePiece(part.trim());
    if (hit) return hit;
  }
  return null;
}

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

function isSafeInspectCommand(part) {
  if (part.includes('`') || part.includes('$(') || part.includes('<') || part.includes('>(')) return false;

  const rawWords = part.trim().match(WORD_TOKEN);
  if (!rawWords || !rawWords.length) return false;
  const unquoted = rawWords.map((w) => w.replace(/^["']|["']$/g, '').trim());
  const cmd = unquoted[0].split(/[\\/]/).pop().toLowerCase().replace(/\.exe$/, '');

  if (['echo', 'write-host', 'write-output'].includes(cmd)) return !part.includes('(');

  if (['get-childitem', 'gci', 'dir', 'ls'].includes(cmd)) {
    if (part.includes('(')) return false;
    let i = 1;
    while (i < unquoted.length) {
      const a = unquoted[i];
      const al = a.toLowerCase();
      if (al === '-exclude') { i += 2; continue; }
      if (al.startsWith('-exclude=') || al.startsWith('--exclude=')) { i += 1; continue; }
      if (!isSelfContainedExclusion(a) && tokenHitsSecret(a)) return false;
      i += 1;
    }
    return true;
  }

  if (['where-object', 'where', '?'].includes(cmd)) {
    const subTokens = unquoted.flatMap((w) => w.split(/[\s()\[\]{}"'`,;|<>:.]+/)).map((s) => s.toLowerCase()).filter(Boolean);
    if (subTokens.some((s) => PS_FILE_READERS.has(s))) return false;
    for (let i = 0; i < unquoted.length; i += 1) {
      const tok = unquoted[i];
      const frags = [tok, ...tok.split(/[\s()\[\]{}"'`,;|<>]+/).filter(Boolean)];
      if (frags.some((frag) => Boolean(tokenHitsSecret(frag)))) {
        const prev = i > 0 ? unquoted[i - 1].toLowerCase() : '';
        if (!PS_NEGATIVE_OPS.has(prev)) return false;
      }
    }
    return true;
  }

  if (['select-string', 'sls'].includes(cmd)) {
    if (part.includes('(')) return false;
    const targetPaths = [];
    const posArgs = [];
    let sawPattern = false;
    let i = 1;
    while (i < unquoted.length) {
      const a = unquoted[i];
      const al = a.toLowerCase();
      if (al === '-pattern') { sawPattern = true; i += 2; continue; }
      if (al.startsWith('-pattern:') || al.startsWith('-pattern=')) { sawPattern = true; i += 1; continue; }
      if (['-path', '-literalpath', '-include'].includes(al)) {
        if (i + 1 < unquoted.length) {
          let val = unquoted[i + 1];
          targetPaths.push(val);
          i += 2;
          while (i < unquoted.length && (val.endsWith(',') || unquoted[i] === ',' || unquoted[i].startsWith(','))) {
            val = unquoted[i];
            if (val !== ',') {
              targetPaths.push(val.replace(/^,+/, ''));
            } else if (i + 1 < unquoted.length) {
              i += 1;
              val = unquoted[i];
              targetPaths.push(val);
            }
            i += 1;
          }
          continue;
        }
        i += 2;
        continue;
      }
      if (/^-(?:path|literalpath|include)[:=]/.test(al)) {
        const sepIdx = a.search(/[:=]/);
        let val = a.slice(sepIdx + 1);
        targetPaths.push(val);
        i += 1;
        while (i < unquoted.length && (val.endsWith(',') || unquoted[i] === ',' || unquoted[i].startsWith(','))) {
          val = unquoted[i];
          if (val !== ',') {
            targetPaths.push(val.replace(/^,+/, ''));
          } else if (i + 1 < unquoted.length) {
            i += 1;
            val = unquoted[i];
            targetPaths.push(val);
          }
          i += 1;
        }
        continue;
      }
      const flagName = al.split(/[:=]/, 1)[0];
      if (SLS_VALUE_FLAGS.has(flagName)) { i += (al.includes(':') || al.includes('=')) ? 1 : 2; continue; }
      if (a.startsWith('-')) { i += 1; continue; }
      posArgs.push(a);
      i += 1;
    }
    const restPos = (!sawPattern && posArgs.length) ? posArgs.slice(1) : posArgs;
    targetPaths.push(...restPos);
    return !targetPaths.some((p) => !isSelfContainedExclusion(p) && Boolean(tokenHitsSecret(p)));
  }

  if (cmd === 'rg') {
    if (part.includes('(')) return false;
    const targetPaths = [];
    const posArgs = [];
    let sawPattern = false;
    let pastDashDash = false;
    let i = 1;
    while (i < unquoted.length) {
      const a = unquoted[i];
      if (a === '--') { pastDashDash = true; i += 1; continue; }
      if (pastDashDash) { targetPaths.push(a); i += 1; continue; }
      if (a === '-e' || a === '--regexp' || a.startsWith('-e=') || a.startsWith('--regexp=') || (a.startsWith('-e') && !a.startsWith('--') && a.length > 2)) {
        sawPattern = true;
        i += (a === '-e' || a === '--regexp') ? 2 : 1;
        continue;
      }
      if ((a.startsWith('-f') && !a.startsWith('--') && a.length > 2 && tokenHitsSecret(a.slice(2))) ||
          (a.startsWith('--file=') && tokenHitsSecret(a.slice(a.indexOf('=') + 1)))) {
        return false;
      }
      if (a === '-g' || a === '--glob' || a === '--iglob') {
        const val = i + 1 < unquoted.length ? unquoted[i + 1] : '';
        if (!(val.startsWith('!') && SAFE_GLOB_VALUE.test(val.slice(1)))) {
          if (tokenHitsSecret(val)) return false;
        }
        i += 2;
        continue;
      }
      if (RG_VALUE_FLAGS.has(a)) {
        if ((a === '-f' || a === '--file') && i + 1 < unquoted.length && tokenHitsSecret(unquoted[i + 1])) return false;
        i += 2;
        continue;
      }
      if (a.startsWith('-')) {
        if (!isSelfContainedExclusion(a) && tokenHitsSecret(a)) return false;
        i += 1;
        continue;
      }
      posArgs.push(a);
      i += 1;
    }
    const restPos = (!sawPattern && posArgs.length) ? posArgs.slice(1) : posArgs;
    targetPaths.push(...restPos);
    return !targetPaths.some((p) => !isSelfContainedExclusion(p) && Boolean(tokenHitsSecret(p)));
  }

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

    if (sub === 'log' && !unquoted.some((a) => /^(?:-p|-u|-L|--patch|--unified)/i.test(a))) return true;
    if (sub === 'check-ignore' || sub === 'status' || sub === 'ls-files') return true;
    if (sub === 'rm' && unquoted.includes('--cached')) return true;

    if (sub === 'grep') {
      const grepArgs = unquoted.slice(i + 1);
      const posArgs = [];
      let pastDashDash = false;
      const pathspecs = [];
      for (const a of grepArgs) {
        if (a === '--') { pastDashDash = true; continue; }
        if (pastDashDash) pathspecs.push(a);
        else if (!a.startsWith('-')) posArgs.push(a);
      }
      if (posArgs.length >= 1) {
        const targetPaths = [...posArgs.slice(1), ...pathspecs];
        const targetsSecret = targetPaths.some((p) => !isSelfContainedExclusion(p) && Boolean(tokenHitsSecret(p)));
        if (!targetsSecret) return true;
      }
    }
  }

  if (cmd === 'findstr') {
    let hasExplicitPattern = false;
    const nonFlags = [];
    for (let i = 1; i < unquoted.length;) {
      const a = unquoted[i];
      const al = a.toLowerCase();
      if (al.startsWith('/g:') || al.startsWith('/f:')) {
        if (tokenHitsSecret(a.slice(3))) return false;
        if (al.startsWith('/g:')) hasExplicitPattern = true;
        i += 1;
        continue;
      }
      if (al === '/g' || al === '/f') {
        if (i + 1 < unquoted.length && tokenHitsSecret(unquoted[i + 1])) return false;
        if (al === '/g') hasExplicitPattern = true;
        i += 2;
        continue;
      }
      if (al.startsWith('/c:')) { hasExplicitPattern = true; i += 1; continue; }
      if (al === '/c') { hasExplicitPattern = true; i += 2; continue; }
      if (a.startsWith('/')) { i += 1; continue; }
      nonFlags.push(a);
      i += 1;
    }
    if (hasExplicitPattern) {
      if (nonFlags.length >= 1 && !nonFlags.some((f) => Boolean(tokenHitsSecret(f)))) return true;
    } else if (nonFlags.length >= 2) {
      if (!nonFlags.slice(1).some((f) => Boolean(tokenHitsSecret(f)))) return true;
    }
  }

  return false;
}

function scanString(str, isCommandField) {
  let effective = isCommandField ? stripPureGitCommitMessage(str) : str;
  if (isCommandField) {
    effective = effective.replace(LEX_TOKEN, (m) => (m[0] === '#' ? '' : m));
  }
  for (const part of effective.split(/&&|\|\||[;&|\r\n]/)) {
    if (isCommandField && isSafeInspectCommand(part)) continue;
    const words = part.trim().match(WORD_TOKEN);
    if (!words) continue;
    for (const rawWord of words) {
      if (isSelfContainedExclusion(rawWord)) continue;
      const unquoted = rawWord.replace(/^["'`]+|["'`]+$/g, '').trim();

      const direct = tokenHitsSecret(unquoted);
      if (direct) return direct;

      for (const sub of unquoted.split(/[\s()\[\]{}"'`,;|<>]+/)) {
        const hit = checkCandidatePiece(sub);
        if (hit) return hit;
      }
    }
  }
  return null;
}

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

function checkLargeJsonlRead(payload) {
  const toolName = payload?.toolCall?.name || payload?.tool_name || '';
  const args = payload?.toolCall?.args ?? payload?.tool_input ?? {};
  if (!args || typeof args !== 'object') return null;
  if (toolName && toolName !== 'read_file' && toolName !== 'view_file') return null;

  const filePath = args.Path || args.AbsolutePath || args.TargetFile || args.file_path || '';
  if (typeof filePath !== 'string' || !filePath.trim().toLowerCase().endsWith('.jsonl')) return null;

  let size = 0;
  try {
    size = fs.statSync(filePath.trim()).size;
  } catch (err) {
    return null;
  }
  if (size <= JSONL_MAX_BYTES) return null;

  const sRaw = args.StartLine ?? args.start_line;
  const eRaw = args.EndLine ?? args.end_line;
  const s = (sRaw !== undefined && sRaw !== null && String(sRaw).trim() !== '') ? Number(sRaw) : NaN;
  const e = (eRaw !== undefined && eRaw !== null && String(eRaw).trim() !== '') ? Number(eRaw) : NaN;
  const validRange = Number.isInteger(s) && Number.isInteger(e) && s >= 1 && e >= s && (e - s + 1) <= JSONL_MAX_LINES;
  if (validRange) return null;

  return `BLOCKED: '${filePath}' supera 100 KB (${size} B). Usa un range <= 100 righe (StartLine/EndLine) oppure analizzalo con python -X utf8 -I.`;
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
      `BLOCKED: '${hit}' e' un file di segreti di progetto. Non va letto, stampato o loggato. Usa il relativo *.example/*.sample per la struttura.`
    );
  }

  const jsonlReason = checkLargeJsonlRead(payload);
  if (jsonlReason) {
    respond('deny', jsonlReason);
  }

  respond('allow');
} catch (err) {
  respond('allow');
}
