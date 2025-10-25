import requests
import re
from datetime import datetime
from ..model import Event

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}

# Täydennä tämä lista: yksi alkio per lukio
# - name: lukion nimi sellaisena kuin haluat näyttää sen sivulla
# - url: sivu jossa kerrotaan avoimet ovet / tutustumisillat / infot
# - location: postiosoite tai paikkakunta (esim. "Tikkurilan lukio, Vantaa")
VANTAA_LUKIOT = [
    {
        "name": "Tikkurilan lukio",
        "url": "https://...TIKKURILA_LUKIO_SIVU_TÄHÄN...",
        "location": "Tikkurilan lukio, Vantaa"
    },
    {
        "name": "Vaskivuoren lukio",
        "url": "https://...VASKIVUORI_SIVU_TÄHÄN...",
        "location": "Vaskivuoren lukio, Vantaa"
    },
    {
        "name": "Lumon lukio",
        "url": "https://...LUMO_SIVU_TÄHÄN...",
        "location": "Lumon lukio, Vantaa"
    },
    {
        "name": "Martinlaakson lukio",
        "url": "https://...MARTINLAAKSO_SIVU_TÄHÄN...",
        "location": "Martinlaakson lukio, Vantaa"
    },
    # lisää muut Vantaan lukiot/linjat jos on omia sivuja
    # myös Varia-toimipisteet voi laittaa tähän, jos niillä on omat "tutustuminen / avoimet ovet" -sivut
    # {
    #   "name": "Varia Aviapolis",
    #   "url": "https://...VARIA_AVIAPOLIS_SIVU_TÄHÄN...",
    #   "location": "Varia Aviapolis, Vantaa"
    # },
]

# Yritetään tunnistaa ilmoitukset kuten:
# "Avoimet ovet ti 23.1.2025 klo 17.30–19.00"
# "Tutustumisilta 14.11. klo 18-19"
#
# sallitaan muodot:
#  - 14.11.2025 klo 18–19
#  - 14.11. klo 18.00-19.30
#  - ti 23.1. klo 17.30–19.00
#
DATE_TIME_PATTERN = re.compile(
    r"(?:(?P<weekday>ma|ti|ke|to|pe|la|su)\s+)?"
    r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})"
    r"(?:\.(?P<year>20\d{2}))?"
    r".{0,40}?"
    r"klo\s+"
    r"(?P<sh>\d{1,2})[.:](?P<sm>\d{2})"
    r"\s*[–\-]\s*"
    r"(?P<eh>\d{1,2})[.:](?P<em>\d{2})",
    re.IGNORECASE,
)

def _mk_dt(y, m, d, hh, mm):
    # main.py lisää myöhemmin aikavyöhykkeen ja suodattaa menneet
    return datetime(y, m, d, hh, mm)

def fetch_vantaa_lukio():
    events = []

    for school in VANTAA_LUKIOT:
        school_name = school["name"]
        url = school["url"]
        location = school["location"]

        # hae sivu
        try:
            resp = requests.get(url, timeout=30, headers=HEADERS)
            resp.raise_for_status()
        except Exception as e:
            print(f"[WARN] Vantaa lukio fetch failed {school_name} {url}: {e}")
            continue

        html = resp.text

        # yritetään päätellä vuosi sivulta (jos päivämäärässä ei lue vuotta)
        year_guess = None
        ym = re.search(r"20\d{2}", html)
        if ym:
            year_guess = int(ym.group(0))

        # regexillä kaikki päivämäärä+ajankohdat
        for m in DATE_TIME_PATTERN.finditer(html):
            day = int(m.group("day"))
            month = int(m.group("month"))

            year = m.group("year")
            if year:
                year = int(year)
            else:
                year = year_guess

            sh = int(m.group("sh"))
            sm = int(m.group("sm"))
            eh = int(m.group("eh"))
            em = int(m.group("em"))

            if year is None:
                # ei uskalleta ilman vuotta
                continue

            start_local = _mk_dt(year, month, day, sh, sm)
            end_local   = _mk_dt(year, month, day, eh,  em)

            # Otsikoksi jotain selkeää
            # Haetaan jonkinlainen fraasi ennen matchia (esim. "Avoimet ovet", "Tutustumisilta")
            context_before = html[max(0, m.start()-200):m.start()]
            title_match = re.search(
                r"(Avoimet ovet|Tutustumisilta|Esittelyilta|Infoilta)[^.<]{0,80}",
                context_before,
                re.IGNORECASE
            )
            if title_match:
                raw_title = title_match.group(0).strip()
            else:
                raw_title = "Avoimet ovet"

            # Rakennetaan lopullinen otsikko
            title = f"{raw_title} – {school_name}"

            events.append(Event(
                title=title,
                start=start_local,
                end=end_local,
                location=location,
                url=url,
                organizer=school_name,
                source_url=url,
            ))

    return events
