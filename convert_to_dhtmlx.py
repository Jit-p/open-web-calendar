import datetime
from flask import jsonify
from conversion_base import ConversionStrategy
import recurring_ical_events
import icalendar
from dateutil.parser import parse as parse_date
import pytz
from clean_html import clean_html, remove_html
from collections import defaultdict
from typing import List


def is_date(date):
    """Whether the date is a datetime.date and not a datetime.datetime"""
    return isinstance(date, datetime.date) and not isinstance(date, datetime.datetime)


class ConvertToDhtmlx(ConversionStrategy):
    """Convert events to dhtmlx. This conforms to a stratey pattern.

    - timeshift_minutes is the timeshift specified by the calendar
        for dates.
    """

    def created(self):
        """Set attribtues when created."""
        try:
            self.timezone = pytz.timezone(self.specification["timezone"])
        except pytz.UnknownTimeZoneError:
            self.timezone = pytz.FixedOffset(-int(self.specification["timeshift"]))

    def date_to_string(self, date):
        """Convert a date to a string."""
        # use ISO format
        # see https://docs.dhtmlx.com/scheduler/howtostart_nodejs.html#step4implementingcrud
        # see https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat
        # see https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
        if is_date(date):
            date = datetime.datetime(date.year, date.month, date.day, tzinfo=self.timezone)
        elif date.tzinfo is None:
            date = self.timezone.localize(date)
        # convert to other timezone, see https://stackoverflow.com/a/54376154
        viewed_date = date.astimezone(self.timezone)
        return viewed_date.strftime("%Y-%m-%d %H:%M")

    def convert_ical_event(self, calendar_index, calendar_event):
        start = calendar_event["DTSTART"].dt
        end = calendar_event.get("DTEND", calendar_event["DTSTART"]).dt
        if is_date(start) and is_date(end) and end == start:
            end = datetime.timedelta(days=1) + start
        geo = calendar_event.get("GEO", None)
        if geo:
            geo = {"lon": geo.longitude, "lat": geo.latitude}
        name = calendar_event.get("SUMMARY", "")
        sequence = str(calendar_event.get("SEQUENCE", 0))
        uid = calendar_event.get("UID", "") # issue 69: UID is helpful for debugging but not required
        start_date = self.date_to_string(start)
        return {
            "start_date": start_date,
            "end_date": self.date_to_string(end),
            "start_date_iso": start.isoformat(),
            "end_date_iso": end.isoformat(),
            "start_date_iso_0": start.isoformat(),
            "end_date_iso_0": end.isoformat(),
            "text": name,
            "description": clean_html(calendar_event.get("DESCRIPTION", ""), self.specification),
            "location": calendar_event.get("LOCATION", None),
            "geo": geo,
            "uid": uid,
            "ical": calendar_event.to_ical().decode("UTF-8"),
            "sequence": sequence,
            "recurrence": None,
            "url": calendar_event.get("URL"),
            "id": uid + "-" + start_date.replace(" ", "-").replace(":", "-"),
            "type": "event",
            "color": calendar_event.get("COLOR", calendar_event.get("X-APPLE-CALENDAR-COLOR", "")),
            "categories": self.get_event_categories(calendar_event),
            "css-classes": ["event"] + self.get_event_classes(calendar_event) + [f"CALENDAR-INDEX-{calendar_index}"]
        }

    def convert_error(self, error, url, tb_s):
        """Create an error which can be used by the dhtmlx scheduler."""
        now = datetime.datetime.now();
        now_iso = now.isoformat()
        now_s = self.date_to_string(now)
        return {
            "start_date": now_s,
            "end_date": now_s,
            "start_date_iso": now_iso,
            "end_date_iso": now_iso,
            "start_date_iso_0": now_iso,
            "end_date_iso_0": now_iso,
            "text":  type(error).__name__,
            "description": str(error),
            "traceback": tb_s,
            "location": None,
            "geo": None,
            "uid": "error",
            "ical": "",
            "sequence": 0,
            "recurrence": None,
            "url": url,
            "id": id(error),
            "type": "error",
            "css-classes": ["error"]
        }

    def merge(self):
        return jsonify(self.components)

    def collect_components_from(self, calendar_index, calendars):
        # see https://stackoverflow.com/a/16115575/1320237
        today = (
            parse_date(self.specification["date"])
            if self.specification.get("date")
            else datetime.datetime.utcnow()
        )
        to_date = (
            parse_date(self.specification["to"])
            if self.specification.get("to")
            else today.replace(year=today.year + 1)
        )
        from_date = (
            parse_date(self.specification["from"])
            if self.specification.get("from")
            else today.replace(year=today.year - 1)
        )
        for calendar in calendars:
            events = recurring_ical_events.of(calendar).between(from_date, to_date)
            with self.lock:
                for event in events:
                    json_event = self.convert_ical_event(calendar_index, event)
                    self.components.append(json_event)

    def get_event_classes(self, event) -> List[str]:
        """Return the CSS classes that should be used for the event styles."""
        classes = []
        for attr in ["UID", "TRANSP", "STATUS", "CLASS", "PRIORITY"]:
            value = event.get(attr)
            if value is not None:
                classes.append(f"{attr}-{value}")
        if event.get("CLASS") not in [None, "PUBLIC", "CONFIDENTIAL", "PRIVATE"]:
            classes.append("CLASS-PRIVATE") # unrecognized is private
        for category in self.get_event_categories(event):
            classes.append(f"CATEGORY-{category}")
        return classes

    def get_event_categories(self, event) -> List[str]:
        """Return the categories of the event."""
        categories = event.get("CATEGORIES", None)
        return categories.cats if categories is not None else []
