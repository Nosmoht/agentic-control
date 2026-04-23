---
topic: pkm
tier: B
date: 2026-04-23
status: draft
---

# Brief 08: Personal Knowledge Management und Task-Integration

## Forschungsfrage
Welche PKM- und Task-Tracking-Architekturen sind empirisch fundiert, welche
Primitive bieten sie, und welche Konzepte sind auf ein multi-projekt-faehiges
agentisches Kontrollsystem uebertragbar? Die bestehenden Objekte unseres
Canonical Domain Model (Project, Work Item, Observation, Decision, Standard,
Artifact, Evidence, Context Bundle) werden gegen etablierte PKM-Literatur
geprueft — welche davon sind belegte Primitive, welche sind Erfindung?

## Methodik
Drei Recherche-Zyklen nach Tier-Regeln. Tier-1-Primaerquellen: Allen (GTD,
2001/2015), Forte (Building a Second Brain/PARA, 2022), Ahrens (How to Take
Smart Notes, 2017), Matuschak (Evergreen Notes, 2020+), Luhmann-Zettelkasten-
Archiv Bielefeld; Heylighen & Vidal (GTD-Science-Paper, Cogprints).
Tier-2: Methodologie-Posts von Carroll (Bullet Journal), Johnny.Decimal-
Dokumentation. Tier-3: Praktiker-Posts zu Obsidian/Logseq/Tana, kritisch
trianguliert. Die empirische Literatur zu PKM-Outcomes ist duenn und im Paper-
Corpus auffallend unterrepraesentiert — das ist selbst ein Befund.

## Befunde

### Kern-Methoden im Vergleich
| Methode | Kernprinzip | Projekte? | Task-Integration | Empirische Evidenz |
|---|---|---|---|---|
| GTD (Allen 2001/2015) | Capture → Clarify → Organize → Reflect → Engage; "mind like water" durch externes Gedaechtnis | Ja: Projekt = "alles, was >1 Schritt braucht"; plus Someday/Maybe | Zentral: Next Actions, Contexts (@computer, @phone), Weekly Review | Keine kontrollierten Studien;[^1] Heylighen & Vidal (2007) leiten theoretische Plausibilitaet aus Kognitionswissenschaft ab (Offloading, Zeigarnik-Effekt), liefern aber keine eigenen Messungen |
| PARA (Forte 2017/2022) | 4 Buckets nach Aktionabilitaet: Projects / Areas / Resources / Archives | Ja, als primaere Achse (Aktionabilitaet schlaegt Thema) | Projekte treiben Notizauswahl; Notiz ist nuetzlich, wenn sie ein aktives Projekt bewegt | Keine peer-reviewten Studien; Evidenz ist selbst-berichtet bei Forte-Kunden |
| Zettelkasten (Luhmann) | Atomare Notizen, fixe IDs, Folgezettel-Verknuepfung, Struktur emergiert | Nein — Wissens-, nicht Projektsystem | Fehlt; explizit produktions-, nicht aktionsorientiert | Luhmann selbst (90k Zettel, 600 Publikationen) ist Einzelfall, keine Kontrolle; Bielefeld-Archiv dokumentiert, vergleicht aber nicht |
| Smart Notes / Evergreen (Ahrens, Matuschak) | Atomicity, ein Konzept pro Notiz, Titel als API, inkrementell veredeln | Indirekt: Evergreen-Notizen sind langlebiger als Projekt-Lebensdauer | Getrennt von Tasks; Matuschak: "Better thinking, not better note-taking" | Keine; theoretischer Bezug zu Spacing, Elaboration, Retrieval — gut belegt fuer Lernen, nicht fuer PKM als Ganzes |
| Johnny.Decimal | 10 Areas × 10 Categories × N IDs = stabile AC.ID-Adressen | Nur implizit (eine Category kann "Projekte" enthalten) | Keine; reines Ablage- und Adressierungsschema | Keine; rein ergonomisches Argument (Muskelgedaechtnis durch stabile Nummern) |
| Bullet Journal (Carroll 2018) | Rapid Logging (Bullets: Task, Event, Note) + Migration (taeglich/monatlich/jaehrlich) | Ja, als "Collections" | Zentral: Migration zwingt zur Bewertung "lohnt sich das noch?" | Keine kontrollierten Studien; Carroll argumentiert aus ADHS-Selbsterfahrung |

### Empirische Evidenz
- **Kein PKM-Verfahren ist gegen eine "einfach aufschreiben"-Baseline in einer
  kontrollierten Studie ueberlegen belegt.** Die Heylighen & Vidal-Analyse zu
  GTD ist eine theoretische Synthese, kein RCT; sie argumentiert mit
  kognitivem Offloading und dem Zeigarnik-Effekt, fuehrt aber keine eigene
  Messung durch. Die PKM-Forschung ist "an under-researched area" (Pauleen,
  Gorman u. a. in den reviewten Uebersichten).[^1]
