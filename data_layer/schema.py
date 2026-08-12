"""Dataset schema map.

EDIT THIS FILE FIRST.

Every CSV column name in the whole project lives here and nowhere else.
The values below are best guesses based on the original Kaggle datasets;
your cleaned files may differ.

You may not have to edit much: `resolve()` falls back to normalised
matching (case/space/underscore insensitive) and then to the SYNONYMS
table, so `Google review rating`, `google_review_rating` and `rating` all
resolve to the logical column "rating" automatically. Open the
"Dataset Doctor" expander in the sidebar to see exactly what resolved and
what did not.

`file` may be a filename or a list of candidate filenames - the first one
present in data/cleaned/ wins.
"""

from __future__ import annotations

from pathlib import Path

import config
from utils.helpers import norm_header

DATASETS: dict[str, dict] = {
    
    "destinations": {
        "label": "Tourist guide / must-see places",
        "file": ["tourist_guide.csv", "detailed_cleaned.csv", "places.csv"],
        "columns": {
            "name": "Name",
            "city": "City",
            "state": "State",
            "zone": "Zone",
            "type": "Type",
            "description": "Significance",
            "rating": "Google review rating",
            "entry_fee": "Entrance Fee in INR",
            "best_time": "Best Time to visit",
            "time_needed": "time needed to visit in hrs",
            "weekly_off": "Weekly Off",
        },
        "text_columns": ["description", "type", "name", "best_time"],
        "required": ["name", "city"],
    },
    
    "hotels": {
        "label": "Hotels (Goibibo)",
        "file": ["hotel_info.csv", "hotels.csv", "goibibo_hotels.csv"],
        "columns": {
            "name": "property_name",
            "city": "city",
            "state": "state",
            "area": "area",
            "type": "property_type",
            "description": "hotel_description",
            "rating": "site_review_rating",
            "star_rating": "hotel_star_rating",
            "price": "price",
            "amenities": "hotel_facilities",
            "review_count": "site_review_count",
            "latitude": "latitude",
            "longitude": "longitude",
        },
        "text_columns": ["description", "amenities", "area", "type", "name"],
        "required": ["name", "city"],
    },
    
    "itineraries": {
        "label": "Reference itineraries",
        "file": ["itinerary.csv", "itinerary_dataset.csv", "indian_tourism_itinerary.csv"],
        "columns": {
            "city": "City",
            "state": "State",
            "day": "Day",
            "activity": "Activity",
            "description": "Description",
            "duration": "Duration",
            "cost": "Cost",
            "category": "Category",
        },
        "text_columns": ["activity", "description", "category"],
        "required": ["city"],
    },
    
    "cities": {
        "label": "Travel cities",
        "file": ["travel_cities.csv", "cities.csv"],
        "columns": {
            "city": "City",
            "state": "State",
            "zone": "Zone",
            "description": "Description",
            "best_time": "Best Time to visit",
            "rating": "Rating",
            "latitude": "latitude",
            "longitude": "longitude",
        },
        "text_columns": ["description", "best_time"],
        "required": ["city"],
    },
    
    "details": {
        "label": "Detailed cleaned reference",
        "file": ["detailed_cleaned.csv", "detailed.csv"],
        "columns": {
            "name": "Name",
            "city": "City",
            "state": "State",
            "type": "Type",
            "description": "Significance",
            "rating": "Google review rating",
            "entry_fee": "Entrance Fee in INR",
            "best_time": "Best Time to visit",
        },
        "text_columns": ["description", "type", "name"],
        "required": ["city"],
    },
}



SYNONYMS: dict[str, list[str]] = {
    "name": ["name", "propertyname", "placename", "attraction", "title", "hotelname", "spot"],
    "city": ["city", "cityname", "location", "place", "destination", "town"],
    "state": ["state", "statename", "region", "province"],
    "zone": ["zone", "region", "area"],
    "type": ["type", "category", "propertytype", "placetype", "kind", "attractiontype"],
    "description": [
        "description", "significance", "about", "details", "overview",
        "hoteldescription", "summary", "info",
    ],
    "rating": [
        "rating", "googlereviewrating", "sitereviewrating", "userrating",
        "reviewrating", "score", "avgrating", "averagerating",
    ],
    "star_rating": ["hotelstarrating", "starrating", "stars", "hotelstar"],
    "entry_fee": ["entrancefeeininr", "entryfee", "entrancefee", "fee", "ticketprice", "price"],
    "best_time": ["besttimetovisit", "besttime", "bestseason", "idealtime", "seasontovisit"],
    "time_needed": ["timeneededtovisitinhrs", "timeneeded", "durationhrs", "visitduration"],
    "weekly_off": ["weeklyoff", "closedon", "dayclosed"],
    "price": [
        "price", "roomprice", "pricepernight", "cost", "tariff", "rate",
        "avgprice", "averageprice", "priceinr", "minprice",
    ],
    "amenities": ["hotelfacilities", "amenities", "facilities", "roomfacilities", "features"],
    "area": ["area", "locality", "landmark", "neighbourhood", "neighborhood", "address"],
    "review_count": ["sitereviewcount", "reviewcount", "numberofreviews", "totalreviews"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lon", "lng", "long"],
    "day": ["day", "daynumber", "dayno", "dayindex"],
    "activity": ["activity", "activities", "placetovisit", "attraction", "plan", "itinerary"],
    "duration": ["duration", "timespent", "hours", "timerequired"],
    "cost": ["cost", "estimatedcost", "budget", "expense", "price"],
    "category": ["category", "type", "theme", "interest"],
}


def dataset_path(dataset: str) -> Path | None:
    """First candidate filename that actually exists in data/cleaned/."""
    spec = DATASETS.get(dataset)
    if not spec:
        return None
    candidates = spec["file"]
    if isinstance(candidates, str):
        candidates = [candidates]
    for candidate in candidates:
        path = config.DATA_DIR / candidate
        if path.exists():
            return path
    
    if config.DATA_DIR.exists():
        for path in sorted(config.DATA_DIR.glob("*.csv")):
            if norm_header(dataset)[:4] in norm_header(path.stem):
                return path
    return None


def resolve(dataset: str, logical: str, headers: list[str], strict: bool = False) -> str | None:
    """Logical column name -> real CSV header, or None if unresolvable.

    Order: exact mapping -> normalised mapping -> synonym table -> (loose
    containment, unless strict).

    `strict=True` disables the loose pass. Auto-detection uses it, because
    loose containment matches almost anything and makes scoring meaningless.
    """
    spec = DATASETS.get(dataset)
    if not spec:
        return None

    mapped = spec["columns"].get(logical)
    if mapped and mapped in headers:
        return mapped

    normalised = {norm_header(h): h for h in headers}

    if mapped and norm_header(mapped) in normalised:
        return normalised[norm_header(mapped)]

    for candidate in SYNONYMS.get(logical, []):
        if candidate in normalised:
            return normalised[candidate]

    if strict:
        return None

    
    for candidate in SYNONYMS.get(logical, [logical]):
        for norm, real in normalised.items():
            if candidate and candidate in norm:
                return real
    return None


def resolve_all(dataset: str, headers: list[str]) -> dict[str, str | None]:
    spec = DATASETS.get(dataset, {})
    return {logical: resolve(dataset, logical, headers) for logical in spec.get("columns", {})}
