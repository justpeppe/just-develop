# Flusso di lavoro con gli agenti

Vocabolario dei ruoli, del ciclo ticket, della review binaria e degli strumenti di `just-develop`.

## Chi lavora

**Opus**:
Il modello Claude più capace (`Opus 5.5` su Claude Pro e Team), usato dal Progettista per decisioni difficili da invertire e `/diagnosing-bugs` complessi.

**Sonnet**:
Il modello predefinito in Claude Code (`Sonnet 5.5 medium`) per progettazione ordinaria e ricerche su documentazione e web (`Sonnet high` nei subagenti).

**Haiku**:
Il modello più piccolo di Claude, usato dai subagenti per cercare file e simboli nel codice.

**Hydrogen**:
Il modello veloce di Google (`Gemini 4 Hydrogen`) su Antigravity Pro e Ultra, usato come esecutore di default a livello `Low` (ritocchi meccanici `<= 30` righe senza nuovo stato) o `Medium` (quando compilatore e test catturano gli errori).

**Carbon**:
Il modello avanzato di Google (`Gemini 4 Carbon`) su Antigravity Ultra (Ufficio), usato per ticket `Review: triple` o errori invisibili ai test e come Progettista in Antigravity.

**Argon**:
Il modello avanzato di Google (`Gemini 4 Argon`) su Antigravity Pro (Casa), usato per ticket `Review: triple` o errori invisibili ai test dove Carbon non è disponibile.

**Progettista**:
Il ruolo di chi esplora, fa grilling, scrive spec, ticket e diagnosi dei bug (`Sonnet 5.5` o `Opus` in Claude Code; `Carbon Medium` su Antigravity).

**Esecutore**:
Il ruolo di chi implementa un ticket seguendo `implement-ticket`: `Hydrogen Low|Medium`, `Carbon Medium` o `Argon Medium`, secondo la riga `Esecutore:`.

**Revisore**:
Il ruolo di chi verifica il lavoro di altri: i tre subagenti paralleli di `Review: triple` (`Standards`, `Spec`, `diff-review` su `inherit`) e il subagente a contesto pulito del premortem su spec e ticket.

**Antigravity**:
L'IDE e app desktop di Google in cui esegui o progetti i ticket con `Hydrogen`, `Carbon` (Ultra) o `Argon` (Pro).

**Subagente**:
Un'altra istanza di AI lanciata con un contesto pulito per un compito mirato (ricerca ampia, premortem o i tre assi di `Review: triple`).

**Livello di ragionamento**:
Quanto a fondo ragiona il modello prima di rispondere (`Low`, `Medium`, `High` in Antigravity; `medium`, `high` in Claude Code).

## Il percorso di un lavoro

**Flusso**:
L'insieme di passi in `flow.md`, `flow-design` e `implement-ticket` che porta un'idea a un commit verificato.

**Ingresso**:
La regola di `flow-design` con cui il Progettista classifica una richiesta nuova dai fatti osservati e conferma il percorso prima di procedere.

**Aim-higher**:
La ricerca iniziale su codice, documentazione ufficiale e web per spiegare principio, causa e giudice esterno proponendo 2-3 opzioni (`(Consigliata)` prima).

**Grilling**:
L'intervista a giri in cui l'AI scioglie ogni dubbio della frontiera decisionale prima di scrivere la spec.

**Wayfinder**:
La modalità per lavori grandi o ambigui (`/wayfinder`): costruisce una mappa delle decisioni in `.scratch/` e le risolve una per volta.

**Spec**:
Il documento `.scratch/<lavoro>/spec.md` che fissa problema, soluzione, storie, seam di test e decisioni prima dei ticket.

**Ticket**:
Una fetta verticale piccola e autonoma salvata in `.scratch/<lavoro>/issues/<NN>-<slug>.md`, con file e simboli verificati, `Review: quick | triple` con motivo, `Esecutore:` e criteri di accettazione eseguibili.
_Avoid_: task generico senza contratto.

**Nucleo**:
Il file compatto `flow.md` (`<= 3.000 B`) caricato a ogni turno con ruoli, modelli, scelte, branching, puntatori e checklist invariante di chiusura ticket.

**Fondamenta**:
La base che ogni repo riceve al setup (`SETUP-REPO.md`): `AGENTS.md` con comando dei test provato, aree a rischio, `docs/` e skill collegate.

**Repo ibrido**:
Un repo condiviso con colleghi dove regole, spec, ticket, skill e `docs/` restano solo sulla tua macchina via `.git/info/exclude`; dopo il commit l'AI scrive nel ticket `Status: resolved` e `Commit: <hash>`.
_Avoid_: repo misto.

