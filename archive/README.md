# Archive

Dieses Verzeichnis enthält historische Dokumente, die für die Entstehung der
V1-Spezifikation relevant waren, aber **nicht mehr normativ sind**. Sie
bleiben erhalten für Nachvollziehbarkeit und als Kontext für zukünftige
Reviews, nicht als Quelle für neue Spec-Entscheidungen.

## Inhalt

### `legacy-notes/` — Erste Brainstorm-Notizen (12 Dateien)

Die ursprünglichen Notizen `00-README.md` bis `11-glossary.md`. Postulieren
13 Bounded Contexts, 12 Kernobjekte, 17 Architekturprinzipien und weitere
Strukturen für einen Single-User-Einsatz. Diese Struktur wurde in
`REVIEW.md` als systematisch überdimensioniert identifiziert und in der
V1-Spezifikation auf 5 Module und 9 Kernobjekte reduziert.

**Nicht als Referenz in neuen ADRs zitieren.** Wenn ein Konzept aus den
Legacy-Notizen in die Spec zurückkehren soll, führt der Weg über die
Synthese (`docs/research/99-synthesis.md`) und einen neuen oder
aktualisierten ADR.

### `REVIEW.md` — Ursprüngliche Kritik

Das erste externe Review der Legacy-Notizen. Identifizierte den Over-
Engineering-Befund, die Ownership-Konflikte und die fehlende
Implementierungs­substanz. Führte zur Entscheidung, V1 als eigenständige
Spezifikation neu zu erfinden.

### `12-open-questions.md` — Ursprüngliche Lückenliste

40 adressierbare Spezifikations-Lücken, die aus dem REVIEW abgeleitet
wurden. Viele davon wurden durch die Research-Briefs 01–17 beantwortet.
Offene Punkte, die noch relevant sind, stehen aktualisiert in
`docs/spec/SPECIFICATION.md §11.3`.

## Status-Regel

- Kein Dokument in `archive/` darf für neue Spec-Aussagen als Quelle
  verwendet werden.
- Änderungen an Dokumenten in `archive/` sind **nicht vorgesehen** — sie
  sind eingefroren.
- Wenn sich eine Legacy-Idee als tragfähig erweist, kommt sie als neuer
  Research-Brief oder ADR in die normative Struktur zurück, nicht als
  Legacy-Zitat.
