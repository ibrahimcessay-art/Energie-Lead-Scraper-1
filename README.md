# Energie-Leads Scraper

Taeglich automatisch neue B2B-Leads aus energieintensiven Branchen.
Zielgruppe: Firmen mit 500.000+ kWh Verbrauch (Strom & Gas Gewerbe).

## CSV-Spalten (CRM-ready)

| Spalte               | Beschreibung                              | CRM-Filter |
|----------------------|-------------------------------------------|------------|
| name                 | Firmenname                                |            |
| ansprechpartner_name | Name der Kontaktperson                    | Ja         |
| ansprechpartner_rolle| Geschaeftsfuehrer / Einkauf / Energie ... | Ja         |
| adresse              | Strasse + Hausnummer                      |            |
| plz                  | Postleitzahl                              |            |
| ort                  | Stadt                                     |            |
| bundesland           | Bundesland                                | Ja         |
| bezirk_region        | Wirtschaftsregion (Muenchen, Koeln ...)   | Ja         |
| telefon              | Telefonnummer                             |            |
| fax                  | Faxnummer                                 |            |
| email                | E-Mail Adresse                            |            |
| website              | Webseite                                  |            |
| google_maps          | Direktlink Google Maps                    |            |
| branche              | Suchbegriff (Galvanik, Giesserei ...)     | Ja         |
| kategorie            | Oberkategorie (Metallverarbeitung ...)    | Ja         |
| verbrauchspotenzial  | Sehr hoch / Hoch                          | Ja         |
| datum_gefunden       | Datum des Scrapings                       | Ja         |
| quell_url            | Link zur Originalseite                    |            |

## Einrichtung GitHub Actions (einmalig, 5 Minuten)

### Schritt 1: GitHub Account
Auf https://github.com anmelden (kostenlos).

### Schritt 2: Neues Repository anlegen
1. Gruenes "New"-Button oben links klicken
2. Name: "energie-leads-scraper"
3. "Private" auswaehlen (Daten nur fuer dich)
4. "Create repository" klicken

### Schritt 3: Dateien hochladen
1. "uploading an existing file" klicken
2. Alle 3 Dateien hochladen:
   - scraper.py
   - .github/workflows/daily_scraper.yml
   - README.md
3. "Commit changes" klicken

### Schritt 4: Actions aktivieren
1. Oben auf "Actions" klicken
2. "I understand my workflows, go ahead and enable them" klicken

### Schritt 5: Ersten Lauf manuell starten
1. Actions > "Taeglich Energie-Leads scrapen" klicken
2. "Run workflow" > "Run workflow" klicken
3. Warten bis gruener Haken erscheint (ca. 30-60 Minuten)

### Schritt 6: CSV herunterladen
1. Auf "data/" Ordner klicken
2. "firmen.csv" anklicken
3. Download-Button klicken

Ab jetzt laueft er jeden Morgen um 06:00 Uhr automatisch!
Neue Firmen werden taeglich hinzugefuegt, Duplikate automatisch herausgefiltert.
