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
Il modello veloce di Google (`Gemini 4 Hydrogen`) su Antigravity Pro e Ultra, usato come esecutore di default a livello `Low` (ritocchi meccanici `<= 30` righe) o `Medium` (quando compilatore e test catturano gli errori).

**Carbon**:
Il modello avanzato di Google (`Gemini 4 Carbon`) su Antigravity Ultra (Ufficio), usato per ticket critici (`C = 1`, errori invisibili ai test) e come Progettista alternativo in Antigravity.

**Argon**:
Il modello avanzato di Google (`Gemini 4 Argon`) su Antigravity Pro (Casa), usato per ticket critici (`C = 1`) dove Carbon non è disponibile.

**Progettista**:
Il ruolo di chi esplora, fa grilling, scrive spec, ticket e diagnosi dei bug (`Sonnet 5.5` o `Opus` in Claude Code; `Carbon` su Antigravity Ultra).

**Esecutore**:
Il ruolo di chi implementa un ticket seguendo `implement-ticket`: `Hydrogen Low|Medium`, `Carbon Medium` (Ufficio/Ultra) o `Argon Medium` (Casa/Pro), secondo la riga `Esecutore:`.

**Revisore**:
Il ruolo di chi verifica il lavoro di altri: i tre subagenti paralleli di `Review: double` (`Standards`, `Spec`, `ponytail-review` su `inherit`) e il `contrarian` sui ticket.

**Antigravity**:
L'IDE e app desktop di Google in cui esegui i ticket con `Hydrogen`, `Carbon` (Ultra) o `Argon` (Pro).

**Subagente**:
Un'altra istanza di AI lanciata con un contesto pulito per un compito mirato (ricerca ampia, `contrarian` o i tre assi di `Review: double`).

**Livello di ragionamento**:
Quanto a fondo ragiona il modello prima di rispondere (`Low`, `Medium`, `High` in Antigravity; `medium`, `high` in Claude Code).

## Il percorso di un lavoro

**Flusso**:
L'insieme di passi in `flow.md`, `flow-design` e `implement-ticket` che porta un'idea a un commit verificato.

**Ingresso**:
La regola di `flow-design` con cui il Progettista sceglie da quale percorso partire davanti a una richiesta nuova.

**Via**:
La riga `Via: /<skill>, perché <segnale>. Correggimi se sbaglio.` con cui il Progettista propone il percorso iniziale.

**Aim-higher**:
La ricerca iniziale su codice, documentazione ufficiale e web per spiegare principio, causa e giudice esterno proponendo 2-3 opzioni (`(Consigliata)` prima).

**Grilling**:
L'intervista a giri in cui l'AI scioglie ogni dubbio della frontiera decisionale prima di scrivere la spec.

**Wayfinder**:
La modalità per lavori grandi o nebbiosi (`/wayfinder`): costruisce una mappa delle decisioni in `.scratch/` e le risolve una per volta.

**Spec**:
Il documento `.scratch/<lavoro>/spec.md` che fissa problema, soluzione, storie, seam di test e decisioni prima dei ticket.

**Ticket**:
Una fetta verticale piccola e autonoma salvata in `.scratch/<lavoro>/issues/<NN>-<slug>.md`, con file e simboli verificati, metrica `S/G/C`, `Review:`, `Esecutore:` e criteri di accettazione eseguibili.
_Avoid_: task generico senza contratto.

**Metrica S/G/C**:
Tre bit binari (`0|1`) assegnati dal Progettista: `S` (Stato persistente o schema dati), `G` (Forza del Giudice: `0` se compilatore e test bastano, `1` se serve prova UI/audio/runtime), `C` (Concorrenza, sicurezza, hook o script sync). `0/0/0` seleziona `Review: quick`; qualsiasi bit `= 1` seleziona `Review: double`.

**Nucleo**:
Il file compatto `flow.md` (`<= 3.000 B`) caricato a ogni turno con ruoli, modelli, lingua, branching, puntatori e checklist invariante di chiusura ticket.

