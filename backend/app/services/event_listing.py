from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EventListing:
    id: str
    title: str
    start: str | None
    end: str | None
    venue: str | None
    city: str | None
    region: str | None
    url: str
    is_free: bool | None
    cost_summary: str | None
    source: str = "meetup"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start,
            "end": self.end,
            "venue": self.venue,
            "city": self.city,
            "region": self.region,
            "url": self.url,
            "is_free": self.is_free,
            "cost_summary": self.cost_summary,
            "source": self.source,
        }
