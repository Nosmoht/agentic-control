---
topic: ddd-scale
tier: B
date: 2026-04-23
status: draft
---

# Brief 06: DDD-Skalenschwellen und Alternativen für kleine Systeme

## Forschungsfrage

Ab welcher Team- und Domänengrösse zahlt sich Domain-Driven Design (DDD) aus?
Welche Alternativen — Modular Monolith, Vertical Slice Architecture, Transaction
Script, Active Record, Hexagonal ohne DDD — passen besser zu einem ~1-Nutzer,
5–10-Kontexte-System? Und konkret: gibt es empirische Literatur, die 13 Bounded
Contexts bei einem Single-User-System rechtfertigt?

## Methodik

- Tier-1: Evans (2003) Foundational, Fowler-Patterns-Katalog, peer-reviewed
  Springer-Kapitel zu DDD-at-Scale.
- Tier-2: Fowler-Bliki, Thoughtworks, Shopify-Engineering, Ardalis, Jimmy Bogard
  Originalartikel, Three Dots Labs, Milan Jovanović, no-kill-switch
  („Failed promise of DDD").
- Tier-3 (cross-check): Pretius, Kranio-Blog, CodeOpinion — nur wo Tier-1/2 deckt.
- Fetch via `r.jina.ai` für Schlüssel-URLs; WebSearch-Snippets für Breitenabdeckung.
- Jede nicht-triviale Behauptung ≥ 2 unabhängige Quellen, ≥ 1 Tier-1/2.
- Scope-Limit: Strategisches DDD (Contexts, Subdomains) steht im Vordergrund;
  taktische Muster (Aggregates, Value Objects) nur, wo sie die Skalenfrage treffen.

## Befunde

### Wann DDD sich rechnet — die Literatur

DDD zahlt sich nach Evans und nachfolgenden Praktikern erst aus, wenn **das
Verstehen der Domäne — nicht der Bau — die eigentliche harte Aufgabe ist**[^1].
Microsoft und die Springer-Fallstudie zum Large-Scale-Agile nennen als
Schwelleindikatoren: hohe Regelkomplexität mit Ausnahmen, Kern-Wertschöpfung,
mehrere Teams, mehrjährige Lebensdauer[^1][^2]. Fowler setzt via Conway's Law
eine explizite quantitative Grenze: **„A dozen or two people can have deep and
informal communications, so Conway's Law indicates they will create a monolith.
That's fine — so Conway's Law doesn't impact our thinking for smaller teams."**
Erst oberhalb von ~12–24 Personen wird formale Kontexttrennung strukturell
notwendig[^3].

Nick Tune und die Team-Topologies-Literatur operationalisieren das: **ein Team
sollte maximal einen komplexen oder drei einfache Subdomänen tragen**; die
Kontext-Zahl folgt daraus also eher der Team-Zahl als der Domänen-Grösse[^1][^4].

Three Dots Labs fasst den Konsens so: **„if you create something that's very
trivial and doesn't need any kind of design"** — dann nicht DDD; DDD sei ein
*Werkzeugkasten, keine Religion*, und strategisches Denken (Kerndomäne,
Modulgrenzen) sei universell wertvoll, aber taktische DDD-Patterns (Aggregate,
Domain Services) gehörten nur dort hin, wo sie ein reales Problem lösen[^5].

### Kritiken und gemeldete Fehladoptionen

Der no-kill-switch-Essay *„The failed promise of DDD"* (Tier 2, Senior CTO,
2024) identifiziert zwei Kernlücken: (F1) DDD gibt keine Anleitung, *gute* von
*schlechten* Modellen zu unterscheiden, und (F2) die Abstraktionsebenen
*Bounded Context* (zu hoch) und *Aggregate/Entity* (zu niedrig) lassen genau die
mittlere, praktisch wichtige Ebene offen[^6]. Kranio listet als häufigste
Anti-Patterns: **Overengineering, erzwungene Pattern-Anwendung, schwache
Grenzen, fehlende Kollaboration mit Domain-Experten**[^7]. Mploed
(Speaker Deck „Failures and learnings during the adoption of DDD") dokumentiert
praktische Postmortems mit demselben Grundmuster: Teams lesen Evans, wenden
Patterns reflexartig auf *alle* Projekte an, auch wo triviale CRUD-Logik
reichen würde[^8].

Simon Brown liefert keine DDD-Kritik im engeren Sinn, positioniert aber sein
C4-Modell bewusst so, dass Komponenten- und Code-Ebene *nur bei echtem Bedarf*
erzeugt werden — eine implizite Einfachheitsheuristik, die gegen reflexartige
DDD-Tiefenstrukturierung wirkt[^9].

Dan North tritt in den gesichteten Quellen nicht mit einem direkten DDD-Verriss
auf; die ihm zugeschriebene Kritik ist in der Sekundärliteratur eher eine
allgemeine BDD-/Pragmatismus-Haltung. **Als Dan-North-Zitat nicht belastbar —
als Gap markiert.**

### Alternativen für kleine Systeme

**Modular Monolith.** Ein Deployment, interne Module mit klaren Grenzen und
geteilter Datenbank. Thoughtworks, Shopify-Engineering und Ardalis beschreiben
ihn als *Goldilocks-Architektur*: strukturell genug für Wartbarkeit, ohne
Verteilungskosten[^10][^11][^12]. Für kleine Teams/Projekte: „single codebase,
easy deployment, shared database simplify development for small teams"[^13].
Migrationspfad zu Services bleibt offen, ohne vorweggenommen zu werden[^10].

**Vertical Slice Architecture (Jimmy Bogard, 2018).** Jeder User-Request — von
UI bis Datenbank — wird in einem Feature-Ordner gebündelt; High Cohesion
innerhalb einer Scheibe, Low Coupling zwischen Scheiben[^14][^15]. VSA kommt
ohne N-Tier-Gerüst aus, skaliert schrittweise (CQRS entsteht „out of the gate")
und eignet sich als Startpunkt, der später verfeinert werden kann[^14][^16].
Für ein 1-Personen-System mit 5–10 fachlich dünnen Scheiben ist das die
vermutlich leichtgewichtigste ernsthafte Option.

**Transaction Script / Active Record (Fowler, PoEAA).** Fowler: *„The glory of
Transaction Script is its simplicity. Organizing logic this way is natural for
applications with only a small amount of logic, and it involves very little
overhead either in performance or in understanding."*[^17] Empfehlung mehrerer
Sekundärquellen: *start simple (Transaction Script) and refactor to richer
models only when code smells appear*[^18][^16]. Für Logik, die im Kern
„Trigger → Validate → Persist → Emit" ist, bleibt dies auch 2026 state of the
art.

**Hexagonal Architecture ohne DDD.** Hexagonal (Ports & Adapters) löst das
separate Problem *Kern isolieren von I/O*. Es ist unabhängig von DDD und
vertretbar, ohne Aggregates/Ubiquitous Language eingeführt zu werden —
insbesondere dort, wo die Testbarkeit des Kerns wichtiger ist als die
Modellierungstiefe[^19]. Praxisnote: häufige Kombination ist
Hexagonal-Kern + Transaction-Script-Use-Cases + minimale Value Objects.

### Anwendbarkeit auf Single-User

Fowler ist hier explizit: Conway's Law (und damit die gesamte „Contexts =
Teams"-Motivation von DDD) greift erst, wenn Menschen *organisiert* werden
müssen[^3]. Ein Einzelentwickler hat per Definition keine Kommunikationsgrenzen
zwischen Teilsystemen; ein *Bounded Context* als **sozio-technische Einheit**
wird zum **rein technischen Modul**, und für Module existieren leichtere
Idiome (Packages, Features, Namespaces). Ein Ardalis-Beispiel illustriert das
invers: als ein Einzelentwickler 18 Monate lang ein Modul baute, war keine
API-Grenze vorhanden — „the code had been optimized for one person's
workflow"[^20]. Erst mit einem *zweiten* Entwickler entstand Bedarf an
Context-Boundaries. Für Single-User heisst das: **strategisches DDD-Denken ist
nützlich (Kerndomäne identifizieren), taktisches DDD und harte
Context-Grenzen sind überstrukturell.**

### Eingrenzung: 13 Contexts bei 1 Nutzer

Keine der gesichteten Tier-1/2-Quellen stützt 13 Bounded Contexts bei einem
1-Personen-System. Gegenteilige Signale:

- **Fowler**: ≤ 24 Personen = Monolith-Zone, keine Context-Trennung
  erforderlich[^3].
- **Tune/Team-Topologies**: 1 Team ↔ max. 1 komplexer oder 3 einfache
  Subdomänen[^1][^4]. Für 1 Person wären also realistisch 1–3 Subdomänen,
  *nicht* 13 Bounded Contexts.
- **Three Dots Labs**: DDD-Taktik nur anwenden, wo ein reales Problem sie
  verlangt — sonst Overengineering[^5].
- **Kranio / mploed Postmortems**: *Pattern-Reflex auf alle Projekte* ist der
  prominenteste dokumentierte DDD-Fehlmodus[^7][^8].

Das legt nahe, dass 13 Contexts bei 1 Nutzer **systematisch über-strukturiert**
sind. Plausibel wäre eine Interpretation der 13 Einheiten als **Feature-Slices
oder Module** in einem Modular Monolith — nicht als Bounded Contexts im
DDD-Sinn mit eigenem Ubiquitous Language und Anti-Corruption-Layer pro Grenze.

## Quellenbewertung

Tier 1: Evans (2003, Fundament) und peer-reviewed Springer-Kapitel (Hohl et al.)
als theoretische Verankerung; Fowler Conway-Law-Bliki als definitiver
Team-Schwellentext. Tier 2 sehr dicht (Fowler PoEAA-Katalog, Thoughtworks,
Shopify, Ardalis, Three Dots Labs, no-kill-switch, Jimmy Bogard
Originalartikel, Milan Jovanović). Tier 3 (Kranio, mploed, Pretius) nur als
Verstärkung bereits belegter Punkte. Cross-Validation pro Kernbehauptung
erfüllt. Gap: keine belastbare Dan-North-Primärquelle zum DDD-Thema
gefunden — die in Framing erwähnte Kritikerrolle ist in der Literatur mploed
und no-kill-switch zuzuordnen, nicht North.

## Implikationen für unser System

1. **DDD ist hier nicht das passende Paradigma**, jedenfalls nicht in Volltracht.
   Die DDD-Begründung (Conway's Law, mehrere Teams, evolvierendes gemeinsames
   Vokabular gegen Missverständnisse) trifft bei 1 Nutzer nicht zu. Die
   DDD-Vokabeln (Bounded Context, Ubiquitous Language, Aggregate) in den Notes
   00–11 riskieren das klassische „Pattern-auf-alles"-Anti-Pattern[^7][^8].
2. **Empfohlenes Idiom: Modular Monolith mit Vertical Slices**, Kern
   hexagonal isoliert, einzelne Slices als Transaction Scripts beginnend.
   Begründung: leichtgewichtig für 1 Entwickler, erlaubt aber späteres
   Herausziehen einzelner Module als Services, ohne aktuell
   Verteilungskomplexität zu bezahlen[^10][^13][^14][^16].
3. **Kontext-Anzahl**: empirisch verteidigbar sind bei 1 Nutzer **≈ 3–5
   Kernmodule** (Work-Lifecycle, Execution, Knowledge/Evidence,
   Policy/Trust, Interaction). Die 13 Einheiten sind als *Feature-Slices*
   legitim, aber nicht als *Bounded Contexts* — sie brauchen keine
   Anti-Corruption-Layer, kein eigenes Vokabular pro Grenze, keine
   separaten Teams.
4. **Strategisches DDD behalten, taktisches reduzieren**: Kerndomäne
   benennen (Agentic Control selbst), Supporting/Generic Subdomains
   erkennen (z. B. Event Fabric als Generic). Keine Aggregates /
   Repositories / Value Objects erzwingen, wo Dictionaries und Funktionen
   reichen[^5].

## Offene Unsicherheiten

- Kein direktes Dan-North-Zitat zur DDD-Kritik belegt; in der Literatur
  übernehmen mploed und no-kill-switch diese Rolle. Falls North-Zitat später
  erforderlich, Primärsuche auf dannorth.net nötig.
- Schwelle 12–24 Personen (Fowler) ist eine *informelle Beobachtung*, keine
  gemessene Grösse; Zahl ist indikativ, nicht präzise.
- Die Aussage „13 Contexts sind systematisch über-strukturiert" ist
  *literaturkonsistent*, aber nicht empirisch im Sinne einer Studie belegt
  — es existiert keine Studie zu Context-Anzahl-vs-Teamgrösse.
- Hybrid-Fall: falls das System später *mehrere* Agenten mit je eigenem
  „Kontext" hat (im operativen, nicht organisatorischen Sinn), wäre die
  13 neu zu prüfen. Gehört in Brief 14 (Kontext-Anzahl).

## Quellen

[^1]: Hohl et al., *Supporting Large-Scale Agile Development with Domain-Driven Design*, Springer 2018. <https://link.springer.com/chapter/10.1007/978-3-319-91602-6_16>
[^2]: Microsoft Learn, *Domain analysis — When to use DDD*. Zitiert über Wikipedia-Lemma Domain-driven_design. <https://en.wikipedia.org/wiki/Domain-driven_design>
[^3]: Martin Fowler, *Conway's Law* (Bliki). <https://martinfowler.com/bliki/ConwaysLaw.html>
[^4]: Nick Tune, *Domain-Driven Architecture Diagrams*. <https://scribe.rip/nick-tune-tech-strategy-blog/domain-driven-architecture-diagrams-139a75acb578>
[^5]: Miłosz Smółka / Robert Laszczak (Three Dots Labs), *DDD: A Toolbox, Not a Religion*. <https://threedots.tech/episode/ddd-toolbox-not-religion/>
[^6]: no-kill-switch, *The failed promise of Domain-Driven Design, part 1*. <https://no-kill-switch.ghost.io/the-failed-promise-of-domain-driven-design-part-1/>
[^7]: Kranio, *From Good to Excellent in DDD: Common Mistakes and Anti-Patterns*. <https://www.kranio.io/en/blog/de-bueno-a-excelente-en-ddd-errores-comunes-y-anti-patrones-en-domain-driven-design---10-10>
[^8]: Michael Plöd, *Failures and learnings during the adoption of DDD* (Speaker Deck). <https://speakerdeck.com/mploed/failures-and-learnings-during-the-adoption-of-ddd>
[^9]: Simon Brown, C4 Model Homepage. <https://c4model.com/>
[^10]: Thoughtworks, *When (modular) monolith is the better way to build software*. <https://www.thoughtworks.com/en-us/insights/blog/microservices/modular-monolith-better-way-build-software>
[^11]: Shopify Engineering, *Deconstructing the Monolith*. <https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity>
[^12]: Steve Smith (Ardalis), *Introducing Modular Monoliths: The Goldilocks Architecture*. <https://ardalis.com/introducing-modular-monoliths-goldilocks-architecture/>
[^13]: Milan Jovanović, *What Is a Modular Monolith?* <https://www.milanjovanovic.tech/blog/what-is-a-modular-monolith>
[^14]: Jimmy Bogard, *Vertical Slice Architecture*. <https://www.jimmybogard.com/vertical-slice-architecture/>
[^15]: Milan Jovanović, *Vertical Slice Architecture*. <https://www.milanjovanovic.tech/blog/vertical-slice-architecture>
[^16]: Oskar Dudycz, *My thoughts on Vertical Slices, CQRS, Semantic Diffusion* (Architecture Weekly). <https://www.architecture-weekly.com/p/my-thoughts-on-vertical-slices-cqrs>
[^17]: Martin Fowler, *Transaction Script* (PoEAA Catalog). <https://martinfowler.com/eaaCatalog/transactionScript.html>
[^18]: Lorenzo Dematté, *Quantifying Domain Model versus Transaction Script*. <https://lorenzo-dee.blogspot.com/2014/06/quantifying-domain-model-vs-transaction-script.html>
[^19]: Alistair Cockburn, Hexagonal Architecture — sekundär referenziert via Fowler-Patterns und Three Dots Labs[^5].
[^20]: Steve Smith (Ardalis), *Conway's Law, DDD, and Microservices*. <https://ardalis.com/conways-law-ddd-and-microservices/>
