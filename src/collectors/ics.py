
import requests
from icalendar import Calendar
from datetime import datetime
from typing import List
from ..model import Event

HEADERS = {'User-Agent': 'OpenDoorsBot/1.0 (+contact@example.com)'}

def fetch_ics(url: str, source_name: str = None) -> List[Event]:
    r = requests.get(url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    cal = Calendar.from_ical(r.content)
    out: List[Event] = []
    for comp in cal.walk('VEVENT'):
        start = comp.get('DTSTART').dt
        end = comp.get('DTEND').dt if comp.get('DTEND') else None
        title = str(comp.get('SUMMARY'))
        loc = str(comp.get('LOCATION') or '') or None
        link = str(comp.get('URL') or '') or None
        out.append(Event(
            title=title, start=start, end=end, location=loc,
            url=link, organizer=source_name, source_url=url
        ))
    return out