**Fondamenta**:
La base che ogni repo riceve al setup (`SETUP-REPO.md`): `AGENTS.md` con comando dei test provato, aree a rischio, `docs/` e skill collegate.

**Repo ibrido**:
Un repo condiviso con colleghi dove regole, spec, ticket, skill e `docs/` restano solo sulla tua macchina via `.git/info/exclude`; dopo il commit l'AI scrive nel ticket `Status: resolved` e `Commit: <hash>`.
_Avoid_: repo misto.

**Repo versionato**:
Un repo in cui anche il materiale degli agenti è tracciato da Git (come `just-develop`); `Status: resolved` e `## Answer` entrano nello stesso commit del ticket.

**Contrarian**:
L'agente in Claude Code (`antigravity: false`) che esegue il premortem sui ticket prima dell'implementazione, portando solo obiezioni sostenute da una prova riapribile.

**Premortem**:
Immaginare che i ticket implementati alla lettera abbiano già prodotto un errore per trovarne le cause prima di scrivere codice (Gary Klein, 2007).

**Triage**:
Valutare una segnalazione esterna o PR, verificarne la riproduzione e portarla a `ready-for-agent`, `ready-for-human`, `needs-info` o `wontfix`.

**Implement**:
La fase governata da `skills/implement-ticket/SKILL.md`: pre-flight, modifiche mirate per file e simbolo, aggiornamento `docs/`, verifiche deterministiche, review binaria, `## Answer`, Walkthrough e commit.

**Review binaria (`quick` e `double`)**:
Due sole fasce di review a fine implementazione: `Review: quick` (0 subagenti, sola auto-verifica e check deterministici per ticket `0/0/0`) e `Review: double` (3 subagenti paralleli a contesto pulito su `inherit`: `Standards`, `Spec` e `ponytail-review`).

**Fix**:
La correzione autonoma in una sola passata dei soli difetti reali e lacune `docs/` confermati sul codice dopo la review, seguita da ri-esecuzione di build e test.

**Retro**:
La riflessione guidata (`/retro`, lanciata solo dall'utente) dopo un errore o bug reale per trasformare la causa in un hook, test o regola di `AGENTS.md`.

**Branching a 3 livelli**:
Convenzione `office|home/<tipo>/<slug>` tutta minuscola creata e integrata dall'utente con merge non-squash su `main` e cancellazione post-merge per lavorare tra due PC senza conflitti Git.

**Controllo silenzioso 8h/24h**:
Meccanismo `SessionStart` non bloccante (`session_check.py` + worker detached `background_checker.py` con lock kernel OS) che controlla ogni 8 ore il repo Git (inclusi file sporchi locali e `merge-tree`) e ogni 24 ore i repository delle skill installate via `git ls-remote`.

## Capire il codice e valutare la qualità

**Guida del Codice (`docs/` Mintlify + GitBook)**:
La documentazione in `docs/` (`docs.json`, `index.mdx`, `SUMMARY.md` e pagine di modulo), scritta secondo `junior-deep-docs`: cataloga i file tracciati e spiega catene di esecuzione, stato (con unità e thread), parametri e flag API.

**Walkthrough**:
Il riepilogo in 5 sezioni mostrato a fine ticket prima della prova manuale: effetto pratico, diagramma `flowchart TD`, tabella API/parametri/flag/unità, schede SMIG e prova HITL granulare.

**SMIG**:
I quattro punti della scheda di ogni passaggio chiave nel Walkthrough: **Dove siamo** (file e simbolo), **Meccanismo** (stato e variabili mosse), **Perché è fatto così**, **Occhio a / Gotcha**.

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
La cartella su disco dove vivono spec, ticket e output del `contrarian`, permettendo di aprire sessioni pulite tra fasi e ticket.

**`DECISIONS.md` e `NOTES.md`**:
I file di traccia dentro `.scratch/<lavoro>/` per decisioni di progetto e note con fonti; `DECISIONS.md` alla radice registra invece le decisioni del setup stesso.

**Fonte verificata**:
Il riferimento esatto di un'affermazione (documento ufficiale con data, autore con data, codice per file e simbolo o comando eseguito); in assenza di verifica si scrive `non verificato`.
