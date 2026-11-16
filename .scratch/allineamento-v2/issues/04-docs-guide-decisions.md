# 04: Documentazione, Guide, `DECISIONS.md` e `SETUP*.md` Allineati

**Status:** resolved
**Blocked by:** 01, 02, 03 (documenta i file e flussi definitivi)
**Review:** quick
**Esecutore:** @token-pro-2
**Metrica (S/G/C):** 0/0/0 (sola documentazione/guide allineata ai file già definiti)

## What to build

Allineare `AGENTS.md`, `README.md`, `GUIDE.md`, `GLOSSARY.md`, `DECISIONS.md`, `SETUP.md`, `SETUP-REPO.md` e `docs/` Mintlify+GitBook in `<REPO_ROOT>\` alla nuova architettura v2, rimuovendo ogni riferimento a `Flash`/`Argon` come vecchio default unico, `Review: single`, `flow-prompts.md`, `righe 1..N` e `CLAUDE_CODE_AUTO_COMPACT_WINDOW`.

## File e simboli toccati

- `AGENTS.md`: aggiornare la sezione `Verifiche` con `python -X utf8 -I`, gli ambiti commit, i nuovi hook (`post-merge`, `post-checkout`, `post-rewrite`) e i nuovi script (`session_check.py`, `background_checker.py`, `check-updates.py`).
- `README.md` & `GUIDE.md`: rimuovere `flow-prompts.md`, aggiornare tabella modelli (Casa Pro `Hydrogen`/`Argon` + `Sonnet`/`Opus`, Ufficio Ultra `Hydrogen`/`Carbon` + `Sonnet`/`Opus`), spiegare branching `office|home/<tipo>/<slug>` stile IDEA, Review binaria (`quick` 0 subagenti / `double` 3 subagenti `inherit`), controllo silenzioso 8h/24h e comando manuale `check-updates.py`.
- `GLOSSARY.md`: aggiornare voci `Hydrogen`, `Carbon`, `Argon`, `Progettista`, `Esecutore`, `Revisore`, `Doppia Review` (`quick` vs `double` a 3 subagenti `inherit`), `Repo versionato` / `Repo ibrido`, rimuovere vecchi valori `Type:` o riferimenti Delphi/`1..N`.
- `DECISIONS.md`: aggiungere voci datate (`2026-11-16`) per ogni decisione v2 (separazione `just-develop` vs `delphi`, `flow.md` nucleo + 2 skill `dmi: false`, Review binaria `quick`/`double` senza `3.8 Flash` né `single`, branching 3 livelli + fix `commit-msg`, `post-merge`/`post-checkout`/`post-rewrite` + worker 8h/24h con `git ls-remote` e lock kernel), aggiungendo `Superata da:` alle decisioni vecchie superate (es. decisione su Flash/Argon o `autoCompactWindow`).
- `SETUP.md` & `SETUP-REPO.md`:
  - `SETUP.md`: installazione dei nuovi hook Git (`pre-commit`, `commit-msg`, `post-merge`, `post-checkout`, `post-rewrite`), `fetch.prune true`, `SessionStart` portabile `python`/`python3`, rimozione `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `model: "sonnet"`, `ponytail` spento in Claude e Antigravity (`config.json`), `permissions.deny` per `agy`, rimozione `write-docs` e `i-have-adhd`, junction delle 5 skill + `agents/`, ramo `Aggiorna` con `check-updates.py` / `git ls-remote`.
  - `SETUP-REPO.md`: allineare il check iniziale su `Repo versionato` vs `Repo ibrido` e su `AGENTS.md` + `tests/run.py`.
- `docs/index.mdx`, `docs/docs.json`, `docs/SUMMARY.md` e nuova guida `docs/skills.md`:
  - Aggiornare catalogo completo di tutti i file tracciati in `docs/index.mdx` (zero file mancanti, zero `flow-prompts.md`).
  - Aggiungere `docs/skills.md` (registrata in `docs/docs.json` e `docs/SUMMARY.md`) che spiega tutte le skill del repo (`aim-higher`, `junior-deep-docs`, `ui-ux-doctrine`, `flow-design`, `implement-ticket`), le skill esterne chiave e quelle escluse dal flusso (`/implement`, `/implement-spec`), con prompt d'esempio in italiano semplice e zero AI slop o emoji.

## Acceptance criteria

- [ ] Nessun riferimento residuo a `flow-prompts.md`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW=400000`, `Review: single`, `Review: flash`, `righe 1..N`, `Livello 1..4`, emoji o nomi aziendali/Delphi in tutto il repo.
- [ ] Ogni file in `just-develop` compare nel catalogo di `docs/index.mdx`, e ogni pagina in `docs/docs.json` e `docs/SUMMARY.md` esiste su disco.
- [ ] `docs/skills.md` elenca tutte e 5 le skill in `skills/`.

## Ipotesi

- Il banner `docs/banner.png` e le pagine `docs/agents/*` restano invariate salvo link di navigazione.

## Answer

- **File creati/modificati:**
  - `AGENTS.md`
  - `README.md`
  - `GUIDE.md`
  - `GLOSSARY.md`
  - `DECISIONS.md`
  - `SETUP.md`
  - `SETUP-REPO.md`
  - `docs/index.mdx`
  - `docs/docs.json`
  - `docs/SUMMARY.md`
  - `docs/skills.md`
- **Verifica eseguita (dopo l'ultima modifica):**
  - Comando: `python -X utf8 -I C:\Works\GIT\Agents\config\just-develop\tests\run.py`
  - Output copiato: `ok`
  - Exit code: `0` (`JD_EXIT:0`)
  - Pre-commit/Commit: non eseguito (commit finale riservato dopo prova manuale/ok utente; `Status` mantenuto `ready-for-agent`).
- **Tentativi:** 2 (implementazione `@token-pro-2` + 1 passata fix Stage 4).
- **Finding review:** 2 (2 fixed, 0 discarded) — rimozione meta-aperture in `docs/index.mdx` e `docs/skills.md` con aggiunta `.gitattributes` nel catalogo, separazione di `deepwiki` e `frontend-design` in sezione opzionale in `docs/skills.md`.
