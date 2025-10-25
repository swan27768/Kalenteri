import requests
import re
from datetime import datetime
from ..model import Event

HEADERS = {'User-Agent': 'OpenDoorsBot/1.0 (+contact@example.com)'}

VANTAA_SOURCES = [
    {
        "name": "Vantaan lukiot ja Varia",
        "url": "https://www.vantaa.fi/fi/tutustumispaivat-vantaan-lukioihin-ja-variaan",
        "location_hint": "Vantaa"
    }
]

# Esim. "ma 22.1.2025 klo 12–15", "ti 23.1. klo 9.00–11.30"
DATE_TIME_PATTERN = re.compile(
    r"(?P<weekday>ma|ti|ke|to|pe|la|su)\s+"
    r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})(?:\.(?P<year>20\d{2}))?"
    r".{0,20}?"          # vähän joustoa tekstin välissä
    r"klo\s+"
    r"(?P<sh>\d{1,2})[.:](?P<sm>\d{2})"
    r"\s*[–-]\s*"
    r"(?P<eh>\d{1,2})[.:](?P<em>\d{2})",
    re.IGNORECASE
)

def _mk_dt(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm)

def fetch_vantaa_events():
    events = []

    for src in VANTAA_SOURCES:
        url = src["url"]
        org_name = src["name"]
        location_hint = src["location_hint"]

        try:
            r = requests.get(url, timeout=30, headers=HEADERS)
            r.raise_for_status()
        except Exception as e:
            print(f"[WARN] Vantaa fetch failed {url}: {e}")
            continue

        html = r.text

        # Selvitetään vuosiviite
        # Jos vuodet puuttuu joistain riveistä (esim. '22.1.'), käytetään sivulta löytyvää ensimmäistä 20xx
        year_guess = None
        year_match = re.search(r"20\d{2}", html)
        if year_match:
            year_guess = int(year_match.group(0))

        for m in DATE_TIME_PATTERN.finditer(html):
            day = int(m.group("day"))
            month = int(m.group("month"))
            year = int(m.group("year")) if m.group("year") else year_guess

            sh = int(m.group("sh"))
            sm = int(m.group("sm"))
            eh = int(m.group("eh"))
            em = int(m.group("em"))

            if year is None:
                # Jos ei löydy edes guessia, hypätään yli ettei rikota
                continue

            start_local = _mk_dt(year, month, day, sh, sm)
            end_local   = _mk_dt(year, month, day, eh, em)

            # Yritetään löytää lähin koulun nimi tälle blokille.
            # Käytetään yksinkertaista "katsotaan 200 merkkiä taaksepäin"-tekniikkaa.
            span_start = max(0, m.start() - 200)
            context = html[span_start:m.start()]
            # etsitään esim. "Tikkurilan lukio", "Vaskivuoren lukio", "Varia Aviapolis" tms.
            school_match = re.search(
                r"(Tikkurilan lukio|Vaskivuoren lukio|Lumon lukio|Varia[^<,\n]*)",
                context,
                re.IGNORECASE
            )
            if school_match:
                place_name = school_match.group(0).strip()
            else:
                place_name = org_name

            title = f"Avoimet ovet – {place_name}"

            events.append(Event(
                title=title,
                start=start_local,
                end=end_local,
                location=place_name + ", " + location_hint,
                url=url,
                organizer=place_name,
                source_url=url
            ))

    return events