**Repo versionato**:
Un repo in cui anche il materiale degli agenti è tracciato da Git (come `just-develop`); `Status: resolved` e `## Answer` entrano nello stesso commit del ticket.

**Contrarian**:
L'agente opzionale in Claude Code (`agents/contrarian.md`, `antigravity: false`) per il premortem; nel flusso standard di `flow-design` il premortem gira in modo identico su Claude e Antigravity tramite subagente `inherit` o `/swarm` con brief inline.

**Premortem**:
Immaginare che spec o ticket implementati alla lettera abbiano già prodotto un errore per trovarne le cause prima di scrivere codice (Gary Klein, 2007), riportando solo obiezioni sostenute da una prova riapribile.

**Triage**:
Valutare una segnalazione esterna o PR, verificarne la riproduzione e portarla a `ready-for-agent`, `ready-for-human`, `needs-info` o `wontfix`.

**Implement**:
La fase governata da `skills/implement-ticket/SKILL.md`: pre-flight, modifiche chirurgiche per file e simbolo, aggiornamento `docs/`, verifiche deterministiche, review binaria, `## Answer`, Walkthrough e commit.

**Review binaria (`quick` e `triple`)**:
Due sole fasce di review a fine implementazione: `Review: quick` (0 subagenti, auto-verifica e check deterministici per modifiche meccaniche o coperte dai test) e `Review: triple` (3 subagenti paralleli a contesto pulito su `inherit`: `Standards`, `Spec` e `diff-review`).

**Fix**:
La correzione autonoma in una sola passata dei soli difetti confermati sul codice dopo la review, seguita da ri-esecuzione di build e test.

**Retro**:
La riflessione guidata (`/retro`, lanciata solo dall'utente) dopo un errore o bug reale per trasformare la causa in un hook, test o regola di `AGENTS.md`.

**Branching `<tipo>/<slug>`**:
Convenzione a 2 livelli tutta minuscola (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`) creata e integrata dall'utente con merge non-squash su `main` e `fetch.prune=true`.

**Controllo silenzioso 8h/24h**:
Meccanismo `SessionStart` non bloccante (`session_check.py` + worker detached `background_checker.py` con lock kernel OS) che controlla ogni 8 ore il repo Git (inclusi file sporchi locali e `merge-tree`) e ogni 24 ore i repository delle skill installate via `git ls-remote`.

## Capire il codice e valutare la qualità

**Guida del Codice (`docs/` Mintlify + GitBook)**:
La documentazione in `docs/` (`docs.json`, `index.mdx`, `SUMMARY.md` e pagine di modulo), scritta secondo `junior-deep-docs`: cataloga i file tracciati e spiega catene di esecuzione, stato (con unità e thread), parametri e flag API.

**Walkthrough**:
Il riepilogo in 5 sezioni mostrato a fine ticket prima della prova manuale: effetto pratico, diagramma `flowchart TD`, tabella API/parametri/flag/unità, passaggi chiave del codice e prova HITL accessibile in linguaggio naturale.

**Valutare criticamente**:
Accompagnare ogni vera scelta architetturale con **A favore**, **Contrario** e opzione **`(Consigliata)`** basata sui fatti.

**Finding**:
Un rilievo verificato della review con file, simbolo e gravità (`Must fix`, `Should fix`, `Nice to have`).

**Aree a rischio**:
Le parti di un repo dove un errore spegne la sicurezza o rompe l'ambiente (in `just-develop`: `hooks/` e `scripts/`).

## Strumenti e file di supporto

**Skill**:
Una scheda di istruzioni caricata solo quando serve (`flow-design`, `implement-ticket`, `aim-higher`, `junior-deep-docs`, `ui-ux-doctrine`).

**Hook**:
Uno script automatico eseguito da Claude, Antigravity o Git prima o dopo un'azione (blocco `git push`/`merge`, creazione o cambio branch, file privati di configurazione e ambiente, letture integrali `*.jsonl > 100 KB`, formato commit e sync automatico).

**MCP**:
Il ponte verso strumenti esterni configurato per macchina e condiviso (quando generico) in `mcp.json`.

**`.scratch/`**:
La cartella su disco dove vivono spec, ticket e output del premortem, permettendo di aprire sessioni pulite tra fasi e ticket.

**`DECISIONS.md` e `NOTES.md`**:
I file di traccia dentro `.scratch/<lavoro>/` per decisioni di progetto e note con fonti; `DECISIONS.md` alla radice registra invece le decisioni del setup stesso.

**Fonte verificata**:
Il riferimento esatto di un'affermazione (documento ufficiale con data, autore con data, codice per file e simbolo o comando eseguito); in assenza di verifica si scrive `non verificato`.
