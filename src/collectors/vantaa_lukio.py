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

# 🔴 TÄRKEÄ: laita oikea URL tänne Lumon lukiolle,
# kunhan sellainen on (nyt laitetaan se, jonka annoit).
# Voit lisätä muitakin lukioita myöhemmin.
VANTAA_LUKIOT = [
    {
        "name": "Lumon lukio",
        "url": "https://lumonlukio.vantaa.fi/fi/ajankohtaista",
        "location": "Lumon lukio, Urpiaisentie 14, 01450 Vantaa"
    },
    # Lisää myöhemmin esim. Tikkurilan lukio, Vaskivuoren lukio, jne.
    # {
    #     "name": "Tikkurilan lukio",
    #     "url": "https://tikkurilanlukio.vantaa.fi/.../hakijainfo",
    #     "location": "Tikkurilan lukio, Vantaa"
    # },
]

# Esimerkkejä muodoista joita haluamme nappailla:
#  - "Avoimet ovet ti 23.1.2026 klo 17.30–19.00"
#  - "Tutustumisilta 14.11. klo 18-19"
#  - "20.1.2026 klo 13–15"
#
# Sallitaan:
#  - viikonpäivä vapaaehtoinen (ma/ti/ke/...)
#  - päivä.kuukausi.(vuosi optional)
#  - "klo HH.MM–HH.MM" tai "klo HH:MM-HH:MM"
DATE_TIME_PATTERN = re.compile(
    r"(?:(?P<weekday>ma|ti|ke|to|pe|la|su)\s+)?"
    r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})"
    r"(?:\.(?P<year>20\d{2}))?"
    r"[^k]{0,80}?"       # vähän joustoa ennen "klo"
    r"klo\s+"
    r"(?P<sh>\d{1,2})[.:](?P<sm>\d{2})"
    r"\s*[–\-]\s*"
    r"(?P<eh>\d{1,2})[.:](?P<em>\d{2})",
    re.IGNORECASE,
)

def _mk_dt(y, m, d, hh, mm):
    # main.py huolehtii aikavyöhykkeestä ja filtteröinnistä myöhemmin
    return datetime(y, m, d, hh, mm)

def fetch_vantaa_lukio():
    """
    Palauttaa listan Event-olioita Vantaan lukioiden (ja Varian)
    sivuilta kaivetun tekstin perusteella.
    Jos sivu ei aukea GitHub Actionsissa (timeout tms),
    kyseisen lukion kohdalta mennään vain ohitse, eikä kaadeta koko ajoa.
    """
    events = []

    for school in VANTAA_LUKIOT:
        school_name = school["name"]
        url = school["url"]
        location = school["location"]

        try:
            resp = requests.get(url, timeout=30, headers=HEADERS)
            resp.raise_for_status()
        except Exception as e:
            print(f"[WARN] Vantaa lukio fetch failed {school_name} {url}: {e}")
            continue

        html = resp.text

        # Arvaa vuosi sivun sisällöstä (jos päivämäärässä ei erikseen lue vuotta)
        year_guess = None
        ym = re.search(r"20\d{2}", html)
        if ym:
            year_guess = int(ym.group(0))

        # Käydään läpi kaikki "päivä.kk.(vvvv) klo HH:MM–HH:MM" -osumat
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

            # Jos emme tiedä vuotta, ei voida tehdä validia datetimeä
            if year is None:
                continue

            start_local = _mk_dt(year, month, day, sh, sm)
            end_local   = _mk_dt(year, month, day, eh, em)

            # Otsikko: yritetään ottaa kontekstista joku kuvaava fraasi
            # ennen osumaa, esim. "Avoimet ovet", "Tutustumisilta"
            context_before = html[max(0, m.start()-200):m.start()]
            title_match = re.search(
                r"(Avoimet ovet|Tutustumisilta|Infoilta|Esittelyilta)[^.<\n]{0,80}",
                context_before,
                re.IGNORECASE
            )
            if title_match:
                raw_title = title_match.group(0).strip()
            else:
                raw_title = "Avoimet ovet"

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

