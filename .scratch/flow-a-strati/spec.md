Status: ready-for-agent

# Spec 1: regole a strati, setup unico dei repo, controlli automatici

## Il problema

Ogni agente, in ogni sessione, legge per intero le regole sempre attive: circa 18 KB oggi, di cui quasi 15 KB sono `flow.md`. Un esecutore Gemini che implementa un ticket legge anche le parti che servono solo a Opus (ingresso, grilling, tabella di consegna), e Opus legge i dettagli di review e commit che servono solo all'esecutore. Anthropic scrive che le regole lunghe consumano contesto e sono seguite peggio (pagina *Memory*, letta il 10/11/2026); Google tratta le regole `always_on` come testo che entra a ogni turno (pagina *Rules*, letta il 10/11/2026).

Il setup dei repo copre male tre casi: un repo nuovo passa da un'analisi che cerca trascrizioni che non esistono; un repo dove l'AI è già stata usata non ha un audit che lo riallinei; un repo condiviso con colleghi, dove il materiale degli agenti resta locale, non è previsto, e lì la regola «il ticket entra nel commit» non può funzionare.

Alcune regole che contano davvero sono solo prosa: nessun controllo impedisce a un agente di creare un branch o di gonfiare un file di regole.

## La soluzione

- `flow.md` diventa il **nucleo**: le poche regole che ogni agente legge sempre. Il resto del flusso si sposta in due skill che si aprono quando servono: una per la progettazione con Opus, una per l'implementazione di un ticket.
- `SETUP-REPO.md` diventa un percorso unico per qualsiasi repo: chiede se è **ibrido** o **versionato**, analizza la storia quando ci sono tracce di AI, fa l'audit e la pulizia, poi posa le **fondamenta**.
- Due controlli automatici: un hook che lascia i branch solo all'utente e un hook che blocca i file per agenti troppo grandi, in ogni repo.
- Le pratiche raccolte dagli autori entrano nelle due skill.

## Storie

1. Come utente, voglio che un esecutore Gemini legga solo le regole del suo passo, così spende token sul ticket e non sulla progettazione.
2. Come utente, voglio che Opus apra le istruzioni di progettazione quando lancio `/grill-with-docs`, `/to-spec`, `/to-tickets` o `/wayfinder`, senza che io debba ricordarglielo.
3. Come utente, voglio che scrivere `Implementa il ticket 3` basti perché l'esecutore apra le istruzioni di implementazione.
4. Come utente, voglio che `Rivedi il ticket 3` apra le stesse istruzioni, per lanciare la Doppia Review a mano.
5. Come utente, voglio che il nucleo resti sotto un tetto di dimensione, così non ricresce regola dopo regola.
6. Come utente, voglio che un commit si fermi se un file letto dagli agenti supera 5.000 token, con un messaggio che dice cosa accorciare.
7. Come utente, voglio solo un avviso, non un blocco, quando committo un file di codice grande, così un fix di una riga su un file legacy passa.
8. Come utente, voglio lo stesso controllo di dimensione in ogni mio repo, anche dove il materiale degli agenti è escluso da git.
9. Come utente, voglio che nessun agente crei o cambi branch: il branch della spec lo creo io.
10. Come utente, voglio che il blocco sui branch valga sia in Claude Code sia in Antigravity, con un messaggio che dice «lo crei tu».
11. Come utente, voglio che il setup di un repo mi chieda per prima cosa se è condiviso con colleghi.
12. Come utente con un repo condiviso, voglio che regole, spec, ticket, skill e `docs/` restino solo sulla mia macchina, esclusi con l'exclude locale.
13. Come utente con un repo condiviso, voglio che dopo il commit l'AI scriva da sola nel ticket `Status: resolved` e `Commit: <hash>`, così ritrovo il commit di ogni ticket.
14. Come utente con un repo versionato, voglio ritrovare il commit di un ticket con il comando git scritto nel ticket stesso.
15. Come utente, voglio che un repo dove l'AI è già stata usata (chat, trascrizioni, file `.md` per agenti) venga analizzato prima di toccare qualsiasi cosa.
16. Come utente, voglio che l'analisi legga trascrizioni, chat e ragionamenti di quel repo con subagenti economici, e mi dia una mappa che regge a `/clear`.
17. Come utente, voglio sapere dove gli agenti perdono tempo a cercare informazioni in quel repo, per renderlo più facile da navigare.
18. Come utente, voglio che, se il repo ha PR con commenti, il setup proponga le regole che i revisori ripetono più spesso.
19. Come utente, voglio un audit che confronti un repo già avviato con la versione attuale del setup e mi proponga una pulizia, dopo un tag di sicurezza.
20. Come utente, voglio che i ticket già chiusi restino come sono: sono storia.
21. Come utente con un repo nuovo, voglio `AGENTS.md` con un comando dei test che so funzionare, perché un test prima fallisce e poi passa.
22. Come utente con un repo esistente senza test, voglio test di caratterizzazione sul modulo che toccherò per primo, non su tutto il repo.
23. Come utente, voglio che una documentazione esistente in un altro formato venga migrata in `docs/` invece di essere riscritta da zero.
24. Come utente, voglio che nella sezione `## Answer` di ogni ticket ci siano i tentativi e i finding della review, per capire nel tempo quali ticket costano di più.
25. Come utente, voglio che le review usino il modello del ticket, così un ticket Argon è controllato da Argon.
26. Come utente, voglio che l'esecutore non modifichi, salti o disattivi i test esistenti, e li faccia solo passare.
27. Come utente, voglio che a inizio ticket l'esecutore legga il ticket e `git log` e lanci i test esistenti prima di cambiare codice.
28. Come utente, voglio che la tabella di consegna metta prima i ticket più rischiosi.
29. Come utente, voglio che il grilling chieda sempre «come rendiamo questa modifica verificabile del tutto?».
30. Come utente, voglio che a fine spec mi venga proposto `/codebase-design` con il test di cancellazione, da lanciare se voglio.
31. Come collega che installa il setup, voglio che le due skill nuove arrivino a Claude Code e ad Antigravity come le altre skill del repo.
32. Come utente, voglio che il flusso nomini i ruoli (progettista, esecutore, revisore) accanto ai modelli, così cambiare il modello di un ruolo costa una riga.
33. Come utente, voglio poter progettare anche con Gemini 4 Carbon in Antigravity, con la stessa skill `flow-design` che usa Opus in Claude Code.
34. Come utente, voglio che il contrarian resti su Claude anche quando progetta Carbon, così il controllo arriva da un'altra famiglia di modelli.
35. Come manutentore del setup, voglio che ogni scelta di questa spec abbia la sua voce in `DECISIONS.md`, con motivo, fonte e data.

