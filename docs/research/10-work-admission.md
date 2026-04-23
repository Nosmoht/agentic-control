---
topic: work-admission
tier: B
date: 2026-04-23
status: draft
---

# Brief 10: Work-Admission und Queueing für aufmerksamkeits­limitierte Systeme

## Forschungsfrage
Was sagt die Literatur zu Queueing-Theorie, Admission Control und Work-Management
über aufmerksamkeits­limitierte Single-User-Systeme? Konkret: Welche empirisch
belastbaren WIP-Grenzen, welche Kosten des Kontextwechsels und welche Triage-Strategien
lassen sich auf ein persönliches Agentic-Control-System übertragen, in dem ein
einzelner Operator (Mensch) und mehrere LLM-Agenten zusammenarbeiten?

## Methodik
Iterative Web-Recherche (drei Zyklen, je zwei Query-Formulierungen) über
Queueing-Grundlagen, Kanban-WIP-Evidenz, Theory of Constraints, Kognitive-Last-
und Task-Switching-Forschung, Admission-vs-Reactive-Scheduling sowie Personal-
Kanban- und Deep-Work-Literatur. Quellen nach Tier 1 (peer-reviewed, Foundational
Books), Tier 2 (Praktikerliteratur mit Daten), Tier 3 (Blogs) bewertet. Zwei
Paper per Jina Reader eingesehen; ACM-Studie war paywalled, daher über
Sekundärquellen validiert.

## Befunde

### Queueing-Grundlagen (Little's Law, M/M/1)
Little's Gesetz (`L = λ · W`) beschreibt den Zusammenhang zwischen durchschnittlichem
WIP (`L`), Ankunftsrate (`λ`) und Durchlaufzeit (`W`) in jedem stabilen System und
setzt keine Verteilungsannahme voraus[^1]. Für ein Single-Operator-System ist die
praktische Konsequenz: Bei konstanter Kapazität erhöht jedes zusätzliche WIP-Item
proportional die Durchlaufzeit aller Items im System[^1][^2]. Formale M/M/1-Modelle
(Poisson-Ankünfte, exponentielle Bedienzeit) sind für die Dimensionierung eines
persönlichen Systems Overkill, weil weder Ankunfts- noch Bedienprozess stationär
sind. Relevant bleibt die qualitative Einsicht: Warteschlangen wachsen nichtlinear
mit der Auslastung, und ab etwa 80 % Kapazitäts­auslastung explodieren die
Durchlaufzeiten — ein Effekt, den Reinertsen für Produktentwicklung quantifiziert
und als "cost of queues" formalisiert hat[^3].

### Kanban und WIP-Limits
Anderson überträgt 2010 das Kanban-Prinzip aus Toyotas TPS (Ohno) auf
Wissensarbeit und macht explizite WIP-Grenzen zum Kernmechanismus seines
"Kanban Method"[^4]. Empirische Validierung ist dünner als die Praktiker­literatur
suggeriert: Eine quantitative Fallstudie über 8 000 Arbeitsitems in fünf Teams über
vier Jahre bestätigt den postulierten Zusammenhang `WIP ↓ ⇒ Lead Time ↓`, stellt
aber gleichzeitig fest, dass kein optimaler WIP-Wert aus realen Daten publiziert
ist[^5]. Für Solo-Arbeit empfiehlt Benson (Personal Kanban) einen Start-WIP von
drei gleichzeitigen Items als "Daumenregel" und erlaubt Anpassung nach Kontext
und Aufgabengröße[^6]. Reinertsen argumentiert ergänzend, dass bei hoher Varianz
kleine Batch-Größen und niedrige Queues den Cost-of-Delay dominieren[^3].

### Theory of Constraints
Goldratts TOC (1984) reduziert Durchsatz­optimierung auf einen einzigen Engpass und
fünf Fokussierungsschritte: Identify → Exploit → Subordinate → Elevate →
Repeat[^7]. Die zentrale Implikation für Einzelpersonen: Nicht-Engpässe zu
optimieren erhöht den Gesamtdurchsatz nicht; der Engpass muss bewusst geschützt
(Subordinate) und erst nach vollständiger Exploitation kapazitativ erweitert werden
(Elevate)[^7]. Für einen Single-User ist die Aufmerksamkeit der strukturelle
Engpass; alles andere (LLM-Capacity, CI-Zeit, Storage) ist elevat-fähig und damit
nicht langfristig begrenzend.

