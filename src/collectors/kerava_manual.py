import yaml
from datetime import datetime
from ..model import Event

def _parse_dt(date_str: str, time_str: str):
    # esim. "2026-01-15" + "18:00"
    year, month, day = [int(x) for x in date_str.split("-")]
    hh, mm = [int(x) for x in time_str.split(":")]
    return datetime(year, month, day, hh, mm)

def fetch_kerava_manual():
    events = []
    try:
        with open("data/kerava_manual.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        # ei kaadeta koko buildiä jos ei ole vielä tiedostoa
        return events

    for row in data.get("events", []):
        # start on pakollinen meillä
        try:
            start_dt = _parse_dt(row["date"], row["start"])
        except Exception as e:
            print(f"[WARN] Kerava manual time parse failed for {row}: {e}")
            continue

        end_dt = None
        if row.get("end"):
            try:
                end_dt = _parse_dt(row["date"], row["end"])
            except Exception as e:
                print(f"[WARN] Kerava manual end time parse failed for {row}: {e}")

        events.append(Event(
            title=row.get("title", "Avoimet ovet – Keravan lukio"),
            start=start_dt,
            end=end_dt,
            location=row.get("location"),
            url=row.get("url"),
            organizer=row.get("organizer", "Keravan lukio"),
            source_url=row.get("url"),
        ))

    return events
