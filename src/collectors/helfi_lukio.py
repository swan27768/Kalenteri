import requests
import re
from datetime import datetime, timezone
from ..model import Event

HEADERS = {'User-Agent': 'OpenDoorsBot/1.0 (+contact@example.com)'}

# Lista lukioista, joita halutaan seurata.
# Lisää tänne kaikki Helsingin lukiot, joilla on vastaava "Tutustu ja hae" / avoimet ovet -sivu.
LUKIOT = [
    {
        "name": "Alppilan lukio",
        "url": "https://www.hel.fi/fi/kasvatus-ja-koulutus/alppilan-lukio/tutustu-ja-hae",
        "location": "Alppilan lukio, Viipurinkatu 21, Helsinki"
    },
    {
        "name": "Kallion lukio",
        "url": "https://www.hel.fi/fi/kasvatus-ja-koulutus/kallion-lukio/tutustu-ja-hae",
        "location": "Kallion lukio, Helsinki"
    },
    {
        "name": "Ressun lukio",
        "url": "https://www.hel.fi/fi/kasvatus-ja-koulutus/ressun-lukio/tutustu-ja-hae/nain-haet",
        "location": "Ressun lukio, Helsinki"
    },
    {
        "name": "Mäkelänrinteen lukio",
        "url": "https://www.hel.fi/fi/kasvatus-ja-koulutus/makelanrinteen-lukio/tutustu-ja-hae/makelanrinteen-lukion-esittelyt-kevaalla-2026",
        "location": "Mäkelänrinteen lukio, Helsinki"
    },
    {
        "name": "Etu-Töölön lukio",
        "url": "https://www.hel.fi/fi/kasvatus-ja-koulutus/etu-toolon-lukio/tutustu-tylyyn",
        "location": "Etu-Töölön lukio, Helsinki"
    },
    {
        "name": "Helsingin luonnontiedelukio",
        "url": "https://www.hel.fi/fi/kasvatus-ja-koulutus/helsingin-luonnontiedelukio/tutustu-ja-hae",
        "location": "Helsingin luonnontiedelukio, Helsinki"
    },
    {
        "name": "Helsingin medialukio",
        "url": "https://www.hel.fi/fi/kasvatus-ja-koulutus/helsingin-medialukio/tutustu-ja-hae",
        "location": "Helsingin medialukio, Helsinki"
    },

    {
        "name": "SYK",
        "url": "https://syk.fi/lukio/hakeminen/",
        "location": "Suomalais-venäläinen koulu / SYK, Helsinki"
    },
    {
        "name": "Helsingin kielilukio",
        "url": "https://www.hel.fi/fi/kasvatus-ja-koulutus/helsingin-kielilukion-esittelytilaisuudet-9-luokkalaisille-seka-huoltajille-alkavat-marraskuussa",
        "location": "Helsingin kielilukio, Helsinki"
    },
     {
        "name": "Konepajan lukio",
        "url": "https://www.hel.fi/fi/kasvatus-ja-koulutus/konepajan-lukio/tutustu-konepajan-lukioon",
        "location": "Konepajan lukio, Helsinki"
    },
    # Lisää tähän loput lukioista samalla kaavalla
]


# regex:
#   ke 14.1.2026 klo 10.30–12.00
#   ti 27.1.2026 klo 19.00–21.00 on lisäksi avoimien ovien tilaisuus huoltajille
PATTERN = re.compile(
    r"(?P<weekday>ma|ti|ke|to|pe|la|su)\s+"
    r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})(?:\.(?P<year>20\d{2}))?\s+"
    r"klo\s+"
    r"(?P<start_h>\d{1,2})[.:](?P<start_m>\d{2})"
    r"\s*[-–]\s*"
    r"(?P<end_h>\d{1,2})[.:](?P<end_m>\d{2})"
    r"(?P<extra>[^<\n]*)",
    re.IGNORECASE
)

# Etsitään ensin mikä vuosi on kyseessä, esim. "Avoimet ovet 2026"
YEAR_FALLBACK = re.compile(r"Avoimet\s+ovet\s+(20\d{2})", re.IGNORECASE)

def _ensure_datetime(y, month, day, hour, minute):
    # Rakentaa timezone-naive datetimein paikalliseen aikaan (Helsinki),
    # UTC-annotointi tehdään myöhemmin main.py:ssä ensure_datetime-funktiossa.
    return datetime(y, month, day, hour, minute)

def fetch_all_helfi_lukio() -> list[Event]:
    events = []

    for school in LUKIOT:
        name = school["name"]
        url = school["url"]
        location = school["location"]

        try:
            r = requests.get(url, timeout=30, headers=HEADERS)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            print(f"[WARN] Failed to load {name} ({url}): {e}")
            continue

        # Arvaa vuosi "Avoimet ovet 2026" -osiosta
        m_year = YEAR_FALLBACK.search(html)
        if m_year:
            default_year = int(m_year.group(1))
        else:
            default_year = datetime.now(timezone.utc).year

        # Etsi kaikki ottelut
        for m in PATTERN.finditer(html):
            day = int(m.group("day"))
            month = int(m.group("month"))
            year = int(m.group("year")) if m.group("year") else default_year

            sh = int(m.group("start_h"))
            sm = int(m.group("start_m"))
            eh = int(m.group("end_h"))
            em = int(m.group("end_m"))

            extra = (m.group("extra") or "").strip()

            # Esim "Avoimet ovet (huoltajille)" jos tekstissä mainitaan huoltajista
            title = f"Avoimet ovet – {name}"
            if "huoltaj" in extra.lower():
                title = f"Avoimet ovet (huoltajille) – {name}"

            start_dt_local = _ensure_datetime(year, month, day, sh, sm)
            end_dt_local = _ensure_datetime(year, month, day, eh, em)

            events.append(Event(
                title=title,
                start=start_dt_local,
                end=end_dt_local,
                location=location,
                url=url,
                organizer=name,
                source_url=url
            ))

    return events

        
        