- **Belegt ist dagegen Hintergrundwissen**, auf das mehrere PKM-Methoden
  aufsetzen: (a) kognitive Entlastung durch externe Gedaechtnisstuetzen
  (Sparrow et al.), (b) Testing- und Spacing-Effekte beim Lernen (Roediger,
  Karpicke), (c) Retrieval-induced-learning (Bjork). Diese sind nicht
  PKM-spezifisch.
- **Fazit**: Der Nutzen von PKM ist plausibel und praktisch oft spuerbar,
  aber methodenspezifische Ueberlegenheit ("Zettelkasten > Ordner") ist
  wissenschaftlich nicht belegt. Die wichtigere Variable ist vermutlich
  Konsistenz der Nutzung, nicht Wahl der Methode.

### Projekt vs. Wissen — Konsens?
- **PARA trennt strikt** nach Aktionabilitaet: Projekt (aktiv, Deadline) vs.
  Area (Dauerverantwortung) vs. Resource (Referenz).
- **GTD trennt schwaecher**: Projekte sind Multi-Step-Commitments, Referenz
  ist eigene Bucket; Someday/Maybe puffert Unentschiedenes.
- **Zettelkasten kennt kein Projekt** — es ist ein reines Wissenssystem;
  Projekt-Output entsteht *aus* dem Zettelkasten, ist aber nicht darin.
- **Bullet Journal vermischt** absichtlich: Tasks, Events und Notes stehen in
  derselben Zeitachse.
- **Konsens, soweit vorhanden**: Die Trennung "aktives Projekt" vs.
  "langlebiges Wissen" ist fruchtbar, aber keine harte Regel. Unsere
  Unterscheidung zwischen `Project`/`Work Item` und `Observation`/`Standard`/
  `Artifact` ist im Kern eine PARA-artige Aktionabilitaets-Achse.

### Tool-Architektur-Primitive (Logseq/Obsidian/Tana/Roam)
Die Werkzeuge bieten unterschiedliche Primitive, und die Wahl ist eine
Schema-Entscheidung, nicht eine Produkt-Entscheidung:
- **Obsidian**: Notiz = Markdown-Datei; Block-IDs moeglich, aber Notiz ist
  der Haupt-Anchor; bidirektionale Links; Plugin-Graph.
- **Logseq / Roam**: Block = erstklassiges Objekt; jede Zeile ein
  adressierbarer Knoten; Outliner-Semantik; Daily-Journal zentral.
- **Tana**: Block + Supertag (typisiertes Schema mit Feldern); de facto eine
  objektorientierte Notiz-Datenbank. Konzept am naechsten an unserem
  Canonical Domain Model.
- **Anytype**: Objekt mit Typ und Relationen; ebenfalls schema-first.
- **Uebertragbare Primitive**: (1) Atomic Unit mit stabiler ID, (2)
  bidirektionale Referenzen, (3) Typisierung ueber Tags/Schemas, (4)
  Daily-Note als append-only-Journal, (5) Query ueber getaggte Attribute.
  Alle finden sich in Ansaetzen in unserem Modell.

### Uebertragbare Konzepte fuer agentische Systeme
- **Capture everywhere, Clarify later (GTD)**: jeder Agent und jeder Nutzer
  kann in denselben Inbox-Strom schreiben, Klassifikation ist ein eigener
  Schritt — mappt direkt auf `Observation` mit spaeterer Promotion.
- **Weekly Review (GTD, Bullet Journal Migration)**: periodischer Trust-
  Check. Fuer uns: Re-Review von `Evidence` und `Context Bundle` auf
  `current_validity_state`.
- **Inbox Zero als Status, nicht als Ziel**: triage bis leer, dann
  abschalten — verhindert Dauer-Aufmerksamkeit auf den Eingangskanal.
- **Atomic Notes (Zettelkasten/Evergreen)**: "ein Konzept pro Einheit",
  uebertragbar auf `Decision` (eine Entscheidung pro Record) und `Standard`
  (eine Regel pro Record).
- **Progressive Summarization (Forte)**: geschichtetes Verdichten in Layern
  0–4. Uebertragbar auf `Artifact`-Lebenszyklus: Rohkontext → verdichtet →
  kanonische Aussage.
- **Projekt = aktiv, Area = laufend (PARA)**: Aktionabilitaet trennt
  `Project` (Lifecycle mit Ende) von `Standard`/`Portfolio` (dauerhaft).
- **Johnny.Decimal-Addressierung**: ID-Stabilitaet ist wertvoll; unsere
  `*_id`-Felder erfuellen das, aber ein menschenlesbares Adressschema fehlt
  und waere billig nachruestbar.