## Decisioni di implementazione

**Nucleo e skill**
- `flow.md` resta il file del nucleo, con lo stesso nome, così la sincronizzazione e i riferimenti non cambiano. Contiene: ruoli e modelli in breve, lingua e fonti, il ciclo in una decina di righe, la regola sui branch, i commit e i puntatori alle due skill.
- Skill `flow-design` (per Opus): ingresso, grilling, spec, ticket, contrarian, tabella di consegna, guida alla scelta dei modelli e degli esecutori. La descrizione la fa scattare con `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/wayfinder` e con la richiesta della tabella dei ticket.
- Skill `implement-ticket` (per l'esecutore): routine di inizio ticket, implementazione, aggiornamento di `docs/`, Doppia Review, `## Answer`, Walkthrough, prova manuale, commit e chiusura del ticket nelle due modalità. La descrizione la fa scattare con `Implementa il ticket <N>` e `Rivedi il ticket <N>`.
- `flow-prompts.md` confluisce nelle due skill e viene tolto; ogni riferimento a lui in README, GUIDE, `docs/index.mdx` e `flow.md` punta alla skill giusta.
- Le due skill vivono nella cartella delle skill del repo e arrivano ai due agenti tramite i link già descritti in `SETUP.md`. La sincronizzazione non cambia.
- Tutto il testo per agenti si scrive con `/writing-for-agents` e in inglese; il nucleo resta in italiano come oggi.

**Ruoli e modelli**
- Il flusso parla di ruoli: **progettista** (grilling, spec, ticket, diagnosi), **esecutore** (implementa un ticket), **revisore** (Doppia Review e contrarian). Accanto a ogni ruolo c'è il modello che lo fa oggi, in un'unica tabella nel nucleo: cambiare modello vuol dire cambiare quella tabella.
- `flow-design` si scrive senza strumenti di un solo agente: deve funzionare con Opus in Claude Code e con Gemini 4 Carbon in Antigravity. Dove un passo esiste solo in un agente (il contrarian, i comandi di Pocock lanciati dall'utente), la skill dice cosa fare nell'altro.
- Il contrarian resta solo in Claude Code: quando progetta Carbon, l'utente lo lancia da Claude sui ticket scritti in `.scratch/`.

**Controllo di dimensione**
- Uno script autonomo, riusabile in ogni repo, stima i token come byte diviso 4 (il metodo del «Prompt of the Day» di Matt Pocock, data `non verificato`).
- Blocca: un file letto dagli agenti (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, ogni `SKILL.md`, le pagine di `docs/`) sopra 5.000 token; i file sempre attivi oltre un tetto totale. Tetto iniziale: 12.000 byte, circa 3.000 token, da rivedere dopo aver misurato il nucleo riscritto.
- Avvisa soltanto: un file di codice in stage sopra 5.000 token.
- Repo versionato: lo script è versionato e lo lancia l'hook pre-commit del repo, nel sistema di hook che il repo ha già (husky, pre-commit, lefthook) oppure in una cartella di hook versionata. In questo repo lo lancia `tests/run.py`, che il pre-commit esegue già.
- Repo ibrido: l'hook sta in `.git/hooks/pre-commit`, locale; i file per agenti si leggono dal disco, perché non entrano mai nello stage.

**Branch solo all'utente**
- Entrambi gli hook git (Claude Code e Antigravity) bloccano la creazione e il cambio di branch: `git switch` con `-c`/`-C` o verso un altro branch, `git checkout -b`/`-B`/`--orphan` e il checkout di un branch, `git branch <nome>`, `git worktree add` con `-b`/`-B`. Il messaggio dice che il branch lo crea l'utente.
- Il checkout di file resta governato dalle regole che ci sono già.
- Gli hook sono un'area a rischio (`AGENTS.md`): questo pezzo è un ticket a parte con `Review: double`.

**Setup unico dei repo**
- Primo passo: chiedere se il repo è ibrido o versionato e scriverlo nell'`AGENTS.md` del repo.
- Il repo ha una storia se ci sono tracce di AI: trascrizioni Claude o Gemini, memorie, conoscenza Gemini, file `.md` per agenti.
- Con storia: analisi con subagenti. Un subagente Haiku elenca e conta sessioni e memorie; un subagente Sonnet ogni circa 10 sessioni legge trascrizioni, chat e ragionamenti (quando ci sono) e riporta fatti con citazioni brevi; Opus unisce e salva la mappa nella cartella `.scratch/` del setup del repo. L'analisi cerca anche dove gli agenti perdono tempo a cercare informazioni e, se il repo ha PR con commenti leggibili con `gh`, le regole che i revisori ripetono.
- Audit, quando il repo è già avviato: `CLAUDE.md` con solo `@AGENTS.md`; `AGENTS.md` con verifiche, aree a rischio e un comando dei test provato; ticket aperti con `Review:`, `Esecutore:` e `## Answer`; `docs/` in struttura Mintlify; nessuna skill locale che duplica una globale. I ticket chiusi non si toccano.
- La pulizia riusa i passi di Allinea che esistono già: tag `pre-cleanup`, materiale in `archive/`, ritorno solo di ciò che l'utente sceglie.
- Fondamenta, per ogni repo, saltando ciò che c'è già: `AGENTS.md` con il comando dei test provato da un test che fallisce e poi passa; test di caratterizzazione sul primo modulo da toccare, se il repo non ha test; `docs/` (locale nel repo ibrido) partendo dal catalogo dei file con `junior-deep-docs`, o migrata con la skill `mintlify` se esiste in un altro formato; l'hook di dimensione secondo la modalità; `/setup-matt-pocock-skills`, che lancia l'utente.

**Chiusura del ticket**
- Repo ibrido: subito dopo il commit l'AI scrive nel ticket `Status: resolved` e `Commit: <hash>`, con l'hash preso da git.
- Repo versionato: come oggi, `Status: resolved` e `## Answer` entrano nello stesso commit; nel ticket c'è il comando git che restituisce il suo commit. Un commit non può contenere il proprio hash, perché l'hash si calcola dal contenuto.
- `## Answer` aggiunge `Tentativi: <N>` e `Finding review: <N> (<corretti>, <scartati>)`. La quota non si annota: la segue l'utente.

**Review**
- Le tre review restano `inherit`: Google definisce `inherit` come il modello di chi le lancia (pagina *Subagents*, letta il 10/11/2026). La frase che lo dava per non definito si corregge. Scartata la review su Flash: su un ticket Argon la review è l'unico giudice di errori che passano i test.

**Pratiche degli autori**
- In `implement-ticket`: i test esistenti non si modificano, non si saltano e non si disattivano (Anthropic, *Effective harnesses for long-running agents*, 26/11/2025); a inizio ticket si leggono ticket e `git log` e si lanciano i test esistenti (stesso articolo).
- In `flow-design`: i ticket più rischiosi per primi nella tabella di consegna (Matt Pocock, *Tips for AI coding with Ralph Wiggum*, 8/1/2026); nel grilling la domanda «come rendiamo questa modifica verificabile del tutto?» (Pocock, «Prompt of the Day», data `non verificato`); a fine spec, la proposta di `/codebase-design` con il test di cancellazione, che lancia l'utente.

**Decisioni**
- Ogni blocco qui sopra ha la sua voce in `DECISIONS.md`, comprese le scelte scartate (review su Flash, quota nella Answer).

## Decisioni sui test

- Un buon test qui controlla un comportamento visibile: un comando bloccato o lasciato passare, un commit fermato o lasciato passare, un file copiato o no. Non controlla il testo esatto delle regole.
- La giuntura è una sola: `tests/run.py`, che il pre-commit lancia già. Dentro ci sono già i casi dei due hook git (lo stesso elenco di comandi provato su Claude Code e su Antigravity) e quelli della sincronizzazione, in cartelle temporanee: i nuovi test seguono lo stesso schema.
- Hook sui branch: ogni forma di creazione o cambio di branch elencata sopra è bloccata in entrambi gli hook; il checkout di un file e i comandi git innocui passano ancora.
- Controllo di dimensione: un file per agenti sopra soglia ferma il controllo; un file di codice sopra soglia dà solo l'avviso; il tetto del nucleo ferma il controllo; in modalità ibrida un file per agenti escluso da git viene letto dal disco e controllato. Il controllo gira anche sui file reali di questo repo.
- Ogni test nuovo si prova rompendo apposta il codice che controlla e vedendolo fallire.
- Le skill e il nucleo non hanno test sul contenuto. Le verifiche sono: il controllo di dimensione, `scripts/sync-from-claude.py --check`, e una prova manuale in Antigravity (scrivere `Implementa il ticket <N>` e vedere la skill aperta) e in Claude Code (lanciare `/to-tickets` e vedere `flow-design` aperta). `agy` non si lancia dal terminale: la prova la fa l'utente nell'app.
- I ruoli si provano a mano: con `flow-design` aperta in Antigravity con Carbon, il grilling fa le domande a giri e i ticket escono nel formato di `/to-tickets`.
- Il setup unico si prova a mano su un repo usa e getta, una volta in modalità ibrida e una in versionata.

## Fuori da questa spec

- Tutto ciò che è della Spec 2: guida alle skill, letture degli autori, pagina sui graph e sulla memoria, sezione «invarianti e scelte» di `junior-deep-docs`, riga `Superata da:` in `DECISIONS.md`.
- La misura della quota.
- Un'alternativa a Gemini quando la sua quota finisce.
- Un controllo del lavoro di Gemini fatto da un modello Claude.
- Strumenti a grafo per il codice e i cicli AFK automatici.

## Note

- Che Antigravity apra `implement-ticket` quando l'utente scrive `Implementa il ticket <N>` dipende da come il modello legge la descrizione della skill: `non verificato` finché non lo prova l'utente. Se non la apre, il nucleo tiene un puntatore esplicito alla skill.
- Uno studio dell'ETH (Gloaguen et al., arXiv 2602.11988, febbraio 2026, letto solo tramite riassunto) ha trovato che i file di contesto sempre caricati non alzano i compiti riusciti e costano circa il 20% in più: è un'altra ragione per un nucleo piccolo, non una misura su questo flusso.
- I termini Nucleo, Fondamenta, Repo ibrido e Repo versionato sono già in `GLOSSARY.md`.
- I branch li crea l'utente: anche il branch di questa spec.
- La Spec 2 è già scritta in `.scratch/guida-e-conoscenza/spec.md`; la prova di Gemini 4 Carbon come progettista si fa sui suoi ticket (`/to-tickets` in Antigravity). Il giudice è il confronto con questa spec: obiezioni del contrarian accolte, ticket rifatti, finding della review per ticket. Su Carbon: disponibile per gli abbonati Ultra in Antigravity dal 10/11/2026 (Google, *Gemini 4 Carbon is now available*); negli indici è alla pari con Opus 5.5 (Vals AI, letto il 10/11/2026); è costruito su Argon (scheda del modello DeepMind), quindi progettista ed esecutore sarebbero della stessa famiglia.
