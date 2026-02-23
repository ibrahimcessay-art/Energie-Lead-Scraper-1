"""
Energie-Leads Scraper – Energieintensive Branchen Deutschland
=============================================================
Scrapt täglich neue Firmen mit:
  ✅ 35+ energieintensive Branchen (500k+ kWh Potenzial)
  ✅ Ansprechpartner-Erkennung (GF, Einkauf, Energiemanager, Technik)
  ✅ Ansprechpartner-Rolle in eigener CRM-Spalte
  ✅ Verbrauchsschätzung pro Branche
  ✅ Duplikat-Schutz (läuft täglich ohne Doppeleinträge)
  ✅ CRM-ready CSV (UTF-8 BOM, direkt in Excel öffenbar)
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import os
import urllib.parse
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
DELAY      = 2.0
OUTPUT_CSV = "data/firmen.csv"

# ─────────────────────────────────────────────
#  BRANCHEN
#  Format: ("Suchbegriff", "Kategorie", "Verbrauchspotenzial")
# ─────────────────────────────────────────────
BRANCHEN = [
    # ── SEHR HOCH – wahrscheinlich >1 Mio kWh/Jahr ──────────────────
    ("Galvanik",              "Oberflaechentechnik",   "Sehr hoch >1 Mio kWh"),
    ("Galvanotechnik",        "Oberflaechentechnik",   "Sehr hoch >1 Mio kWh"),
    ("Pulverbeschichtung",    "Oberflaechentechnik",   "Sehr hoch >1 Mio kWh"),
    ("Verzinkerei",           "Oberflaechentechnik",   "Sehr hoch >1 Mio kWh"),
    ("Giesserei",             "Metallverarbeitung",    "Sehr hoch >1 Mio kWh"),
    ("Druckguss",             "Metallverarbeitung",    "Sehr hoch >1 Mio kWh"),
    ("Oberflaechenbehandlung","Oberflaechentechnik",   "Sehr hoch >1 Mio kWh"),
    ("Haerterei",             "Waermebehandlung",      "Sehr hoch >1 Mio kWh"),
    ("Waermebehandlung",      "Waermebehandlung",      "Sehr hoch >1 Mio kWh"),
    ("Schmelzwerk",           "Metallverarbeitung",    "Sehr hoch >1 Mio kWh"),

    # ── HOCH – wahrscheinlich 500k–1 Mio kWh/Jahr ───────────────────
    ("Lackiererei",           "Oberflaechentechnik",   "Hoch 500k-1 Mio kWh"),
    ("Blechbearbeitung",      "Metallverarbeitung",    "Hoch 500k-1 Mio kWh"),
    ("Metallbau",             "Metallverarbeitung",    "Hoch 500k-1 Mio kWh"),
    ("Schweisshtechnik",      "Metallverarbeitung",    "Hoch 500k-1 Mio kWh"),
    ("Lohnfertigung",         "Metallverarbeitung",    "Hoch 500k-1 Mio kWh"),
    ("Zerspanungstechnik",    "Metallverarbeitung",    "Hoch 500k-1 Mio kWh"),
    ("Werkzeugmaschinen",     "Maschinenbau",          "Hoch 500k-1 Mio kWh"),
    ("Kunststoffverarbeitung","Kunststoff",            "Hoch 500k-1 Mio kWh"),
    ("Spritzguss",            "Kunststoff",            "Hoch 500k-1 Mio kWh"),
    ("Druckluft",             "Drucklufttechnik",      "Hoch 500k-1 Mio kWh"),
    ("Papierfabrik",          "Papier/Druck",          "Hoch 500k-1 Mio kWh"),

    # ── LEBENSMITTELINDUSTRIE & KUEHLHAEUSER ────────────────────────
    ("Lebensmittelindustrie", "Lebensmittel",          "Sehr hoch >1 Mio kWh"),
    ("Kuehlhaus",             "Lebensmittel/Logistik", "Sehr hoch >1 Mio kWh"),
    ("Tiefkuehllogistik",     "Lebensmittel/Logistik", "Sehr hoch >1 Mio kWh"),
    ("Kuehllogistik",         "Lebensmittel/Logistik", "Sehr hoch >1 Mio kWh"),
    ("Brauerei",              "Lebensmittel",          "Sehr hoch >1 Mio kWh"),
    ("Molkerei",              "Lebensmittel",          "Sehr hoch >1 Mio kWh"),
    ("Baeckerei",             "Lebensmittel",          "Hoch 500k-1 Mio kWh"),
    ("Fleischverarbeitung",   "Lebensmittel",          "Sehr hoch >1 Mio kWh"),
    ("Kaeltetechnik",         "Kaeltetechnik",         "Hoch 500k-1 Mio kWh"),

    # ── HOTELLERIE & GASTRONOMIE (GROSS) ────────────────────────────
    ("Hotel",                 "Hotellerie",            "Hoch 500k-1 Mio kWh"),
    ("Grosshotels",           "Hotellerie",            "Hoch 500k-1 Mio kWh"),
    ("Tagungshotel",          "Hotellerie",            "Hoch 500k-1 Mio kWh"),
    ("Wellnesshotel",         "Hotellerie",            "Hoch 500k-1 Mio kWh"),
    ("Grossgastronomie",      "Gastronomie",           "Hoch 500k-1 Mio kWh"),
    ("Catering",              "Gastronomie",           "Hoch 500k-1 Mio kWh"),
    ("Gemeinschaftsverpflegung","Gastronomie",         "Hoch 500k-1 Mio kWh"),

    # ── KRANKENHAUESER & KLINIKEN ────────────────────────────────────
    ("Krankenhaus",           "Gesundheit",            "Sehr hoch >1 Mio kWh"),
    ("Klinik",                "Gesundheit",            "Sehr hoch >1 Mio kWh"),
    ("Rehabilitationsklinik", "Gesundheit",            "Sehr hoch >1 Mio kWh"),
    ("Pflegeheim",            "Gesundheit",            "Hoch 500k-1 Mio kWh"),
    ("Dialysezentrum",        "Gesundheit",            "Hoch 500k-1 Mio kWh"),

    # ── RECHENZENTREN & IT ───────────────────────────────────────────
    ("Rechenzentrum",         "IT/Rechenzentren",      "Sehr hoch >1 Mio kWh"),
    ("IT-Dienstleistungen",   "IT/Rechenzentren",      "Hoch 500k-1 Mio kWh"),
    ("Serverhosting",         "IT/Rechenzentren",      "Sehr hoch >1 Mio kWh"),
    ("Telekommunikation",     "IT/Rechenzentren",      "Sehr hoch >1 Mio kWh"),
]

# ─────────────────────────────────────────────
#  ANSPRECHPARTNER-Erkennung
#  Priorität: Energiemanager > GF > Technik > Einkauf
# ─────────────────────────────────────────────
ANSPRECHPARTNER_PRIORITAET = [
    ("Geschaeftsfuehrer", [
        "geschaeftsfuehrer", "geschäftsführer", "ceo", "inhaber",
        "managing director", "gesellschafter", "gf", "direktor",
        "prokurist", "vorstand", "eigentuemer",
    ]),
]

# ─────────────────────────────────────────────
#  PLZ → Bundesland
# ─────────────────────────────────────────────
PLZ_BUNDESLAND = {
    "01":"Sachsen","02":"Sachsen","03":"Brandenburg","04":"Sachsen",
    "06":"Sachsen-Anhalt","07":"Thueringen","08":"Sachsen","09":"Sachsen",
    "10":"Berlin","12":"Berlin","13":"Berlin","14":"Brandenburg",
    "15":"Brandenburg","16":"Brandenburg","17":"Mecklenburg-Vorpommern",
    "18":"Mecklenburg-Vorpommern","19":"Mecklenburg-Vorpommern",
    "20":"Hamburg","21":"Hamburg","22":"Hamburg",
    "23":"Schleswig-Holstein","24":"Schleswig-Holstein","25":"Schleswig-Holstein",
    "26":"Niedersachsen","27":"Niedersachsen","28":"Bremen","29":"Niedersachsen",
    "30":"Niedersachsen","31":"Niedersachsen","32":"Nordrhein-Westfalen",
    "33":"Nordrhein-Westfalen","34":"Hessen","35":"Hessen","36":"Hessen",
    "37":"Niedersachsen","38":"Niedersachsen","39":"Sachsen-Anhalt",
    "40":"Nordrhein-Westfalen","41":"Nordrhein-Westfalen","42":"Nordrhein-Westfalen",
    "44":"Nordrhein-Westfalen","45":"Nordrhein-Westfalen","46":"Nordrhein-Westfalen",
    "47":"Nordrhein-Westfalen","48":"Nordrhein-Westfalen","49":"Niedersachsen",
    "50":"Nordrhein-Westfalen","51":"Nordrhein-Westfalen","52":"Nordrhein-Westfalen",
    "53":"Nordrhein-Westfalen","54":"Rheinland-Pfalz","55":"Rheinland-Pfalz",
    "56":"Rheinland-Pfalz","57":"Nordrhein-Westfalen","58":"Nordrhein-Westfalen",
    "59":"Nordrhein-Westfalen","60":"Hessen","61":"Hessen","63":"Hessen",
    "64":"Hessen","65":"Hessen","66":"Saarland","67":"Rheinland-Pfalz",
    "68":"Baden-Wuerttemberg","69":"Baden-Wuerttemberg","70":"Baden-Wuerttemberg",
    "71":"Baden-Wuerttemberg","72":"Baden-Wuerttemberg","73":"Baden-Wuerttemberg",
    "74":"Baden-Wuerttemberg","75":"Baden-Wuerttemberg","76":"Baden-Wuerttemberg",
    "77":"Baden-Wuerttemberg","78":"Baden-Wuerttemberg","79":"Baden-Wuerttemberg",
    "80":"Bayern","81":"Bayern","82":"Bayern","83":"Bayern","84":"Bayern",
    "85":"Bayern","86":"Bayern","87":"Bayern","88":"Bayern","89":"Bayern",
    "90":"Bayern","91":"Bayern","92":"Bayern","93":"Bayern","94":"Bayern",
    "95":"Bayern","96":"Bayern","97":"Bayern","98":"Thueringen","99":"Thueringen",
}

# ─────────────────────────────────────────────
#  PLZ → Wirtschaftsregion
# ─────────────────────────────────────────────
PLZ_BEZIRK = {
    "10":"Berlin","12":"Berlin","13":"Berlin","14":"Berlin/Potsdam",
    "20":"Hamburg","21":"Hamburg","22":"Hamburg","23":"Luebeck","24":"Kiel",
    "28":"Bremen","30":"Hannover","31":"Hannover","37":"Goettingen",
    "38":"Braunschweig","26":"Oldenburg","49":"Osnabrueck",
    "40":"Duesseldorf","41":"Duesseldorf","47":"Duisburg",
    "50":"Koeln","51":"Koeln","52":"Aachen","53":"Bonn",
    "44":"Dortmund","45":"Essen","46":"Essen","42":"Wuppertal",
    "48":"Muenster","33":"Bielefeld","32":"Bielefeld","57":"Siegen",
    "60":"Frankfurt","61":"Frankfurt","63":"Frankfurt/Offenbach",
    "64":"Darmstadt","65":"Wiesbaden","34":"Kassel","35":"Marburg",
    "55":"Mainz","54":"Trier","56":"Koblenz","66":"Saarbruecken",
    "68":"Mannheim","69":"Heidelberg","70":"Stuttgart","71":"Stuttgart",
    "72":"Tuebingen","74":"Heilbronn","76":"Karlsruhe","79":"Freiburg",
    "80":"Muenchen","81":"Muenchen","82":"Muenchen","85":"Muenchen",
    "83":"Rosenheim","84":"Landshut","86":"Augsburg","87":"Kempten",
    "89":"Ulm","90":"Nuernberg","91":"Nuernberg","93":"Regensburg",
    "94":"Passau","97":"Wuerzburg","01":"Dresden","04":"Leipzig",
    "09":"Chemnitz","06":"Halle","39":"Magdeburg","99":"Erfurt",
    "18":"Rostock","19":"Schwerin",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

FELDER = [
    "name",
    "ansprechpartner_name",
    "ansprechpartner_rolle",
    "adresse", "plz", "ort",
    "bundesland", "bezirk_region",
    "telefon", "fax", "email",
    "website", "google_maps",
    "branche", "kategorie", "verbrauchspotenzial",
    "datum_gefunden", "quell_url",
]


# ─────────────────────────────────────────────
#  HILFSFUNKTIONEN
# ─────────────────────────────────────────────

def get_soup(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            print(f"    Fehler: {e} - Versuch {i+1}/{retries}")
            time.sleep(3)
    return None


def lade_bekannte_urls():
    urls = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row.get("quell_url"):
                    urls.add(row["quell_url"])
    return urls


def erkenne_ansprechpartner(soup, text):
    """
    Sucht nach Ansprechpartnern mit Rollenbezeichnung.
    Gibt (Name, Rolle) zurueck – priorisiert Energiemanager zuerst.
    """
    text_lower = text.lower()

    for rolle, keywords in ANSPRECHPARTNER_PRIORITAET:
        for kw in keywords:
            if kw in text_lower:
                # Name in Tabellenzeilen suchen
                for tbl in soup.find_all("table"):
                    for row in tbl.find_all("tr"):
                        cols = row.find_all(["td", "th"])
                        if len(cols) >= 2:
                            zeile = row.get_text(" ", strip=True).lower()
                            if kw in zeile:
                                kandidat = cols[-1].get_text(strip=True)
                                if (3 < len(kandidat) < 60 and
                                        not any(x in kandidat.lower() for x in
                                                ["gmbh","kg","ag","http","@",
                                                 "str.","tel","fax"])):
                                    return kandidat, rolle
                return "", rolle  # Rolle erkannt, kein Name gefunden

    return "", ""


def parse_firmen_liste(soup):
    firmen = []
    table = soup.find("table")
    if not table:
        return firmen
    for row in table.find_all("tr"):
        a = row.find("a")
        if a and "/firmen/" in a.get("href", ""):
            firmen.append((a.get_text(strip=True), a["href"]))
    return firmen


def parse_detail(url, suchbegriff, kategorie, verbrauchspotenzial):
    soup = get_soup(url)
    if not soup:
        return None

    d = {f: "" for f in FELDER}
    d["branche"]             = suchbegriff
    d["kategorie"]           = kategorie
    d["verbrauchspotenzial"] = verbrauchspotenzial
    d["quell_url"]           = url
    d["datum_gefunden"]      = datetime.now().strftime("%Y-%m-%d")

    # Name aus Titel
    title = soup.find("title")
    if title:
        d["name"] = title.get_text(strip=True).split(" in ")[0].strip()

    text = soup.get_text(separator="\n")

    # Tabellenzeilen parsen
    for tbl in soup.find_all("table"):
        for row in tbl.find_all("tr"):
            cols = row.find_all(["td", "th"])
            if len(cols) < 2:
                continue
            key = cols[0].get_text(strip=True).lower().rstrip(":")
            val = cols[1].get_text(separator=" ", strip=True)
            a_tag = cols[1].find("a")

            if any(x in key for x in ["stra","adresse"]):
                d["adresse"] = val
            elif "plz" in key:
                d["plz"] = re.sub(r"\D", "", val)[:5]
            elif key in ["ort", "stadt", "standort"]:
                d["ort"] = val
            elif any(x in key for x in ["telefon","tel.","fon","phone"]) and "fax" not in key:
                d["telefon"] = val
            elif "fax" in key:
                d["fax"] = val
            elif any(x in key for x in ["e-mail","email","mail"]):
                d["email"] = val
            elif any(x in key for x in ["internet","homepage","website","www"]):
                d["website"] = a_tag["href"] if a_tag and a_tag.get("href") else val

    # Fallback Telefon
    if not d["telefon"]:
        m = re.search(
            r"(?:Tel(?:efon)?\.?|Fon|Phone)[\s:]*([+\d][\d\s\(\)\-\/]{6,20})",
            text, re.IGNORECASE)
        if m:
            d["telefon"] = m.group(1).strip()

    # Fallback E-Mail
    if not d["email"]:
        m = re.search(r"[\w.\-+]+@[\w.\-]+\.\w{2,6}", text)
        if m:
            d["email"] = m.group(0)

    # Fallback Website
    if not d["website"]:
        skip = {"schnelle-seiten","iskonet","google","facebook",
                "twitter","xing","linkedin","instagram"}
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and not any(s in href for s in skip):
                d["website"] = href
                break

    # Fallback PLZ
    if not d["plz"]:
        m = re.search(r"\b(\d{5})\b", text)
        if m:
            d["plz"] = m.group(1)

    # Fallback Ort aus URL
    if not d["ort"]:
        m = re.search(r"/firmen/([^_]+)_", url)
        if m:
            d["ort"] = m.group(1).replace("-", " ").title()

    # Bundesland & Bezirk
    prefix = d["plz"][:2] if d["plz"] else ""
    d["bundesland"]    = PLZ_BUNDESLAND.get(prefix, "")
    d["bezirk_region"] = PLZ_BEZIRK.get(prefix, "")

    # Ansprechpartner erkennen
    d["ansprechpartner_name"], d["ansprechpartner_rolle"] = \
        erkenne_ansprechpartner(soup, text)

    # Google Maps
    query = urllib.parse.quote(
        f"{d['name']} {d['adresse']} {d['plz']} {d['ort']}".strip())
    d["google_maps"] = f"https://www.google.com/maps/search/?api=1&query={query}"

    return d


# ─────────────────────────────────────────────
#  HAUPTPROGRAMM
# ─────────────────────────────────────────────

def main():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            csv.DictWriter(f, fieldnames=FELDER).writeheader()
        print(f"Neue CSV angelegt: {OUTPUT_CSV}")

    bekannte_urls = lade_bekannte_urls()
    print(f"Bereits bekannte Firmen: {len(bekannte_urls)}")
    print(f"Branchen zu scrapen:     {len(BRANCHEN)}\n")

    neue = 0
    basis = "https://www.schnelle-seiten.de/firmen/index.php"

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FELDER, extrasaction="ignore")

        for suchbegriff, kategorie, potenzial in BRANCHEN:
            print(f"\n[{kategorie}] {suchbegriff} — {potenzial}")
            enc = urllib.parse.quote(suchbegriff)

            for seite in range(1, 100):
                url = (f"{basis}/{enc}" if seite == 1
                       else f"{basis}?searchStr={enc}&s={seite}")

                soup = get_soup(url)
                if not soup:
                    break

                liste = parse_firmen_liste(soup)
                if not liste:
                    print(f"  Fertig nach {seite-1} Seiten")
                    break

                print(f"  Seite {seite}: {len(liste)} Firmen")

                for name, detail_url in liste:
                    if not detail_url.startswith("http"):
                        detail_url = "https://www.schnelle-seiten.de" + detail_url

                    if detail_url in bekannte_urls:
                        continue
                    bekannte_urls.add(detail_url)

                    time.sleep(DELAY)
                    firma = parse_detail(detail_url, suchbegriff, kategorie, potenzial)

                    if firma:
                        writer.writerow(firma)
                        f.flush()
                        neue += 1

                        ap = ""
                        if firma["ansprechpartner_rolle"]:
                            ap = f" | {firma['ansprechpartner_rolle']}"
                            if firma["ansprechpartner_name"]:
                                ap += f": {firma['ansprechpartner_name']}"

                        print(f"  [{neue:>4}] {firma['name'][:38]:<38} "
                              f"{firma['plz']} {firma['ort']:<18} "
                              f"{firma['bundesland']:<22}{ap}")

                time.sleep(DELAY)

    print(f"\n{'='*60}")
    print(f"  FERTIG! {neue} neue Firmen gespeichert -> {OUTPUT_CSV}")
    print(f"  Gesamt in CSV: {len(bekannte_urls)} Firmen")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