### Kognitive Last und Task-Switching
Sweller (Cognitive Load Theory) etabliert, dass das Arbeits­gedächtnis 2–4
gleichzeitige "Chunks" verarbeiten kann und bei Überlastung Lernen und
Problemlösung einbrechen[^8]. Mark, Gudith, Klocke (CHI 2008, n=48) zeigen im
kontrollierten Experiment, dass unterbrochene Aufgaben zwar ~7 % schneller
abgeschlossen werden, aber mit signifikant höherem Stress (6,92 → ~9,3), höherer
Frustration (4,73 → ~6,6) und höherem Effort[^9]. Marks frühere Feldstudien (2004)
quantifizieren die Wiederaufnahme­zeit nach echten Arbeits­unterbrechungen
populär auf ~23 min 15 s; sie zeigen außerdem, dass Wissensarbeiter im Schnitt alle
~11 min das Arbeits­feld wechseln[^10]. Leroy (2009, Organizational Behavior and
Human Decision Processes) belegt experimentell "attention residue" — Teilnehmer
mit unvollständig abgeschlossener Vor­aufgabe zeigen messbar schlechtere
Leistung in der Folge­aufgabe, proportional zur Residue-Stärke[^11]. Newport
(Deep Work) synthetisiert diese Befunde zur Empfehlung langer, ungebrochener
Fokus­blöcke[^12].

### Admission vs. Reactive
Real-Time-Queueing-Theorie zeigt, dass Admission-Control bei bekannten Deadlines
messbare Gewinne bringt: Im Telekom-Beispiel reduziert packet-level Admission
die Verspätungsrate um bis zu 31 %[^13]. Triage-Algorithmen in der Notaufnahme
demonstrieren, dass eine explizite Klassifikation vor Annahme ins Hauptsystem
Wartezeit und Ressourcen­allokation verbessert[^14]. Die Regel: Admission-Control
lohnt, wenn (a) die Ankunftsrate die Bedienrate zeitweise übersteigt, (b) Items
heterogene Kosten und Werte haben und (c) reaktives Rescheduling selbst
kostspielig ist. Genau diese drei Bedingungen gelten für einen Single-User mit
LLM-Agenten: Ideen entstehen in Bursts, haben sehr unterschiedliche Tragweite und
Rescheduling erzeugt Kontextwechsel­kosten (siehe oben).

### Anwendung auf agentische Systeme
LLM-Agenten haben andere Kosten-/Kapazitätsprofile als menschliche Worker:
parallelisier­bar bis ~300 Sub-Agenten in Einzel­systemen (Kimi K2.6)[^15] und ohne
Stress-/Residue-Effekte, aber mit harten Limits in Token-Kosten, Tool-Rate-Limits
und Durable-Execution-Zeit[^15]. Das bedeutet: WIP-Limits auf den menschlichen
Operator sind weiterhin bindend (Reviews, Entscheidungen, Approvals), während
WIP auf die Agenten-Flotte primär wirtschaftlich und nicht kognitiv zu
dimensionieren ist. Übertragbar aus Kanban ist das Prinzip "explizite Policy und
limitierte Queue"; nicht übertragbar ist die Annahme homogener Worker mit
symmetrischer Kapazität.

## Quellenbewertung
Tier-1-Abdeckung durch Little (1961/2008 Überblick), Mark et al. (CHI 2008),
Leroy (2009), Sweller (CLT-Kanon), Anderson (2010), Goldratt (1984) ist stark.
Die einzige belastbare empirische Kanban-WIP-Studie (Dragicevic et al., ESEM
2018) war paywalled; Sekundärquellen bestätigten Stichprobe (5 Teams, 8 000
Items, 4 Jahre) und Kernergebnis (WIP↓ ⇒ Lead Time↓), aber kein optimaler
WIP-Wert publiziert. Reinertsen (2009) ist Tier-2-Praktiker­literatur mit solider
Theorie­basis. Benson (Personal Kanban) ist Tier-2-Praktiker ohne formale
Evidenz für den Wert 3. Mark's "23 min 15 s" ist stark mediatisiert; die präzise
Zahl stammt aus frühen Feldstudien, nicht aus dem CHI-2008-Paper selbst[^9][^10].

## Implikationen für unser System
- **WIP-Vorschlag V1**: maximal **2 aktive Work Items** (menschlicher Operator im
  Engagement) und **3–5 aktive Projekte** (Portfolio-Ebene, nicht alle gleichzeitig
  in Arbeit). Begründung: Working-Memory-Grenze 2–4 Chunks[^8] + Bensons
  Daumenregel[^6] + Little's Law gegen Lead-Time-Explosion[^1]. Agenten-WIP
  getrennt zu dimensionieren; für V1 konservativ 2–3 parallele Agent-Runs pro
  aktivem Work Item.
- **Work Intake & Triage muss minimal**: (a) jeden Input atomar erfassen (GTD
  "Capture")[^16], (b) in ≤ 4 Policy-Klassen einsortieren (reject / defer /
  delegate-to-agent / accept-into-active-WIP), (c) bei Admission eine explizite
  Kostenschätzung fordern, (d) gegen die WIP-Grenze prüfen und bei Überschreiten
  zurückstauen statt verdrängen — das ist der Kern von Admission-Control[^13].
  Alles weitere (Dependency-Analyse, Scope-Zerlegung, Schätzgüte-Tracking) kann
  in Work Design & Planning verschoben werden.
- **Empirisch verteidigbar**: WIP begrenzt Lead Time (Little, Dragicevic);
  Kontextwechsel ist quantifiziert teuer (Mark, Leroy); Admission schlägt reaktives
  Rescheduling unter unseren drei Bedingungen (Burst-Input, Heterogenität,
  Rescheduling-Kosten).
