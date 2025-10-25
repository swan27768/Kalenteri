
import requests, json
from bs4 import BeautifulSoup
from dateutil import parser as dtparser
from typing import List
from ..model import Event

HEADERS = {'User-Agent': 'OpenDoorsBot/1.0 (+contact@example.com)'}

def _iter_jsonld(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    for s in soup.find_all('script', attrs={'type':'application/ld+json'}):
        if not s.string:
            continue
        try:
            data = json.loads(s.string)
        except Exception:
            continue
        if isinstance(data, list):
            for d in data:
                yield d
        else:
            yield data

def fetch_jsonld_events(url: str, source_name: str = None) -> List[Event]:
    r = requests.get(url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    out: List[Event] = []
    for node in _iter_jsonld(r.text):
        t = node.get('@type')
        if isinstance(t, list):
            is_event = 'Event' in t
        else:
            is_event = (t == 'Event')
        if not is_event:
            continue
        name = node.get('name') or node.get('headline')
        start = node.get('startDate')
        end = node.get('endDate')
        if not name or not start:
            continue
        try:
            start_dt = dtparser.parse(start)
            end_dt = dtparser.parse(end) if end else None
        except Exception:
            continue
        # location can be string or object
        loc = None
        loc_node = node.get('location')
        if isinstance(loc_node, dict):
            loc = loc_node.get('name') or (loc_node.get('address') if isinstance(loc_node.get('address'), str) else None)
        elif isinstance(loc_node, str):
            loc = loc_node
        event_url = node.get('url') or url
        out.append(Event(
            title=name, start=start_dt, end=end_dt, location=loc,
            url=event_url, organizer=source_name, source_url=url
        ))
    return out
