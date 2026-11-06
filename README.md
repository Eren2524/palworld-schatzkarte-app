# Palworld Schatzkarte – iPhone-App

Die offline-fähige Schatzkarte als eigene App. Jeder Push auf `main` baut automatisch eine unsignierte `Schatzkarte.ipa`
(Tab **Actions** → letzter Lauf → **Artifacts** → `Schatzkarte-IPA`). Die IPA mit Sideloadly und deiner Apple-ID aufs iPhone laden.

Häkchen und Plan werden zusätzlich in einer Datei im App-Ordner gespeichert und überstehen Neustarts und das Neu-Aufspielen nach 7 Tagen.

## Version 2.0 – neues Design

- Karte im Vollbild, Bedienung über ein Bottom-Sheet (nach oben ziehen) mit Tab-Leiste: Plan, Karte, Pals, Wissen.
- Marker-Cluster beim Rauszoomen (Kreisring zeigt, welche Kategorien drinstecken), Tippen zoomt hinein.
- Filter-Chips oben (Welt, Kategorien, Erledigtes ausblenden), Fortschrittsring in der Kopfzeile.
- Detail-Karte statt Popup, Suche über Punkte und Pal-Spawns, Koordinaten-Chips im Text springen auf die Karte.
- Nur sichtbare Marker werden gezeichnet (Canvas), dadurch flüssiges Zoomen auch mit allen Ebenen.
- Haptisches Feedback beim Abhaken, Tippen und Plan erstellen.
- Häkchen, Plan und Einstellungen bleiben beim Update erhalten (gleicher Speicher wie 1.x).