## Quellenbewertung
Primaerquellen (Tier 1) fuer Methoden sind solide und direkt zugaenglich
(Allen, Forte, Ahrens, Matuschak). Peer-reviewte empirische Evidenz ist
duenn und aelter; die Heylighen & Vidal-Analyse war als PDF nicht mehr
erreichbar (500er), alternative Zusammenfassungen bestaetigen aber ihre
theoretische — nicht empirische — Natur. PKM-Lehrbuecher selbst sind
haeufig Praktiker-Werke ohne Kontrollgruppen. Cross-Validation durch je
mindestens zwei Quellen erfuellt; Claims zur *Ueberlegenheit* einzelner
Methoden bleiben als unverifiziert markiert.

## Implikationen fuer unser System
- **PKM-fundierte Objekte**: `Project` (GTD/PARA), `Observation` (Capture-
  Inbox), `Standard` (Evergreen-artige atomare Regel), `Decision` (atomare
  Notiz mit Permanenz), `Artifact` (Output, vergleichbar mit Forte-Output),
  `Context Bundle` (Progressive-Summarization-Layer). Diese Objekte haben
  klare PKM-Analoga.
- **Erfindungen (ohne direkte PKM-Analogie)**: `Work Item` (operations-
  agile, nicht PKM), `Workflow`, `Dependency`, `Approval`, `Evidence` mit
  Trust-Class, `Provider Binding`. Das sind Kontroll- und Governance-
  Primitive, kein PKM-Erbe — und das ist OK, sie entstehen aus dem
  Multi-Agent-Kontext.
- **Uebernehmen fuer V1**: (1) Capture-Inbox als `Observation`-Strom ohne
  Zwang zur Klassifikation, (2) Weekly-Review-artiger Trust-Recheck als
  periodischer Prozess, (3) Atomicity-Regel ("eine Aussage pro
  Decision/Standard") als Modellierungsdisziplin, (4) PARA-artige
  Aktionabilitaets-Trennung zwischen Project und langlebigen Objekten.
- **Vermeiden**: Zettelkasten-artige reine Emergenz fuer Governance-Objekte
  — dort brauchen wir explizite Typen und Lifecycles; Bullet-Journal-artige
  Vermischung von Tasks und Notizen in einem Strom bricht unsere Bounded
  Contexts.
- **Minimale PKM-Kern-Integration V1**: (a) eine Capture-Inbox, (b) klare
  Promotion-Pfade Observation → (Decision | Standard | Artifact), (c)
  periodischer Review-Hook fuer `current_validity_state`, (d) atomare
  Notiz-Disziplin fuer Decision und Standard. Mehr ist fuer V1 nicht noetig.

## Offene Unsicherheiten
- Empirischer Nutzen gegenueber "einfach aufschreiben" ist nicht belegt;
  die Methodenwahl bleibt Geschmack.
- Ob wir ein menschenlesbares Adressschema (Johnny.Decimal-artig) zusaetzlich
  zu den `*_id`-UUIDs brauchen, ist offen.
- Die Grenze zwischen `Observation` und einer zukuenftigen expliziten `Note`/
  `Knowledge-Item`-Entitaet ist unscharf; evtl. braucht V2 eine eigene
  Wissensdomaene neben der Kontrolldomaene.
- Keine der Quellen adressiert Multi-Agent-Capture (mehrere "Autoren" im
  selben Inbox) — das ist unser blinder Fleck gegenueber der Literatur.

## Quellen
- Allen, D. *Getting Things Done* (2001, rev. 2015). gettingthingsdone.com
- Forte, T. *Building a Second Brain* (2022); "The PARA Method",
  buildingasecondbrain.com/para; "Progressive Summarization",
  fortelabs.com/blog/progressive-summarization-…
- Ahrens, S. *How to Take Smart Notes* (2017).
- Matuschak, A. "Evergreen notes", notes.andymatuschak.org/Evergreen_notes
- Luhmann, N. "Kommunikation mit Zettelkaesten" (1981); Zettelkasten-Archiv
  Bielefeld.
- Heylighen, F. & Vidal, C. "Getting Things Done: The Science behind
  Stress-Free Productivity" (2008, Cogprints; zum Zeitpunkt der Recherche
  HTTP 500, via Sekundaerzusammenfassungen verifiziert).
- Carroll, R. *The Bullet Journal Method* (2018); bulletjournal.com.
- Johnny.Decimal, johnnydecimal.com (Kern- und Konzept-Seiten).
- Logseq, Obsidian, Tana, Anytype — offizielle Dokumentationen.
- Wikipedia: "Personal knowledge management", "Getting Things Done",
  "Zettelkasten" (als Sekundaer-Triangulation).

[^1]: Stand der durchsuchten Literatur: keine RCTs zu GTD-, PARA-,
Zettelkasten- oder Bullet-Journal-Outcomes; nur Theorie-Papers und
Selbstberichte. Die Methodenwahl bleibt empirisch unter-determiniert.
