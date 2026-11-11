Status: ready-for-agent

# Spec 2: guida alle skill, letture degli autori, graph e memoria

Dipende dalla Spec 1 (`.scratch/flow-a-strati/spec.md`): la guida alle skill descrive anche `flow-design` e `implement-ticket`, che nascono lì.

## Il problema

Chi arriva su `just-develop` trova regole e decisioni, ma nessuna pagina che spieghi quali skill ha a disposizione, quando usarle e con quale prompt. Molte skill installate non sono nominate dal flusso (per esempio `handoff`, `wait-what`, `teach`, `improve-codebase-architecture`, `to-questionnaire`), e due (`implement`, `implement-spec`) sono vietate da `flow.md` senza che una guida lo dica a chi le vede nell'elenco.

Le pratiche che autori come Matt Pocock, antirez, Anthropic e altri pubblicano sono sparse in post, video e tweet. Il setup ne ha già preso molte senza dirlo, e non c'è un posto dove ritrovarle con la fonte.

Termini come "context graph", "code graph" o "memoria procedurale" circolano senza una spiegazione che li colleghi ai file che il setup usa davvero. Senza quel collegamento si sceglie alla cieca se adottare uno strumento.

Due lacune minori: una decisione sostituita da un'altra non lo dice (la 15 è stata superata dalla 30), e la guida del codice spiega cosa fa un modulo ma non quali regole deve sempre rispettare e perché è fatto così.

## La soluzione

- Una pagina che spiega ogni skill installata, ordinata per fase del flusso, con un prompt d'esempio da incollare.
- Una pagina di letture: per ogni autore, cosa propone, cosa il setup ne ha preso e dove, con link e data di lettura. Riassunti con parole nostre, mai copie.
- Una pagina su graph e memoria che spiega i concetti e li collega ai file del setup, e dice quale strumento vale la pena adottare (oggi nessuno) e perché.
- `junior-deep-docs` aggiunge a ogni modulo una sezione «invarianti e scelte».
- In `DECISIONS.md` una decisione sostituita riceve la riga `Superata da: N (data)`.

## Storie

1. Come nuovo utente, voglio una pagina che mi dica quali skill ho e quando usarle, così non devo leggere ogni `SKILL.md`.
2. Come nuovo utente, voglio le skill ordinate per fase del flusso (ingresso, progettazione, implementazione, review, documentazione, manutenzione), così trovo quella giusta per il momento in cui sono.
3. Come nuovo utente, voglio per ogni skill un prompt d'esempio pronto da incollare e cosa produce.
4. Come nuovo utente, voglio sapere quali skill lancio solo io (quelle con `disable-model-invocation`) e quali l'agente apre da solo.
5. Come nuovo utente, voglio sapere quali skill sono vietate nel flusso e perché (`implement`, `implement-spec`).
6. Come nuovo utente, voglio trovare anche le skill che il flusso non nomina (`handoff`, `wait-what`, `teach`, `improve-codebase-architecture`, `to-questionnaire`, `ask-matt`, `wizard`, `pr`, `research`), con il caso in cui servono.
7. Come nuovo utente, voglio sapere quali skill vengono dal plugin ponytail e come si usano.
8. Come manutentore, voglio che un test fallisca se una skill del repo manca dalla guida, così la guida non resta indietro.
9. Come utente, voglio una pagina con le pratiche degli autori e la fonte di ognuna, così capisco da dove viene ogni regola del setup.
10. Come utente, voglio vedere per ogni pratica se il setup la usa già, dove, o perché l'ha scartata.
11. Come utente, voglio l'elenco dei «Prompt of the Day» di Matt Pocock trovati, con il link e la skill che usano.
12. Come utente, voglio sapere quali fonti sono state lette per intero e quali solo da estratti, così so quanto fidarmi.
13. Come utente, voglio che nessun testo degli autori sia copiato, perché il repo è pubblico.
14. Come utente, voglio capire cos'è un context graph e a cosa corrisponde nel setup.
15. Come utente, voglio capire cos'è un code graph, cosa promette e cosa è stato misurato davvero.
16. Come utente, voglio capire i tipi di memoria di un agente (procedurale, semantica, episodica, di lavoro) e quale file del setup fa da ciascuna.
17. Come utente, voglio capire gli schemi di lavoro degli agenti di Anthropic e quale parte del flusso usa ciascuno.
18. Come utente, voglio capire il flusso come un grafo di stati: da quale stato a quale passa un ticket.
19. Come utente, voglio sapere quando un grafo di build come quello di Nx serve (monorepo) e quando no.
20. Come utente, voglio un elenco di letture di approfondimento per i concetti che non adottiamo.
21. Come utente, voglio sapere perché oggi non adottiamo nessuno strumento a grafo, e cosa dovrebbe cambiare per adottarlo.
22. Come junior che legge `docs/`, voglio per ogni modulo le regole che deve sempre rispettare e il perché delle scelte, così cambio il codice senza rompere il design.
23. Come utente, voglio che una decisione sostituita lo dica, con il numero di quella nuova e la data, così non seguo una regola vecchia.
24. Come utente, voglio una spiegazione di come si divide una PR "senza ritorno" in due, con un feature flag.
25. Come utente che arriva dal README, voglio un link alla guida delle skill tra le prime righe.

