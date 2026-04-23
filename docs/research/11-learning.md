---
topic: learning
tier: B
date: 2026-04-23
status: draft
---

# Brief 11: Learning und Standards-Promotion in Einzelsystemen

## Forschungsfrage

Ab welchem Punkt zahlt sich fuer ein **Einzelnutzersystem** ein formaler
Learning-Pipeline- bzw. Standards-Promotion-Mechanismus aus — gegenueber dem
trivialen Baseline "einfach eine Notiz schreiben"? Die Architekturentscheidung
AD-15 sowie das 6-stufige Standards-Lifecycle-Modell aus Brief 03 setzen eine
mehrstufige Promotion voraus. Zu klaeren: (a) Ist das organisationales-
Lernen-Erbe (Argyris/Schoen/Senge) bei *n=1* ueberhaupt wirksam?
(b) Wann rechnen sich ADRs, Runbooks, Playbooks, Evergreen Notes fuer eine
einzelne Person? (c) Aendert der Kontext-Reset eines LLM-Agenten die
Kalkulation? (d) Laesst sich *Standard* von *Konvention*, *Gewohnheit*, *Notiz*
bei *n=1* ueberhaupt trennscharf definieren?

## Methodik

- Foundationale Tier-1-Literatur (Argyris, Schoen, Nygard, Google SRE) direkt
  konsultiert bzw. ueber autoritaetsnahe Sekundaerquellen trianguliert.
- Tier-2-Praktiker-Reflexionen (Matuschak, Ahrens, ein 2-Jahres-Erfahrungsbericht
  zu Evergreen Notes) zur Plausibilisierung des Empirie-Stands.
- Tier-3-Material (Blog-Essays, Scrum/Agile-Sekundaerliteratur) nur als
  Cross-Check, nie als Primaerbeleg.
- Cross-Validation: jede nicht-triviale Behauptung mit >= 2 unabhaengigen Quellen;
  wo nur eine Quelle verfuegbar, explizit als unverifiziert markiert.
- Scope-Limit: keine RCTs-Jagd zu Journaling — die meta-analytische Lage ist
  weich und beruht auf Selbstbericht.

## Befunde

### Organisationales Lernen — Fundamente
- **Double-Loop Learning (Argyris, 1977)**: der Mechanismus ist nicht
  zwingend organisational — er wird ausdruecklich auch als *individuelles*
  Verhaltenslernen definiert, das die *governing variables* (Werte, Normen,
  Ziele) der eigenen *theory-in-use* aendert, nicht nur die Aktion[^1].
  Die vier Schritte (Entdeckung espoused vs. in-use, Invention, Produktion,
  Generalisation) gelten auch bei *n=1*[^1].
- **Wichtige methodologische Einschraenkung**: Argyris & Schoen basierten
  ihre Interventionen auf *direkter Beobachtung* des Verhaltens; reine
  Fragebogen-/Interview-Evidenz verletzt ihr methodisches Fundament[^1].
  Das ist fuer *n=1* relevant: ohne externe Beobachtung (oder auditierbares
  Log) bleibt Selbstbericht unterbestimmt.
- **Schoen (1983) — reflection-in-action vs. reflection-on-action**: trennt
  Echtzeit-Anpassung waehrend der Handlung von rueckblickender
  Reflexion[^2]. Beides ist konzeptionell individuell — das Modell ist in
  Nursing, Education, Engineering als Einzelpraktiker-Framework etabliert[^2].
- **Fazit**: die Theorie ist bei *n=1* anwendbar, aber ihre Wirksamkeit wurde
  historisch primaer in Teams und beobachteten Settings demonstriert.

### Engineering-Praxis — ADRs, Runbooks, Playbooks
- **Nygard-ADRs (2011)**: originaer motiviert durch (a) Verlust des
  Entscheidungs-*Kontexts* ueber die Zeit und (b) Dokumenten-Verfall; kleine
  modulare Dokumente haben "zumindest eine Chance aktualisiert zu
  werden"[^3]. Positive Erfahrung in frueher Adoption — aber Nygard diskutiert
  *keine* Teamgroessen-Schwelle, ab der es sich lohnt[^3].
