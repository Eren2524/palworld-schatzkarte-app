# Palworld Schatzkarte – iPhone-App

Die offline-fähige Schatzkarte als eigene App, verteilt über **Enriques Store** (SideStore/AltStore-Quelle).

## Enriques Store

- Webseite: https://eren2524.github.io/palworld-schatzkarte-app/
- Store-Quelle (stabil): `https://eren2524.github.io/palworld-schatzkarte-app/apps.json`
- Store-Quelle (Beta): `https://eren2524.github.io/palworld-schatzkarte-app/apps-beta.json`

**Neues Update veröffentlichen:** `MARKETING_VERSION` in `project.yml` erhöhen, oben in `CHANGELOG.md` einen Abschnitt `## <Version>` schreiben, pushen.
Die Pipeline baut die IPA, legt ein GitHub-Release an, erzeugt Store und Webseite neu und schickt eine ntfy-Benachrichtigung.
Pushes ohne neue Version bauen nur den Store neu.

**Beta:** Actions → „IPA bauen und Store aktualisieren“ → *Run workflow* → Kanal `beta`. Text kommt aus dem Abschnitt `## Unveröffentlicht`.

**Store anpassen:** `store/store.json` (Name, Apps, Empfehlungen), `store/news.json` (eigene News), `store/site/` (Webseite und Bilder).
Weitere Apps: Eintrag in `store.json` → `apps` mit eigenem `repo`, `tagPrefix` und `asset`.

Häkchen und Plan werden zusätzlich in einer Datei im App-Ordner gespeichert und überstehen Neustarts und das Neu-Aufspielen nach 7 Tagen.

## Version 2.0 – neues Design

- Karte im Vollbild, Bedienung über ein Bottom-Sheet (nach oben ziehen) mit Tab-Leiste: Plan, Karte, Pals, Wissen.
- Marker-Cluster beim Rauszoomen (Kreisring zeigt, welche Kategorien drinstecken), Tippen zoomt hinein.
- Filter-Chips oben (Welt, Kategorien, Erledigtes ausblenden), Fortschrittsring in der Kopfzeile.
- Detail-Karte statt Popup, Suche über Punkte und Pal-Spawns, Koordinaten-Chips im Text springen auf die Karte.
- Nur sichtbare Marker werden gezeichnet (Canvas), dadurch flüssiges Zoomen auch mit allen Ebenen.
- Haptisches Feedback beim Abhaken, Tippen und Plan erstellen.
- Häkchen, Plan und Einstellungen bleiben beim Update erhalten (gleicher Speicher wie 1.x).
