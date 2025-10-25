import requests
import re
from datetime import datetime
from ..model import Event

HEADERS = {
    "User-Agent": "OpenDoorsBot/1.0 (+contact@example.com)"
}

VANTAA_SOURCES = [
    {
        "name": "Vantaan lukiot ja Varia",
        "url": "https://www.vantaa.fi/fi/tutustumispaivat-vantaan-lukioihin-ja-variaan",
        "location_hint": "Vantaa"
    }
]

DATE_TIME_PATTERN = re.compile(
    r"(?P<weekday>ma|ti|ke|to|pe|la|su)\s+"
    r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})(?:\.(?P<year>20\d{2}))?"
    r".{0,40}?"
    r"klo\s+"
    r"(?P<sh>\d{1,2})[.:](?P<sm>\d{2})"
    r"\s*[–-]\s*"
    r"(?P<eh>\d{1,2})[.:](?P<em>\d{2})",
    re.IGNORECASE
)

SCHOOL_PATTERNS = [
    r"Tikkurilan lukio",
    r"Vaskivuoren lukio",
    r"Lumon lukio",
    r"Martinlaakson lukio",
    r"Varia[^<,\n]*",
]

SCHOOL_REGEX = re.compile(
    "(" + "|".join(SCHOOL_PATTERNS) + ")",
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
            resp = requests.get(url, timeout=30, headers=HEADERS)
            resp.raise_for_status()
        except Exception as e:
            print(f"[WARN] Vantaa fetch failed {url}: {e}")
            continue

        html = resp.text

        # Yritetään arvata vuosi, esim. "2025"
        year_guess = None
        year_match = re.search(r"20\d{2}", html)
        if year_match:
            year_guess = int(year_match.group(0))

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
                # ei uskalleta tehdä tapahtumaa ilman vuotta
                continue

            start_local = _mk_dt(year, month, day, sh, sm)
            end_local   = _mk_dt(year, month, day, eh, em)

            # etsi koulun nimi 250 merkkiä ennen osumaa
            span_start = max(0, m.start() - 250)
            context_before = html[span_start:m.start()]

            school_match = SCHOOL_REGEX.search(context_before)
            if school_match:
                school_name = school_match.group(0).strip()
            else:
                school_name = org_name  # fallback: yleinen otsikko

            title = f"Avoimet ovet – {school_name}"

            events.append(Event(
                title=title,
                start=start_local,
                end=end_local,
                location=f"{school_name}, {location_hint}",
                url=url,
                organizer=school_name,
                source_url=url,
            ))

    return events