- **Team-Coordination-These**: die breite ADR-Literatur (Red Hat, AWS,
  Microsoft, Google Cloud, Fowler) rechtfertigt ADRs ueberwiegend mit
  Team-Wechsel, Onboarding, Wissensuebergabe[^4]. "ADRs are not a solo
  activity. Engage with your team and gather feedback before finalizing an
  ADR"[^4]. Das ist der stroengste Hinweis, dass der Hauptnutzen
  koordinativ ist — nicht erkenntnisbezogen.
- **Google SRE — Postmortems & Runbooks**: Google beziffert Postmortems als
  "most effective tool for preventing recurrent outages" und hat ueber
  Tausende strukturierter Postmortems **Trend-Analyse** betrieben, die
  systemische Ursachen sichtbar machte[^5]. Runbooks beschleunigen
  Incident-Response, indem bekannte Fixes nicht neu erfunden werden[^5].
  Beides skaliert mit *Volumen*: ohne wiederkehrende Incidents fehlt das
  Material fuer Trend-Analyse.

### Solo-Retrospektiven — Evidenzlage
- **Team-Retrospektiven empirisch**: Teams mit regelmaessigen Retros zeigen
  hoehere Reaktionsfaehigkeit und Qualitaet gegenueber Teams ohne Retros
  (Zahlen kursieren in Scrum/Agile-Sekundaerliteratur, unterliegen aber
  Tier-3-Evidenz-Qualitaet)[^6].
- **Solo-spezifisch**: die einschlaegige empirische Literatur zu Agile
  Retros fokussiert Teams; spezifische Evidenz zu Solo-Retros fehlt
  weitgehend[^6]. Eine systematische Uebersicht stellt fest, dass zu
  individueller Selbstreflexion "wenig empirische Evidenz bisher
  existiert"[^6].
- **Journaling als Proxy**: breite Selbstbericht-Literatur suggeriert
  Produktivitaetsgewinne und metakognitive Effekte durch **strukturiertes**
  Reflexionsschreiben gegenueber unstrukturiertem Free-writing[^7]. Die
  haeufig zitierten Prozent-Verbesserungen stammen aus Tier-3-Marketing-
  Aggregationen und werden hier nur als schwacher Richtungshinweis
  gewertet.
- **Minimum-viable Kadenz**: aus der Agile-Praxis (2-Wochen- bis Monats-
  Sprints) liegt die konventionelle Untergrenze einer sinnvollen Retro bei
  etwa **2 Wochen**[^6]; eine sehr kurze Kadenz (taeglich) verfaellt laut
  Praktikerberichten schnell in Ritualismus ohne Substanz.

### Evergreen Notes / Zettelkasten-Promotion
- **Ahrens (2017)**: drei Notiz-Typen (fleeting, literature, permanent);
  Promotion ist bewusster kognitiver Akt — eine fluechtige Notiz wird zur
  permanenten *nur wenn* sie selbstenthaltend und in ein bestehendes
  Geflecht eingefuegt werden kann[^8].
- **Matuschak (Evergreen Notes)**: die Pointe ist nicht "bessere Notizen",
  sondern **besseres Denken**; Evergreen Notes sind atomar, konzeptorientiert
  und ueber Zeit/Projekte hinweg evolvierend[^9].
- **Empirische Basis — schwach**: die Primaerliteratur (Matuschak, Ahrens,
  Luhmann) ist ueberwiegend theoretisch und selbstbezogen; es gibt **keine
  RCTs**, die Zettelkasten-artige Promotion gegen "einfaches
  Aufschreiben" validieren[^10].
- **Gegengewicht — Zwei-Jahres-Selbstberichts-Studie**: nach > 1000
  Evergreen-Notes beobachtet der Autor (a) Gewinn als externes Gedaechtnis,
  (b) **keine** signifikante Verbesserung der mentalen "connect-the-dots"-
  Faehigkeit, (c) Schwaeche fuer etablierte Domaenen (Fluenz-Training),
  (d) unstrukturierte Note-Graphen, die nicht mit mentalen Reference-
  Frames (~7 Items) uebereinstimmen[^11]. Das ist ein starker Tier-2-
  Hinweis, dass Promotion-Rituale fuer *Frontier-Denken* nuetzlich sind —
  fuer *operationale Routine* eher nicht.