- **Nicht übertragbar**: Der konkrete Zahlenwert "WIP = 3" ist kein empirisches
  Optimum[^5][^6]; er ist Heuristik und muss im laufenden Betrieb kalibriert werden.

## Offene Unsicherheiten
- Optimaler WIP-Wert für hybride Mensch-/LLM-Flotten ist unpubliziert.
- "23 min 15 s" Recovery-Zeit ist populär zitiert, aber methodisch von der
  CHI-2008-Studie zu trennen; die Zahl gilt für spezifische Office-Settings, nicht
  zwingend für Entwickler­arbeit mit persistenten Agenten-Kontexten.
- Wirkung von Admission-Control bei sehr kleinen Ankunftsraten (≤ 5 Ideen/Tag) ist
  in der Literatur nicht belegt; die Kosten des Admission-Protokolls selbst könnten
  dann den Nutzen übersteigen.
- Ob "attention residue" bei agent-delegierter Arbeit (der Mensch wartet, der Agent
  arbeitet) identisch auftritt, ist ungeklärt.

## Quellen
[^1]: John D. C. Little, Stephen C. Graves, "Little's Law", Chapter 5,
  <https://web.eng.ucsd.edu/~massimo/ECE158A/Handouts_files/Little.pdf>
  (Tier 1, foundational).
[^2]: Little's Law — Wikipedia, <https://en.wikipedia.org/wiki/Little's_law>
  (Tier 3, als Zusammenfassung).
[^3]: Donald G. Reinertsen, *The Principles of Product Development Flow*, 2009,
  <https://www.amazon.com/Principles-Product-Development-Flow-Generation/dp/1935401009>
  (Tier 2).
[^4]: David J. Anderson, *Kanban: Successful Evolutionary Change for Your
  Technology Business*, 2010, <https://books.google.com/books?id=RJ0VUkfUWZkC>
  (Tier 1, foundational).
[^5]: Dragicevic et al., "An empirical study of WIP in kanban teams", ESEM 2018,
  <https://dl.acm.org/doi/10.1145/3239235.3239238>; SINTEF-Eintrag
  <https://www.sintef.no/en/publications/publication/1637884/> (Tier 1, paywalled).
[^6]: Jim Benson, Tonianne DeMaria Barry, *Personal Kanban: Mapping Work |
  Navigating Life*, 2011; "How To: Setting Your Personal WIP Limit",
  <https://www.personalkanban.com/pk/uncategorized/how-to-setting-your-personal-wip-limit>
  (Tier 2).
[^7]: Eliyahu M. Goldratt, *The Goal*, 1984; "Five Focusing Steps", TOC Institute,
  <https://www.tocinstitute.org/five-focusing-steps.html> (Tier 1, foundational).
[^8]: John Sweller, "Cognitive Load Theory", Chapter 2, 2011,
  <https://www.emrahakman.com/wp-content/uploads/2024/10/Cognitive-Load-Sweller-2011.pdf>
  (Tier 1).
[^9]: Gloria Mark, Daniela Gudith, Ulrich Klocke, "The Cost of Interrupted Work:
  More Speed and Stress", CHI 2008,
  <https://ics.uci.edu/~gmark/chi08-mark.pdf> (Tier 1).
[^10]: Gloria Mark et al., Feldstudien zur Arbeits­unterbrechung; Referat in
  *Fast Company*, "Worker, Interrupted",
  <https://www.fastcompany.com/944128/worker-interrupted-cost-task-switching>
  (Tier 2 für die 23-Minuten-Zahl).
[^11]: Sophie Leroy, "Why is it so hard to do my work? The challenge of
  attention residue when switching between work tasks", *Organizational Behavior
  and Human Decision Processes* 109(2), 2009,
  <https://www.sciencedirect.com/science/article/abs/pii/S0749597809000399>
  (Tier 1).
[^12]: Cal Newport, *Deep Work*, 2016; Newport-Essay,
  <https://calnewport.com/a-productivity-lesson-from-a-classic-arcade-game/>
  (Tier 2).
[^13]: "Real-time queueing theory: A tutorial presentation with an admission
  control application", *Queueing Systems* 35, 1999,
  <https://link.springer.com/article/10.1023/A:1019177624198> (Tier 1).
[^14]: "Applying queueing theory to evaluate wait-time-savings of triage
  algorithms", *Queueing Systems* 2024,
  <https://link.springer.com/article/10.1007/s11134-024-09927-w> (Tier 1).
[^15]: "Kimi K2.6 runs agents for days — and exposes the limits of enterprise
  orchestration", VentureBeat 2026,
  <https://venturebeat.com/orchestration/kimi-k2-6-runs-agents-for-days-and-exposes-the-limits-of-enterprise-orchestration>
  (Tier 3, aktuelle Kapazitäts­indikation).
[^16]: David Allen, *Getting Things Done*, rev. ed. 2015,
  <https://en.wikipedia.org/wiki/Getting_Things_Done> (Tier 1, foundational).