## Decisioni di implementazione

**Pagine nuove in `docs/`** (Mintlify, con la navigazione aggiornata e compatibili con `SUMMARY.md`): skill, letture, graph e memoria. Scritte per una persona, in italiano semplice, secondo `junior-deep-docs` e `humanizer`. Il testo che leggono gli agenti (skill, regole) si scrive con `/writing-for-agents`.

**Guida alle skill**
- Copre: le skill di questo repo (comprese `flow-design` e `implement-ticket` della Spec 1), quelle installate da `SETUP.md` (mattpocock/skills, humanizer, skill-creator, pdf, find-skills, mintlify) e le skill del plugin ponytail (`ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`).
- Per ogni skill: fase, quando usarla, chi la lancia (tu o l'agente), un prompt d'esempio, cosa produce. Le informazioni si leggono dal `SKILL.md` di ogni skill, non dalla memoria.
- Le skill vietate (`implement`, `implement-spec`) compaiono con il motivo scritto in `flow.md`.
- Il test di copertura controlla solo le skill del repo: l'elenco delle skill esterne cambia con gli aggiornamenti e lo ricontrolla il ramo Aggiorna di `SETUP.md`.

**Letture**
- Per ogni fonte: autore, titolo, link, data di pubblicazione, data di lettura, la pratica in una o due righe con parole nostre, e dove il setup la usa o perché no. Al massimo una citazione breve per fonte.
- Ogni fonte che la ricerca ha visto solo da estratto (vedi «Fonti raccolte») si legge per intero durante il ticket; se non si riesce resta `non verificato`.

**Graph e memoria**
- Contenuto, in quest'ordine: gli schemi di Anthropic collegati al flusso; il flusso come grafo di stati; i tipi di memoria collegati ai file del setup; i fatti con una data di validità; grafo dall'AST contro grafo costruito da un LLM; i grafi di build per i monorepo; il context graph; il code graph e la sua unica misura; letture di approfondimento.
- Conclusione: nessuno strumento da adottare oggi, perché LSP e ricerca testuale coprono la struttura del codice e un database a grafo è un altro sistema da mantenere. Si riconsidera per un repo grande o un monorepo.

**`junior-deep-docs`**
- Per ogni modulo, una sezione «invarianti e scelte»: le regole che il modulo deve sempre rispettare e perché il design è questo. È l'idea di antirez di descrivere il design in parole semplici, così persone e agenti partono dal design e non dal codice.

**`DECISIONS.md`**
- Una decisione sostituita riceve `Superata da: N (gg/mm/aaaa)` sotto il titolo, e il suo testo resta com'è. Da applicare subito: la 15 è superata dalla 30 per la regola su file e simbolo.

**PR "senza ritorno"**
- Spiegata nella guida alle skill o nelle letture: la modifica irreversibile si divide in una PR reversibile e una successiva, con un feature flag. Fonte: un «Prompt of the Day» di Pocock visto solo da LinkedIn, `non verificato`.

**Decisioni**
- Ogni blocco qui sopra ha la sua voce in `DECISIONS.md`.

## Decisioni sui test

- Un buon test controlla un comportamento: la guida contiene ogni skill del repo, la navigazione di Mintlify punta a pagine che esistono.
- La giuntura è `tests/run.py`, come nella Spec 1. Test nuovi: ogni cartella delle skill del repo compare nella pagina delle skill; ogni pagina elencata nella navigazione esiste. Ogni test si prova rompendo apposta ciò che controlla.
- Il controllo di dimensione della Spec 1 vale anche per le pagine nuove (5.000 token per file).
- Le pagine si verificano a mano con `npx mint dev`, che l'utente lancia e guarda nel browser.

## Fuori da questa spec

- Adottare uno strumento a grafo (server MCP per il code graph, database a grafo).
- Cicli AFK automatici e sandbox (Pocock, Ralph).
- `/software-factory` e altre infrastrutture da team.
- Copiare testi, video o post degli autori.
- Tutto ciò che è della Spec 1.

## Note

- La prova di Gemini 4 Carbon come progettista, prevista dalla Spec 1, si fa su `/to-tickets` di questa spec: la spec è scritta ora per non perdere il contesto della ricerca.
- Ricerche fatte il 10/11/2026 da subagenti Sonnet e Haiku; gran parte delle pagine è stata vista solo tramite estratti. Il ticket di ogni pagina deve rileggere le fonti.

## Fonti raccolte (10/11/2026)

Legenda: **letto** = pagina letta; **estratto** = visto solo nei risultati di ricerca o in riassunti, da rileggere.

**Autori e pratiche**
- Anthropic, Justin Young, *Effective harnesses for long-running agents*, 26/11/2025, https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents — letto. Elenco di funzioni che partono tutte come non riuscite, l'agente cambia solo lo stato e non tocca i test; routine di inizio sessione; un file di avanzamento. Nel setup: Spec 1.
- Anthropic, *How we built our multi-agent research system*, 13/06/2025, https://www.anthropic.com/engineering/built-multi-agent-research-system — letto. Più agenti costano circa 15 volte una chat; convengono su compiti di valore e molto paralleli; il codice lo è meno della ricerca.
- Anthropic, *Effective context engineering for AI agents*, 29/09/2025, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — letto. Il contesto è un budget di attenzione; il più piccolo insieme di token utili; caricare al momento giusto.
- Anthropic, *Building effective agents*, 12/2024, https://www.anthropic.com/research/building-effective-agents — estratto. Schemi: prompt chaining, routing, parallelizzazione, orchestrator-workers, evaluator-optimizer.
- Matt Pocock, repo https://github.com/mattpocock/skills — letto. Skill lanciate dall'utente e skill lanciate dal modello; grilling a ogni modifica; `improve-codebase-architecture` ogni pochi giorni.
- Matt Pocock (autore probabile), *5 Agent Skills I Use Every Day*, aggiornato 16/03/2026, https://www.aihero.dev/5-agent-skills-i-use-every-day — letto. Grill, poi spec dalla conversazione, poi ticket a fette verticali; codice disordinato porta output disordinato.
- Matt Pocock (autore probabile), *Tips for AI coding with Ralph Wiggum*, aggiornato 08/01/2026, https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum — letto. HITL una volta poi AFK; file di avanzamento; ticket più rischiosi per primi; standard di qualità espliciti.
- antirez, *Coding with LLMs in the summer of 2025 (an update)*, estate 2025, https://antirez.com/news/154 — letto. Niente vibe coding sul lavoro serio; tanto contesto al modello; modelli più forti; lui sposta il codice a mano senza agenti (non adottato).
- antirez, *Control the ideas, not the code*, circa 13/07/2026, https://antirez.com/news/169 — letto. Un documento di design per componente in parole semplici; scegliere design e obiettivi prima di chiedere il codice; la review del codice non scala con il volume prodotto dagli LLM.
- Simon Willison, *Agentic Engineering Patterns*, 23/02/2026, https://simonwillison.net/guides/agentic-engineering-patterns/ — estratto (solo titoli dei capitoli). Lanciare prima i test; TDD rosso e verde; test manuale fatto dall'agente; walkthrough lineari.
- Harper Reed, *My LLM codegen workflow atm*, 16/02/2025, https://harper.blog/2025/02/16/my-llm-codegen-workflow-atm/ — letto. Una domanda alla volta, poi `spec.md`; piano a piccoli passi e checklist tra le sessioni.
- Kent Beck, *Augmented Coding: Beyond the Vibes*, https://www.kentbeck.com/summaries/augmented-coding-beyond-the-vibes/ — estratto, data `non verificato`. TDD, attenzione alla deriva del design, rifiutare test disattivati e funzioni non chieste.
- Karpathy: fonti primarie non lette. Articolo secondario Signals, 26/05/2026, https://signals.aktagon.com/articles/2026/05/from-vibe-coding-to-agentic-engineering-andrej-karpathy-on-the-evolution-of-ai-assisted-programming/ — estratto. Il file `forrestchang/andrej-karpathy-skills` non è di Karpathy: è «derived from» le sue osservazioni.
- Gloaguen et al., ETH, *Evaluating AGENTS.md*, arXiv 2602.11988, 02/2026 — estratto. Nessun guadagno nei compiti riusciti, circa +20% di costo con file di contesto sempre caricati.

**«Prompt of the Day» di Matt Pocock** (X, @mattpocockuk; tutti estratto, date da riassunti)
1. `/codebase-design` moduli sottili e test di cancellazione — https://x.com/mattpocockuk/status/2105563604384915639 (circa 01/10/2026)
2. `/retro` sulle ultime 10 sessioni per la navigabilità — https://x.com/mattpocockuk/status/2105951409887949107 (circa 02/10/2026)
3. Aggiornare le skill alla v1.3 e rinominare CONTEXT.md in GLOSSARY.md — https://x.com/mattpocockuk/status/2106730768789602313 (circa 04/10/2026)
4. `/retro` sui commenti delle PR per `CODING_STANDARDS.md` — https://x.com/mattpocockuk/status/2107077843859513769 (circa 05/10/2026)
5. Hook pre-commit che blocca file oltre 5.000 token, token = byte/4 — https://x.com/mattpocockuk/status/2111708560715292675 (data `non verificato`)
6. `/grill-me` su una `/software-factory` — https://x.com/mattpocockuk/status/2113196247964074322 (data `non verificato`)
7. «Come rendiamo questa modifica verificabile del tutto?» — https://x.com/mattpocockuk/status/2118313863917564136 (circa 05/11/2026)
8. `/writing-for-agents` su un AGENTS.md disordinato — LinkedIn, link al post non trovato
9. Dividere una PR "senza ritorno" in due — LinkedIn, link al post non trovato

**Graph e memoria**
- Foundation Capital, Jaya Gupta e Ashu Garg, *AI's trillion-dollar opportunity: Context graphs*, 22/12/2025, https://ashugarg.substack.com/p/ais-trillion-dollar-opportunity-context — estratto. Traccia delle decisioni per agenti aziendali, non codice. Nel setup corrisponde a `DECISIONS.md`.
- Aider, *Building a better repository map with tree-sitter*, 22/10/2023, https://aider.chat/2023/10/22/repomap.html — letto. Mappa di definizioni e riferimenti, tagliata a un budget di token. Nessuna misura.
- Anthropic, Code intelligence plugins, https://code.claude.com/docs/en/plugins/code-intelligence — estratto. Un plugin avvia un language server: errori dopo ogni modifica, vai alla definizione, trova i riferimenti.
- Vogel et al., *Codebase-Memory*, arXiv 2603.27277, 28/03/2026 — letto. Grafo del codice via MCP contro ricerca e lettura: circa 1.000 contro 10.000 token per domanda, qualità 0,83 contro 0,92; un modello, un valutatore.
- *Reliable Graph-RAG for Codebases: AST-Derived Graphs vs LLM-Extracted Knowledge Graphs*, arXiv 2601.08773, 01/2026 — estratto. Grafo dall'AST 15 su 15, grafo da LLM 13 su 15, su 3 repo Java.
- Ouyang et al., *RepoGraph*, ICLR 2025, arXiv 2410.14684 — estratto. +32,8% relativo su SWE-bench Lite.
- *LocAgent*, arXiv 2503.09089, 03/2025 — estratto. Grafo per trovare il codice da cambiare.
- *CodexGraph*, NAACL 2025, arXiv 2408.03910 — estratto.
- Sourcegraph, *Precise Code Navigation* (SCIP) — estratto.
- Sumers et al., *Cognitive Architectures for Language Agents* (CoALA), arXiv 2309.02427 — solo abstract.
- LangChain, documentazione Memory, https://docs.langchain.com/oss/python/concepts/memory — letto. Memoria a breve termine, semantica, episodica, procedurale.
- LangChain, LangGraph *Graph API*, https://docs.langchain.com/oss/langgraph/graph-api — estratto. Flusso di un agente come grafo di stati.
- Rasmussen et al., Zep, *A Temporal Knowledge Graph Architecture for Agent Memory*, arXiv 2501.13956, 20/01/2025 — estratto. Fatti con un periodo di validità.
- Besta et al., *Graph of Thoughts*, AAAI 2024, arXiv 2308.09687 — estratto. Superato dai modelli che ragionano da soli.
- Nx, *nx ai agent skills* e *Why we deleted most of our MCP tools*, https://nx.dev/blog — estratto. Lanciare solo i test toccati in un monorepo.