### Standard vs. Konvention vs. Gewohnheit vs. Notiz
- **Industrie-Definition**: Standards sind verbindlich, oft von
  IEEE/ISO/Corporate gesetzt; Conventions sind Empfehlungen und koennen
  auch die "habituellen Codierpraxis eines Individuums" sein; Guidelines
  sind weiter gefasste Empfehlungen[^12].
- **Trennkriterium ist Enforcement/Verbindlichkeit**: "coding conventions
  are recommendations, while coding standards are mandatory, non-negotiable
  rules your team has agreed to follow strictly"[^12].
- **Implikation fuer n=1**: der Enforcement-Operator bist du selbst.
  Mechanisch verschwindet die Trennung — sie lebt nur im *Artifact-Status*
  (Was ist nachschlagbar vs. implizit-im-Kopf) und in der
  *Automatisierbarkeit* (liest der Agent es? bricht ein Hook, wenn
  verletzt?). Das ist ein LLM-Agent-spezifischer Wiedergewinn der
  Unterscheidung.

### LLM-Agent-Spezifika — Kontext-Reset
- **Kernproblem**: ein LLM-Agent hat **kein biologisches Langzeitgedaechtnis**;
  jede Session startet kalt bzw. mit einem begrenzten Fenster. "The winning
  pattern is external memory plus disciplined retrieval: store state outside
  the prompt, then pull back only what matters for the current loop"[^13].
- **Anthropic-Muster 2026**: `CLAUDE.md` als "persistent memory" pro
  Projekt/Home; **Agent Skills** als modulare Markdown-Instruktionen mit
  YAML-Frontmatter, die dynamisch geladen werden[^14]. Das ist *de facto* ein
  produktifiziertes Promotion-System: Skills sind "permanente Notes" fuer
  Agenten.
- **Memento-Skills / A-MEM**: Forschung 2025/26 zeigt, dass *strukturierte
  Markdown-Skills* als evolvierendes externes Gedaechtnis einer passiven
  Konversations-Log ueberlegen sind — "extracted, curated knowledge, not raw
  conversation"[^15]. Das ist die empirisch staerkste Begruendung fuer
  formale Promotion im *LLM-Agent-Kontext*.
- **Konsequenz fuer n=1 mit LLM-Executor**: die Promotion-Pipeline
  existiert nicht fuer dich — sie existiert **fuer den Agenten**, der dein
  Gedaechtnis nicht teilt. Das dreht die Kalkulation um: was fuer einen
  menschlichen Solo-Entwickler Overhead waere, ist fuer einen LLM-basierten
  Executor **Infrastruktur**.

## Quellenbewertung

- **Tier 1** (foundational): Argyris 1977 HBR, Schoen 1983, Nygard 2011.
  Stark konzeptionell, schwach RCT-belegt.
- **Tier 1/2** (engineering empirisch): Google SRE Book/Workbook —
  quantitativ ("tausende Postmortems"), operativ belastbar, aber
  grossskaliert und nicht direkt auf n=1 uebertragbar[^5].
- **Tier 2**: Matuschak, Ahrens (Selbstbericht hoher Qualitaet);
  2-Jahres-Evergreen-Reflexion als kritischer Gegenpol[^11].
- **Tier 3**: Scrum/Agile-Blogs mit Prozent-Zahlen ohne verlinkte
  Primaerstudie — als Richtungsindikator, nicht als Beleg behandelt.
- **Entdeckte Luecke**: keine gefundene empirische Arbeit vergleicht
  Solo-Retro gegen Keine-Retro; keine RCTs zu Zettelkasten-Promotion.

## Implikationen fuer unser System

- **Die reine *human* n=1-Kalkulation rechtfertigt keine 6-Stufen-Pipeline**:
  die Engineering-Literatur (ADRs, Runbooks, Postmortems) zeigt ueberwiegend
  **koordinativen** Nutzen; bei n=1 faellt dieser weg. Evergreen-Notes-
  Promotion hilft fuer Frontier-Denken, nicht fuer operationale Routine[^11].
