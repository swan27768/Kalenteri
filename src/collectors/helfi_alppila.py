import requests
import re
from datetime import datetime, timezone
from dateutil import parser as dtparser
from ..model import Event

HEADERS = {'User-Agent': 'OpenDoorsBot/1.0 (+contact@example.com)'}

def fetch_alppila_open_doors(url: str, source_name: str = None):
    """
    Hakee Alppilan lukion "Tutustu ja hae" -sivun ja yrittää löytää
    Avoimet ovet 20XX -osion alla listatut päivät ja kellonajat.
    Palauttaa listan Event-olioita.
    """
    r = requests.get(url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    text = r.text

    events = []

    # 1. Selvitä vuosi otsikosta "Avoimet ovet 2026"
    year_match = re.search(r"Avoimet\\s+ovet\\s+(20\\d{2})", text, re.IGNORECASE)
    if year_match:
        year = int(year_match.group(1))
    else:
        # fallback: nykyinen vuosi jos ei löydy
        year = datetime.now(timezone.utc).year

    # 2. Etsi rivit tyyliin:
    #   * to 8.1.2026 klo 14.00-15.30
    #   * ke 14.1.2026 klo 10.30-12.00
    #   * ti 27.1.2026 klo 19.00-21.00 on lisäksi avoimien ovien tilaisuus huoltajille
    #
    # Selitys regexistä:
    # - viikonpäivä lyhenteenä (ma|ti|ke|to|pe|la|su)
    # - pvm muodossa d.m. tai d.m.yyyy
    # - "klo"
    # - alku & loppuajat HH.MM-HH.MM
    pattern = re.compile(
        r"(?P<weekday>ma|ti|ke|to|pe|la|su)\\s+"
        r"(?P<day>\\d{1,2})\\.(?P<month>\\d{1,2})(?:\\.(?P<y>20\\d{2}))?\\s+"
        r"klo\\s+"
        r"(?P<start_h>\\d{1,2})[.:](?P<start_m>\\d{2})"
        r"\\s*[-–]\\s*"
        r"(?P<end_h>\\d{1,2})[.:](?P<end_m>\\d{2})"
        r"(?P<extra>[^<]*)",
        re.IGNORECASE
    )

    for m in pattern.finditer(text):
        day = int(m.group("day"))
        month = int(m.group("month"))
        y = int(m.group("y")) if m.group("y") else year

        sh = int(m.group("start_h"))
        sm = int(m.group("start_m"))
        eh = int(m.group("end_h"))
        em = int(m.group("end_m"))

        # Rakennetaan alku- ja loppuajat Helsinki-ajassa (oletuksena Europe/Helsinki)
        # ja muutetaan ne UTC:ksi (modelin kirjoitus tekee myöhemmin kuitenkin UTC).
        # Tässä teemme tietoisesti naive -> Europe/Helsinki oletuksen.
        # (Voit hienosäätää, mutta tämä riittää julkaisuun.)
        start_dt_local = datetime(y, month, day, sh, sm)
        end_dt_local   = datetime(y, month, day, eh, em)

        # Lisätään selite (esim. "huoltajille") mukaan otsikkoon jos sellainen on.
        extra = m.group("extra").strip()
        base_title = "Avoimet ovet"
        if "huoltaj" in extra.lower():
            base_title = "Avoimet ovet (huoltajille)"

        events.append(Event(
            title=base_title + " – Alppilan lukio",
            start=start_dt_local,
            end=end_dt_local,
            location="Alppilan lukio, Viipurinkatu 21, Helsinki",
            url=url,
            organizer=source_name or "Alppilan lukio",
            source_url=url,
        ))

    return events
