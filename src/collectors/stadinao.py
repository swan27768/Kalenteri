import requests
import re
from datetime import datetime, timezone
from ..model import Event

HEADERS = {'User-Agent': 'OpenDoorsBot/1.0 (+contact@example.com)'}

# Lisää tähän kaikki Stadin AO:n avoimet ovet / vierailupäivät -sivut,
# jos niitä on useita. Tässä oletetaan yksi keskus-sivu.
STADIN_SITES = [
    {
        "name": "Stadin AO",
        "url": "https://stadinao.hel.fi/",
        "location": "Stadin AO, Helsinki"
    },
    # Jos heillä on tarkempi sivu esim. oppilaitosvierailut / avoimet ovet:
    # {
    #   "name": "Stadin AO (Ilkantie)",
    #   "url": "https://stadinao.hel.fi/tietoa-stadin-aosta/oppilaitosvierailut/",
    #   "location": "Ilkantie, Helsinki"
    # },
]

# Haetaan päivämäärät muodossa:
# 25.11.2025
# 3.2.2026
# ja mahdollinen aika:
# klo 9.00–14.30
DATE_PATTERN = re.compile(
    r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>20\d{2})",
    re.IGNORECASE
)

TIME_PATTERN = re.compile(
    r"klo\s+(?P<sh>\d{1,2})[.:](?P<sm>\d{2})\s*[–-]\s*(?P<eh>\d{1,2})[.:](?P<em>\d{2})",
    re.IGNORECASE
)

def _dt_local(y, month, day, hour, minute):
    return datetime(y, month, day, hour, minute)

def fetch_stadinao_events() -> list[Event]:
    events = []

    for site in STADIN_SITES:
        name = site["name"]
        url = site["url"]
        location = site["location"]

        try:
            r = requests.get(url, timeout=30, headers=HEADERS)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            print(f"[WARN] Failed to load Stadin AO site {url}: {e}")
            continue

        # Kaivetaan kaikki päivämäärät
        for dm in DATE_PATTERN.finditer(html):
            day = int(dm.group("day"))
            month = int(dm.group("month"))
            year = int(dm.group("year"))

            # Yritetään löytää kellonaika läheltä samaa kohtaa sivulla
            # Oikeasti voisit parantaa tätä kontekstihakua,
            # nyt mennään yksinkertaisesti: etsi TIME_PATTERN koko sivulta
            # ja käytä samaa aikaa kaikille päiville jos löytyy.
            tm = TIME_PATTERN.search(html)
            if tm:
                sh = int(tm.group("sh"))
                sm = int(tm.group("sm"))
                eh = int(tm.group("eh"))
                em = int(tm.group("em"))
                start_dt_local = _dt_local(year, month, day, sh, sm)
                end_dt_local = _dt_local(year, month, day, eh, em)
            else:
                # jos ei kellonaikaa löydy, luodaan vain aloitus klo 09–10 oletuksella
                start_dt_local = _dt_local(year, month, day, 9, 0)
                end_dt_local   = _dt_local(year, month, day, 10, 0)

            title = f"Avoimet ovet – {name}"

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
