import yaml
from datetime import datetime
from ..model import Event

def _parse_dt(date_str: str, time_str: str):
    # esim. "2025-10-29" + "09:00"
    year, month, day = [int(x) for x in date_str.split("-")]
    hh, mm = [int(x) for x in time_str.split(":")]
    return datetime(year, month, day, hh, mm)

def fetch_keuda_manual():
    events = []
    try:
        with open("data/keuda_manual.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        # jos tiedostoa ei ole, ei kaadeta koko julkaisua
        return events

    for row in data.get("events", []):
        # yritetään rakentaa start ja mahdollinen end
        try:
            start_dt = _parse_dt(row["date"], row["start"])
        except Exception as e:
            print(f"[WARN] Keuda manual time parse failed for {row}: {e}")
            continue

        end_dt = None
        if row.get("end"):
            try:
                end_dt = _parse_dt(row["date"], row["end"])
            except Exception as e:
                print(f"[WARN] Keuda manual end time parse failed for {row}: {e}")

        events.append(Event(
            title=row.get("title", "Avoimet ovet – Keuda"),
            start=start_dt,
            end=end_dt,
            location=row.get("location"),
            url=row.get("url"),
            organizer=row.get("organizer", "Keuda"),
            source_url=row.get("url"),
        ))

    return events
