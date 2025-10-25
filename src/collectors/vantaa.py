import requests
import re
import time
from datetime import datetime
from ..model import Event

# Käytetään melko "selainmaista" UA:ta, jotta kunnan sivu ei hermostu
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7",
}

VANTAA_SOURCES = [
    {
        "name": "Vantaan lukiot ja Varia",
        "url": "https://www.vantaa.fi/fi/tutustumispaivat-vantaan-lukioihin-ja-variaan",
        "location_hint": "Vantaa",
    }
]

# Sallitaan muodot kuten:
#  - "ma 22.1.2025 klo 12–15"
#  - "ti 23.1. klo 9.00–11.30"
#  - myös ilman viikonpäivää: "22.1.2025 klo 12-15"
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

SCHOOL_PATTERNS = [
    r"Tikkurilan lukio",
    r"Vaskivuoren lukio",
    r"Lumon lukio",
    r"Martinlaakson lukio",
    r"Varia[^<,\n]*",
]

SCHOOL_REGEX = re.compile("(" + "|".join(SCHOOL_PATTERNS) + ")", re.IGNORECASE)


def _mk_dt(y, m, d, hh, mm):
    # naive datetime, main.py normalisoi aikavyöhykkeen UTC:ksi myöhemmin
    return datetime(y, m, d, hh, mm)


def fetch_html_with_retry(url: str, max_attempts: int = 3, delay_seconds: float = 2.0):
    """
    Lataa HTML-sivun useammalla yrityksellä.
    Palauttaa sivun tekstin tai None.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, timeout=60, headers=HEADERS)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"[WARN] attempt {attempt}/{max_attempts} failed for {url}: {e}")
            if attempt < max_attempts:
                time.sleep(delay_seconds)
    return None


def fetch_vantaa_events():
    events = []

    for src in VANTAA_SOURCES:
        url = src["url"]
        org_name = src["name"]
        location_hint = src["location_hint"]

        html = fetch_html_with_retry(url)
        if html is None:
            print(f"[WARN] Vantaa fetch failed {url}: all retries gave up")
            continue

        # Arvaa vuosi sivulta: etsi ensimmäinen 20xx
        year_guess = None
        year_match = re.search(r"20\d{2}", html)
        if year_match:
            year_guess = int(year_match.group(0))

        for m in DATE_TIME_PATTERN.finditer(html):
            day = int(m.group("day"))
            month = int(m.group("month"))

            # Vuosi riviltä tai fallback
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
                # Emme voi muodostaa kelvollista päivämäärää ilman vuotta
                continue

            start_local = _mk_dt(year, month, day, sh, sm)
            end_local = _mk_dt(year, month, day, eh, em)

            # Yritä päätellä koulun nimi tutkimalla tekstiä ennen osumaa
            span_start = max(0, m.start() - 250)
            context_before = html[span_start:m.start()]

            school_match = SCHOOL_REGEX.search(context_before)
            if school_match:
                school_name = school_match.group(0).strip()
            else:
                school_name = org_name  # fallback

            title = f"Avoimet ovet – {school_name}"

            events.append(
                Event(
                    title=title,
                    start=start_local,
                    end=end_local,
                    location=f"{school_name}, {location_hint}",
                    url=url,
                    organizer=school_name,
                    source_url=url,
                )
            )

    return events
