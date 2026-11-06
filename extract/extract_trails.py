# extract/extract_trails.py
import csv
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import requests

# Paths are relative to this script, so it works from any folder
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
PARKS_FILE = REPO_ROOT / "national_parks" / "seeds" / "parks.csv"
SEED_FILE = REPO_ROOT / "national_parks" / "seeds" / "trails.csv"
OUTPUT_DIR = REPO_ROOT / "data" / "raw" / "trails"

# Official NPS Public Trails dataset (no API key needed)
TRAILS_URL = (
    "https://mapservices.nps.gov/arcgis/rest/services/"
    "NationalDatasets/NPS_Public_Trails_Geographic/FeatureServer/0/query"
)
PAGE_SIZE = 2000  # the service's maximum per request
MAX_ATTEMPTS = 3
EARTH_RADIUS_MILES = 3958.8


def fetch_page(park_code, offset):
    params = {
        "where": f"UNITCODE = '{park_code}'",
        "outFields": "UNITCODE,TRLNAME,TRLSTATUS",
        "returnGeometry": "true",
        "outSR": "4326",  # plain latitude/longitude
        "orderByFields": "OBJECTID",
        "resultOffset": offset,
        "resultRecordCount": PAGE_SIZE,
        "f": "json",
    }
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = requests.get(TRAILS_URL, params=params, timeout=120)
        if response.status_code == 200:
            return response.json()
        print(f"  attempt {attempt} failed ({response.status_code}), waiting 30 seconds...")
        time.sleep(30)
    response.raise_for_status()


def fetch_trails(park_code):
    # Keep asking for the next page until the service says there's no more
    features = []
    offset = 0
    while True:
        page = fetch_page(park_code, offset)
        if "error" in page:
            raise RuntimeError(f"NPS service error for {park_code}: {page['error']}")
        features.extend(page.get("features", []))
        if not page.get("exceededTransferLimit"):
            break
        offset += PAGE_SIZE
        time.sleep(1)
    return features


def haversine_miles(lat1, lon1, lat2, lon2):
    # Distance between two points on the globe, in miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def feature_length_miles(feature):
    # A trail segment can have several parts ("paths"), each a list of [lon, lat] points
    total = 0.0
    for path in feature.get("geometry", {}).get("paths", []):
        for (lon1, lat1), (lon2, lat2) in zip(path, path[1:]):
            total += haversine_miles(lat1, lon1, lat2, lon2)
    return total


def write_seed(parks):
    rows = []
    for park in parks:
        code = park["park_code"]
        with open(OUTPUT_DIR / f"{code}.json", encoding="utf-8") as f:
            features = json.load(f)

        # Trails are split into segments, so add up the miles per trail name
        miles_by_name = defaultdict(float)
        for feature in features:
            name = (feature["attributes"].get("TRLNAME") or "Unnamed").strip()
            miles_by_name[name] += feature_length_miles(feature)

        for name in sorted(miles_by_name):
            rows.append({
                "park_code": code,
                "trail_name": name,
                "length_miles": round(miles_by_name[name], 2),
            })

    with open(SEED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["park_code", "trail_name", "length_miles"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} distinct trails to {SEED_FILE.name}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(PARKS_FILE, newline="") as f:
        parks = list(csv.DictReader(f))

    for park in parks:
        code = park["park_code"]
        output_file = OUTPUT_DIR / f"{code}.json"

        if output_file.exists():
            print(f"Skipping {code}, already saved")
            continue

        print(f"Fetching trails for {code}...")
        features = fetch_trails(code)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(features, f)

        print(f"  saved {len(features)} trail segments to {output_file.name}")
        time.sleep(2)

    write_seed(parks)
    print("Done.")


if __name__ == "__main__":
    main()