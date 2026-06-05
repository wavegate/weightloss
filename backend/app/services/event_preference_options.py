"""Allowed values aligned with platform filters (Meetup, Eventbrite, Funcheap, Luma)."""

from typing import Literal

TimingPreference = Literal["upcoming", "today", "weekend", "free", "date-range"]

BAY_AREA_LOCATIONS: list[dict[str, str]] = [
    {"id": "cupertino", "label": "Cupertino"},
    {"id": "mountain-view", "label": "Mountain View"},
    {"id": "palo-alto", "label": "Palo Alto"},
    {"id": "sunnyvale", "label": "Sunnyvale"},
    {"id": "san-jose", "label": "San Jose"},
    {"id": "san-francisco", "label": "San Francisco"},
    {"id": "oakland", "label": "Oakland"},
    {"id": "berkeley", "label": "Berkeley"},
    {"id": "fremont", "label": "Fremont"},
    {"id": "menlo-park", "label": "Menlo Park"},
]

TIMING_OPTIONS: list[dict[str, str]] = [
    {"id": "upcoming", "label": "Any upcoming"},
    {"id": "today", "label": "Today"},
    {"id": "weekend", "label": "This weekend"},
    {"id": "free", "label": "Free events"},
    {"id": "date-range", "label": "Specific date range"},
]

# Eventbrite category slugs + Meetup-style topics.
EVENT_CATEGORY_OPTIONS: list[dict[str, str]] = [
    {"id": "tech", "label": "Tech & startups"},
    {"id": "networking", "label": "Networking"},
    {"id": "music", "label": "Music"},
    {"id": "food-drink", "label": "Food & drink"},
    {"id": "family", "label": "Family & education"},
    {"id": "sports", "label": "Sports & fitness"},
    {"id": "arts", "label": "Arts & entertainment"},
    {"id": "community", "label": "Community & culture"},
    {"id": "health", "label": "Health & wellness"},
]

VALID_LOCATION_IDS = {item["id"] for item in BAY_AREA_LOCATIONS}
VALID_TIMING_IDS = {item["id"] for item in TIMING_OPTIONS}
VALID_CATEGORY_IDS = {item["id"] for item in EVENT_CATEGORY_OPTIONS}

DEFAULT_HOME_LOCATION = "cupertino"
DEFAULT_TIMING: TimingPreference = "upcoming"
DEFAULT_DISTANCE_MILES = 25
DEFAULT_CATEGORIES: list[str] = []
