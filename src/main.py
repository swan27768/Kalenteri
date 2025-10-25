import argparse, os, yaml
from datetime import datetime, timezone
from typing import List
from .model import Event, dump_events_json, dump_events_ics
from .collectors.ics import fetch_ics
from .collectors.jsonld import fetch_jsonld_events
from .collectors.helfi_lukio import fetch_all_helfi_lukio
from .collectors.stadinao import fetch_stadinao_events
from .collectors.vantaa import fetch_vantaa_events


def load_sources(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def dedupe(events: List[Event]) -> List[Event]:
    seen = set()
    out = []
    for e in events:
        key = (
            e.title.strip().lower(),
            e.start.isoformat(),
            (e.location or '').strip().lower()
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def run(sources_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    data = load_sources(sources_path)
    events: List[Event] = []

    # ICS sources (esim. julkiset Google-kalenterit)
    for item in (data.get('ics') or []):
        try:
            events.extend(fetch_ics(item['url'], item.get('name')))
        except Exception as e:
            print(f"[WARN] ICS failed for {item}: {e}")

    # HTML (JSON-LD) sources (sivut joilla on schema.org/Event datana)
    for item in (data.get('html') or []):
        try:
            events.extend(fetch_jsonld_events(item['url'], item.get('name')))
        except Exception as e:
            print(f"[WARN] HTML JSON-LD failed for {item}: {e}")

    # HELSINGIN LUKIOT (useita kouluja yhdellä kierrolla)
    try:
        events.extend(fetch_all_helfi_lukio())
    except Exception as e:
        print(f"[WARN] helfi lukio fetch failed: {e}")

    # STADIN AMMATTIOPISTO
    try:
        events.extend(fetch_stadinao_events())
    except Exception as e:
        print(f"[WARN] Stadin AO fetch failed: {e}")
        
   # VANTAAN LUKIOT JA VARIA
    try:
        events.extend(fetch_vantaa_events())
    except Exception as e:
        print(f"[WARN] Vantaa fetch failed: {e}")
        
    # Suodata + normalisoi ajat
    now = datetime.now(timezone.utc)
    keep = []

    def ensure_datetime(dt):
        """
        Ottaa joko datetime- tai date-olion ja palauttaa timezone-aware datetime UTC:ssä.
        """
        if hasattr(dt, "tzinfo"):
            # dt on datetime-tyyppi (tai datetime-like)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        else:
            # dt on pelkkä date-olio -> tulkitaan klo 00:00 paikallista päivää UTC:ssa
            return datetime(dt.year, dt.month, dt.day, 0, 0, 0, tzinfo=timezone.utc)

    for e in events:
        # normalisoi alku ja loppu datet -> datetimes
        e.start = ensure_datetime(e.start)
        if e.end:
            e.end = ensure_datetime(e.end)

        # suodatus: pidä tulevat + viimeiset 30 päivää
        if (e.start >= now) or ((now - e.start).days <= 30):
            keep.append(e)

    events = dedupe(keep)
    events.sort(key=lambda e: e.start)

    # Kirjoita ulostulot
    json_path = os.path.join(out_dir, 'events.json')
    ics_path = os.path.join(out_dir, 'opendoors.ics')

    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(dump_events_json(events))

    with open(ics_path, 'wb') as f:
        f.write(dump_events_ics(events))

    print(f"Wrote {len(events)} events → {json_path}, {ics_path}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--sources', default='sources.yaml')
    ap.add_argument('--out', default='dist')
    args = ap.parse_args()
    run(args.sources, args.out)

