
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
from icalendar import Calendar, Event as ICalEvent, vText
import hashlib
import json

@dataclass
class Event:
    title: str
    start: datetime
    end: Optional[datetime] = None
    location: Optional[str] = None
    url: Optional[str] = None
    organizer: Optional[str] = None
    source_url: Optional[str] = None

    @property
    def id(self) -> str:
        base = f"{self.title}|{self.start.isoformat()}|{self.location or ''}"
        return hashlib.sha1(base.encode('utf-8')).hexdigest()

    def to_dict(self):
        d = asdict(self)
        d['id'] = self.id
        # ISO format with timezone when available
        for k in ['start', 'end']:
            if d.get(k):
                d[k] = d[k].isoformat()
        return d


def dump_events_json(events: List[Event]) -> str:
    payload = [e.to_dict() for e in events]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def dump_events_ics(events: List[Event]) -> bytes:
    cal = Calendar()
    cal.add('prodid', '-//OpenDoorsBot//EN')
    cal.add('version', '2.0')
    for e in events:
        ve = ICalEvent()
        ve.add('uid', e.id + '@opendoors.bot')
        ve.add('summary', vText(e.title))
        ve.add('dtstart', e.start)
        if e.end:
            ve.add('dtend', e.end)
        if e.location:
            ve.add('location', vText(e.location))
        if e.url:
            ve.add('url', vText(e.url))
        cal.add_component(ve)
    return cal.to_ical()
