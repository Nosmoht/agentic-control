# Open Questions

Durchnummerierte, adressierbare Lücken in der Spezifikation. Jede Frage verweist auf
die Stelle in den Dokumenten `00-11`, wo die Lücke sichtbar wird. Reihenfolge folgt
grob dem Weg von Infrastruktur → Fachlichkeit → Betrieb, nicht der Dringlichkeit.

## A. Persistenz, Runtime, Transport

1. **Persistenzschicht.** Welche Technologie hält den Zustand der 13 Kontexte?
   (Kandidaten: SQLite, Postgres, Dateisystem + Git, ein Mix.)
   Bezug: `04` State Ownership, `05` State Contracts, AD-12.
2. **Shared vs. per-Context-DB.** Teilen sich die Kontexte eine Datenbank, oder hat
   jeder Kontext eigene Storage? Wenn getrennt: Konsistenzmodell?
   Bezug: AD-12 (One Owner), AD-11 (Events nie Authority).
3. **Workflow-Runtime.** Was führt langlebige Orchestrierung aus?
   (Kandidaten: eigener Daemon mit persistierter State Machine, Temporal, Restate,
   Cron + DB-Flags.) Bezug: `04` Workflow Coordination.
4. **Event-Fabric-Transport.** NATS, Redis Streams, Postgres LISTEN/NOTIFY,
   Append-Only-Log? Idempotenz-Key-Format? Consumer-Gruppen? Retention?
   Bezug: `04` Event Fabric, AD-11.
5. **Konsistenzmodell.** Strong-consistency (eine DB, Transaktionen) oder eventual
   (Projektionen, Reconciliation-Intervall)? Bei eventual: wie verhindert AD-11,
   dass Events zur faktischen SoT werden?

## B. Control Surface und Interaktion

6. **Control-Surface-Wahl.** Telegram, Slack, Matrix, CLI, Mail, Web-UI — oder
   mehrere parallel? Pro Kanal: Inbound-Trust, Rate-Limits, E2E-Eigenschaften.
   Bezug: `04` Interaction Management, `06` Trust Boundaries.
7. **Interaktionszustand.** Wie wird Konversationskontext persistiert, wie ist
   Kanalwechsel modelliert (dieselbe Absicht, andere Surface)?

## C. Identität, Secrets, Provisioning

8. **Single-User-Identität.** Welche Identität authentifiziert gegen das System?
   (SSH-Key? OAuth? Lokaler Token?) Braucht ein Single-User-System überhaupt einen
   eigenen Kontext dafür? Bezug: `04` Identity, Trust & Access.
9. **Secret-Store.** Wo leben Provider-Credentials, wie rotieren sie?
   Welche Trust-Zone umfasst den Secret-Store? Bezug: AD-16, `04` Provisioning.
10. **Provider-Inventar.** Welche externen Provider werden initial unterstützt
    (GitHub, GitLab, Plane, Linear-Replacement, Jira)? Was bedeutet „provider-neutral"
    konkret? Bezug: `01` Kernannahmen, AD-10.

## D. Execution und Isolation

11. **Execution-Isolationsmechanismus.** Container, Firecracker, gVisor, nsjail,
    Chroot, oder nur Worktree? Pro Work Item eine eigene Sandbox?
    Bezug: AD-09, `06` Restricted Execution.
12. **Harness für Codex CLI und Claude Code.** Was umschließt die beiden Tools, damit
    sie zu „Execution & Verification" werden? (Scheduler, Workspace-Manager,
    Result-Parser, Cost-Tracker.) Bezug: `07`.
13. **Permission-Mapping.** Wie wird Claude Codes `settings.json` / Hooks / Skills /
    MCP und Codex CLIs Permission-Mode auf Policy & Governance abgebildet?
    Bezug: `04` Policy & Governance, AD-08.