- **Die LLM-Agent-Dimension kehrt die Kalkulation um**: der Kontext-Reset
  macht *externe, strukturierte, auffindbare Artefakte* zur Infrastruktur
  fuer den Executor[^13][^15]. "Notiz mit Tag" reicht **nur**, wenn der Agent
  den Tag verlaesslich findet und der Inhalt atomar genug ist, ohne Rest-
  Session-Kontext verstanden zu werden. Das ist faktisch die Evergreen-Note-
  Disziplin unter anderem Namen.
- **Minimalform mit Evidenz + Nutzen** (Empfehlung V1):
  1. **Capture-Inbox** als `Observation` (keine Klassifikation erzwungen) —
     deckt fleeting-notes-Rolle (Ahrens[^8]).
  2. **Atomare Decision/Standard-Notizen** mit Kontext, Entscheidung,
     Konsequenz — deckt ADR-Mindestform (Nygard[^3]) und
     Evergreen-Atomaritaet (Matuschak[^9]).
  3. **Periodischer Review-Hook** (2-Woechentlich als Untergrenze,
     monatlich als robuster Default) — deckt Schoen's
     reflection-on-action[^2] und die Agile-Retro-Kadenz[^6].
  4. **Explizite Promotion-Schwelle** nur dort, wo es den Agent-Kontrakt
     aendert (z. B. `Standard` wird von Agenten gelesen und
     enforced) — Enforcement ist das einzige bei n=1 tragfaehige
     Trennkriterium[^12].
- **Verteidigbare Stufen-Anzahl**: empirisch verteidigbar sind **2–3 Stufen**
  (`Observation` → `Decision`/`Standard`; optional zusaetzlich
  `Retired`/`Superseded`). Die 6-Stufen-Variante aus Brief 03 traegt dann,
  wenn jede Stufe (a) einen *beobachtbaren* Zustandswechsel fuer den Agenten
  bedeutet und (b) ein *Review-Event* erzeugt. Stufen ohne beides sind
  Overhead.
- **Agent-spezifische Begruendung**: jede Promotion-Stufe rechtfertigt sich
  genau dann, wenn sie (i) die Auffindbarkeit durch den Agenten aendert,
  (ii) die *Verbindlichkeit* (Hooks, Gates, Trust-Zone) aendert, oder
  (iii) die *Cache-/Load-Strategie* aendert. Andernfalls ist sie ein
  Team-Artefakt ohne Teamkontext.

## Offene Unsicherheiten

- Keine RCT-Evidenz fuer Zettelkasten/Evergreen-Promotion gegen "einfach
  aufschreiben"[^10][^11]. Der Nutzen bleibt Selbstbericht.
- Keine spezifische Empirie zu Solo-Retrospektiven; die 2-Wochen-Kadenz ist
  aus Team-Analogie uebernommen, nicht fuer Solo validiert[^6].
- Die Tier-3-Zahlen zu Journaling-Produktivitaet (+22.8 %, +30 % Klarheit)
  konnten nicht auf Primaerstudien zurueckgefuehrt werden — nicht in die
  Argumentation aufgenommen[^7].
- Ob `CLAUDE.md`/Skills-artige Persistenz *langzeitlich* konsistent bleibt
  (Drift zwischen Agent-Verhalten und geschriebenem Standard) ist offen;
  die Muster sind zu jung fuer Longitudinaldaten.
- Ob Double-Loop Learning bei n=1 **ohne externen Beobachter** ueberhaupt
  wirksam ist, bleibt methodisch ungeloest[^1] — ein LLM-Peer-Reviewer
  koennte diese Rolle einnehmen, aber das ist spekulativ.

## Quellen

- Argyris, C. "Double Loop Learning in Organizations", *Harvard Business
  Review*, 1977 (PDF-Archivfassung).
- Wikipedia / infed.org / Open University: Sekundaerzusammenfassungen zu
  Argyris & Schoen (Triangulation).
- Schoen, D. *The Reflective Practitioner: How Professionals Think in
  Action*, Basic Books, 1983 (Archivfassung).
- Nygard, M. "Documenting Architecture Decisions", cognitect.com, 2011.
- Fowler, M. "Architecture Decision Record", martinfowler.com/bliki.
- Red Hat, AWS Prescriptive Guidance, Microsoft Well-Architected Framework,
  Google Cloud Architecture Center — ADR-Sekundaerliteratur.
