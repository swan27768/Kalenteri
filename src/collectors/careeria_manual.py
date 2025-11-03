import yaml
from datetime import datetime
from ..model import Event

def _parse_dt(date_str: str, time_str: str):
    year, month, day = [int(x) for x in date_str.split("-")]
    hh, mm = [int(x) for x in time_str.split(":")]
    return datetime(year, month, day, hh, mm)

def fetch_careeria_manual():
    events = []
    try:
        with open("data/careeria_manual.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return events

    for row in data.get("events", []):
        try:
            start_dt = _parse_dt(row["date"], row["start"])
        except Exception as e:
            print(f"[WARN] Careeria manual time parse failed for {row}: {e}")
            continue

        end_dt = None
        if row.get("end"):
            try:
                end_dt = _parse_dt(row["date"], row["end"])
            except Exception as e:
                print(f"[WARN] Careeria manual end time parse failed for {row}: {e}")

        events.append(Event(
            title=row.get("title", "Avoimet ovet – Careeria"),
            start=start_dt,
            end=end_dt,
            location=row.get("location"),
            url=row.get("url"),
            organizer=row.get("organizer", "Careeria"),
            source_url=row.get("url"),
        ))

    return events