14. **Session-Grenzschnitt.** Was bleibt im Agentenprozess, was geht zurück an
    Workflow Coordination? Bezug: AD-09 („bounded").
15. **Cloud vs. lokal.** Wird Claude Code lokal (CLI) oder remote (Web/Cloud)
    betrieben? Codex CLI lokal oder Codex Cloud? Trust-Implikationen pro Variante.

## E. Kosten, Scheduling, Zeit

16. **Kosten- und Budgetmodell.** Token-Caps pro Work Item, pro Projekt, pro Tag?
    Wer bricht ab, wenn Budget reißt? Bezug: fehlt komplett in `01-11`.
17. **Scheduling-Policy.** Wie wird aus `priority_class` eine Ausführungsreihenfolge?
    Parallelismus pro Projekt, global? Starvation-Vermeidung?
    Bezug: `09` Work Item, `04` Workflow Coordination.
18. **Zeitmodell.** Deadlines auf Work Item? Waiting-Timeouts? Human-Escalation-
    Timeouts? Bezug: `05` Work Item Lifecycle `waiting`.
19. **Kapazitätsmodell.** „Kapazität wird geprüft" (`10`) — welche? Menschliche
    Aufmerksamkeit, Agent-Concurrency, Budget? Bezug: `10` Neue Arbeitsanforderung.

## F. Fachliche Vollständigkeit

20. **Definition of Done.** Wann ist ein Work Item fertig? Wie schließt sich der
    Loop in Knowledge? Bezug: `05` Work Item `completed`, AD-15.
21. **Konfliktauflösung.** Zwei Work Items benötigen dasselbe Artefakt —
    Resolution-Policy? Bezug: `09` Dependency.
22. **Approval für Single-User.** Behalten wir das Objekt, oder reicht
    `pending_confirmation` am Work Item? Bezug: `09` Approval.
23. **Standard-Versionierung.** SemVer auf Standards? Wie wirkt sich Version-Bump
    auf bestehende Bindings aus? Bezug: `05` Standard, AD-15.
24. **Dependency-Typen.** Welche `dependency_type`-Werte gibt es? Blocking,
    soft-blocking, artifact-providing, informational? Bezug: `09` Dependency.
25. **Artifact-Storage.** Wo leben Artefakte physisch? Git, Object Storage, DB-Blob?
    Bezug: `09` Artifact, `11` Glossary.

## G. Governance und Lernen

26. **Binding-Scope-Modell.** Wie wird `applicability_scope` eines Standards
    strukturiert? Projekttyp, Projekt-ID, Tag, Pfad? Bezug: `09` Standard.
27. **Promotion-Trigger.** Was schiebt einen Standard von `accepted` → `bound`?
    Manueller Akt, Schwellwert, Zeit? Bezug: AD-15.
28. **Rücknehmbarkeit.** `11` nennt „Governance = Rücknehmbarkeit" — durch welchen
    Mechanismus? Rollback-Plan pro Binding?
29. **Evidenz-Integrität.** Was heißt `Evidence.integrity_state` konkret? Signatur,
    Hash, Provenance-Kette? Bezug: `09` Evidence.

## H. Observability und Audit

30. **Audit-Log vs. Telemetrie.** Derselbe Kontext heute (`04` Observability &
    Audit). Trennen oder zusammenlegen? Audit hat Integritätsanforderungen
    (append-only, signiert), Telemetrie nicht. Bezug: `06` „Audit ist nicht
    Governance".
31. **Observability-Stack.** OTEL, Prometheus, eigene SQLite-Tabelle? Wer ist
    Konsument? Bezug: `04` Observability.

## I. Daten-Lifecycle

32. **Retention.** Wie lange bleiben Observations, Evidence, Artefakte, Events?
33. **Backup und Restore.** Welche Kontexte sind recovery-kritisch?
34. **Export und Portabilität.** Kann der Nutzer sein Portfolio verlustfrei
    exportieren?
35. **Löschung.** GDPR-relevante Pfade (auch wenn Single-User) — Konversationslogs,
    Messenger-Inhalte.

## J. Betriebsmetriken

36. **Erfolgsmetrik.** Woran misst der Nutzer, dass das System funktioniert?
    Kandidaten: aktive vs. blockierte Projekte, Median-Zeit idea → active,
    Eskalationsrate, Standard-Bind-Rate. Bezug: fehlt komplett.
37. **Health-Definition.** Was heißt „gesundes System" im Sinne von `04`
    Observability? Welche Indikatoren, welche Schwellen?

## K. Roadmap und MVP

38. **MVP-Schnitt.** Welche Kontexte sind v0, welche v1, welche v2? Vorschlag in
    `REVIEW.md` Empfehlungen — benötigt Entscheidung.
39. **Bootstrap-Projekt.** Welches Projekt ist das erste, mit dem das System sich
    selbst betreibt (Self-Hosting)? Bezug: `01` Zielbild.
40. **Refactor-Richtung.** Sollen `01-11` schlanker (5–7 Kontexte) oder tiefer
    (mehr Implementierungsdetails je Kontext) werden? Entscheidung vor weiteren
    Dokumentänderungen.
