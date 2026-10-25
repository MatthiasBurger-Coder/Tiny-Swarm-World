---
name: github-sub-issues
description: Erstellt und verknüpft echte native GitHub-Sub-Issues unter einer Epic und verifiziert die Parent-Beziehungen. Pflicht bei jeder Epic-Erstellung sowie beim Zuordnen bestehender Issues oder Prüfen ihrer Parent-Beziehungen.
---

# Native GitHub-Sub-Issues verwalten

Verwende diesen Skill zwingend bei jeder Epic-Erstellung sowie wenn der Nutzer Sub-Issues für eine GitHub-Epic erstellen, bestehende Issues unter eine Epic hängen oder Parent-Beziehungen prüfen lassen möchte. Eine Markdown-Checklist oder ein `Parent: #N` im Issue-Text ist keine native Sub-Issue-Beziehung.

Bei einem rein lokalen Epic-Entwurf die geplanten Child-Issues und die noch ausstehende native Verifikation festhalten. Der Skill allein autorisiert keine GitHub-Schreiboperationen. Bei beauftragter GitHub-Veröffentlichung gehören native Verknüpfung und Verifikation zur Epic-Erstellung; ohne Nachweis keinen abgeschlossenen Verknüpfungsstatus melden.

## Voraussetzungen

- Repository und Epic eindeutig bestimmen; `owner/repo` und Parent-Issue-Nummer feststellen.
- Vor dem Erstellen auf vorhandene Sub-Issues und verwandte offene Issues prüfen, um Duplikate zu vermeiden. Listen vollständig mit Pagination abrufen.
- Für neue Arbeit im Repository `AGENTS.md` beachten. Bei Dateiänderungen gelten insbesondere dessen Branch-Regeln; für reine GitHub-Issue-Operationen ist keine lokale Dateiänderung erforderlich.
- `gh` muss authentifiziert sein und ausreichende Issue-Berechtigungen besitzen. Alternativ kann ein GitHub-Connector verwendet werden, sofern er die nativen Sub-Issues-Endpunkte bereitstellt.

## Native Verknüpfung mit GitHub CLI

GitHub verwendet `sub_issue_id` als numerische Datenbank-ID des Child-Issues. Das ist **nicht** die sichtbare Issue-Nummer und darf nicht aus einer anderen Issue-Antwort übernommen werden.

Für jedes Child-Issue die numerische ID direkt aus genau diesem Issue abrufen:

```bash
gh api repos/OWNER/REPO/issues/CHILD_NUMBER --jq '{number,title,id,node_id,parent_issue_url}'
```

Vor dem Verknüpfen prüfen:

- `number` entspricht der gewünschten Child-Issue-Nummer.
- `title` ist das erwartete Issue.
- `id` ist die numerische Issue-ID, die als `sub_issue_id` verwendet wird.
- `parent_issue_url` ist leer oder bereits der gewünschte Parent. Ein Issue kann nur einen Parent haben.

Ist bereits der gewünschte Parent gesetzt, die Beziehung verifizieren und den POST überspringen.

Sub-Issue nativ hinzufügen (den Platzhalter `CHILD_DATABASE_ID` durch die validierte numerische ID ersetzen):

```bash
gh api repos/OWNER/REPO/issues/PARENT_NUMBER/sub_issues \
  --method POST \
  --input - <<'JSON'
{"sub_issue_id": CHILD_DATABASE_ID}
JSON
```

Nicht mehrere Mutationen parallel ausführen, solange nicht alle Child-IDs einzeln zweifelsfrei ermittelt wurden. Bei mehreren Items sequenziell verknüpfen. Ein HTTP-422-Fehler wie „Sub issue may only have one parent“ bedeutet, dass das Child bereits einem Parent zugeordnet ist. Nicht mit erzwungenen oder geratenen IDs wiederholen; Parent des Childs auslesen und den Konflikt korrekt behandeln.

## Verifizieren

Die Beziehung muss über GitHub-Daten geprüft werden, nicht nur über Issue-Beschreibung oder erfolgreiche HTTP-Antwort:

```bash
gh api --paginate repos/OWNER/REPO/issues/PARENT_NUMBER/sub_issues \
  --jq '.[] | {number,title,parent_issue_url}'

gh api repos/OWNER/REPO/issues/CHILD_NUMBER \
  --jq '{number,title,parent_issue_url}'

gh api repos/OWNER/REPO/issues/PARENT_NUMBER \
  --jq '.sub_issues_summary'
```

Für jedes gewünschte Child muss gelten:

1. Es erscheint in der Sub-Issue-Liste des Parents.
2. Das Child enthält `parent_issue_url`, das auf genau den Parent verweist.
3. Die Zusammenfassung des Parents weist die erwartete Gesamtzahl aus. Bereits vorhandene Childs mitzählen; erneut zugeordnete Childs nicht doppelt zählen.

Eine Markdown-Checklist darf zusätzlich zur Lesbarkeit synchronisiert werden, ersetzt diese Verifikation aber nie.

## Issues anlegen und verknüpfen

Wenn neue Sub-Issues gewünscht sind:

1. Epic und Bestand prüfen.
2. Umsetzbare Child-Issues mit eigenständigem Ziel und prüfbaren Abnahmekriterien formulieren.
3. Child-Issues anlegen und jede zurückgegebene sichtbare Nummer verwenden, um die numerische Datenbank-ID einzeln abzurufen.
4. IDs einzeln validieren und Childs nacheinander mit dem Parent-Endpunkt verbinden.
5. Parent- und Child-Daten sowie die Parent-Zusammenfassung verifizieren.
6. Dem Nutzer die Child-Issues und den geprüften nativen Verknüpfungsstatus nennen. Nicht behaupten, eine native Beziehung sei gesetzt, wenn nur Text oder Links in der Epic existieren.

## Grenzen und Fehlerfälle

- Ist die GitHub-CLI oder Integration nicht berechtigt, den Sub-Issue-Endpunkt aufzurufen, die genaue Grenze nennen und keine Text-Checkliste als gleichwertigen Ersatz darstellen.
- Ist das Child bereits einem anderen Parent zugeordnet, diese Beziehung nicht stillschweigend überschreiben oder entfernen. Den Konflikt melden und nur bei ausdrücklichem Auftrag die bestehende Parent-Verknüpfung ändern.
- Bei unklarer API-Antwort den Zustand erneut lesen, bevor ein Schreibaufruf wiederholt wird. Bereits erstellte Child-Issues melden und bei Wiederaufnahme wiederverwenden, statt Duplikate anzulegen.
- Sichtbare Issue-Nummer, numerische Datenbank-ID und GraphQL-Node-ID sind verschiedene Werte. Für `sub_issue_id` wird die numerische Datenbank-ID aus `.id` im Issue-Objekt benötigt.