- Google SRE. *Site Reliability Engineering* / *The Site Reliability
  Workbook*, sre.google (Postmortem Culture, Postmortem Analysis).
- Ahrens, S. *How to Take Smart Notes*, 2017.
- Matuschak, A. "Evergreen notes", notes.andymatuschak.org.
- "Reflection on two years of writing evergreen notes",
  engineeringideas.substack.com (Tier-2-Selbstbericht).
- Anthropic. "Agent Skills", platform.claude.com/docs; "Claude Code Best
  Practices", code.claude.com/docs; Skills-Repository
  github.com/anthropics/skills.
- Karpathy / VentureBeat. "LLM Knowledge Base" Architecture, 2026.
- A-MEM, "Agentic Memory for LLM Agents", arXiv 2502.12110, 2025.
- Research-Starters / Wiley *European Management Review* 2024 — "Revitalizing
  double-loop learning" Systematic Review (Sekundaerquelle).
- Codacy, Institute of Data, opslevel, Wikipedia — Coding Standards vs.
  Conventions vs. Guidelines (Triangulation).

[^1]: Argyris 1977 (HBR-PDF) sowie Wikipedia/infed.org/Open University
      (Triangulation). Double-Loop gilt explizit auch individuell; methodische
      Anforderung *beobachtbare Daten* schwaecht reine Selbstbericht-Evidenz.
[^2]: Schoen 1983 (Ragged-University-PDF); Hull-University-LibGuide;
      Workplace-Hero-Sekundaertext. Unterscheidung in-action / on-action
      etabliert, bei Einzelpraktiker angewendet.
[^3]: Nygard, "Documenting Architecture Decisions", cognitect.com, 2011 —
      Original-Essay, begruendet ADRs mit Kontext-Verlust und
      Dokumentenverfall; keine Teamgroessen-Schwelle.
[^4]: Fowler-Bliki, Red Hat Blog, AWS Prescriptive Guidance,
      Microsoft-Well-Architected, Google Cloud Architecture Center — alle
      rechtfertigen ADRs primaer mit Team-Koordination.
[^5]: Google SRE Book/Workbook — "Postmortem Culture", "Postmortem
      Analysis"; Tausende Postmortems ueber sieben Jahre erlaubten Trend-
      Analyse.
[^6]: ResearchGate/Springer "Reflection in Agile Retrospectives"; SAFe
      Framework; Atlassian Team Playbook; NN/g "UX Retrospectives" — Team-
      Literatur, Solo-Evidenz-Luecke explizit benannt.
[^7]: mindsera.com und reflection.app Aggregationen zu Journaling-
      Produktivitaet — Tier-3, nicht primaer-verlinkt; nur als Richtungshinweis.
[^8]: zettelkasten.de Concept-Review; Ahrens' drei Notiz-Typen
      (fleeting/literature/permanent); Promotion als bewusster Akt.
[^9]: Matuschak, notes.andymatuschak.org — "Evergreen notes should be
      atomic", "Knowledge work should accrete".
[^10]: Durchgaengige Beobachtung der Primaer- und Sekundaerquellen: keine
       RCTs; Evidenz ist Selbstbericht.
[^11]: "Reflection on two years of writing evergreen notes",
       engineeringideas.substack.com — > 1000 Notes; Nutzen als externes
       Gedaechtnis, schwach fuer mental model & fluency.
[^12]: Codacy Blog; Institute of Data; opslevel; Wikipedia "Coding
       conventions"; promovre.com — Konvergenz auf Enforcement als
       Trennkriterium.
[^13]: Felo Search Blog; aiagentmemory.org; Oracle Blogs; Karpathy/
       VentureBeat — Konsensmuster "external memory + disciplined
       retrieval".
[^14]: Anthropic "Agent Skills" platform.claude.com/docs; Anthropic
       "Claude Code Best Practices" code.claude.com/docs;
       github.com/anthropics/skills.
[^15]: A-MEM (arXiv 2502.12110); VentureBeat zu Memento-Skills; "strukturiertes
       externes Gedaechtnis schlaegt passives Log".
