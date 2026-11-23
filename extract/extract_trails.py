# extract/extract_trails.py
"""Download trails for every park and build the trails dbt seed.

For each park in seeds/parks.csv, this asks the official NPS Public Trails
service for all of the park's trail segments, including their shapes, and saves
them as data/raw/trails/<PARK_CODE>.json. It then measures each segment, adds
up the miles per trail name, and writes national_parks/seeds/trails.csv.

The seed is committed to the repo, so this only needs to run when you want to
refresh the trails. Parks that already have a JSON file are skipped; delete the
files in data/raw/trails to download everything again.

Usage:
    python extract/extract_trails.py
"""
# Built-in Python modules
import csv            # read the parks CSV and write the trails seed
import json           # save and load the downloaded trail data
import math           # sin, cos, etc. for measuring distances
import time           # pause between requests
from collections import defaultdict  # a dictionary that starts missing keys at 0
from pathlib import Path  # build file paths that work on Windows and Mac

# Installed from requirements.txt; makes the web requests
import requests

# Paths are relative to this script, so it works from any folder.
# __file__ is this script's own path; .parent is the folder it's in.
# The / operator joins folder and file names into a full path.
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
PARKS_FILE = REPO_ROOT / "national_parks" / "seeds" / "parks.csv"
SEED_FILE = REPO_ROOT / "national_parks" / "seeds" / "trails.csv"
OUTPUT_DIR = REPO_ROOT / "data" / "raw" / "trails"

# Official NPS Public Trails dataset (no API key needed).
# Two strings side by side inside () are joined into one long string.
TRAILS_URL = (
    "https://mapservices.nps.gov/arcgis/rest/services/"
    "NationalDatasets/NPS_Public_Trails_Geographic/FeatureServer/0/query"
)
PAGE_SIZE = 2000  # the service's maximum per request
MAX_ATTEMPTS = 3  # retries per page, 30 seconds apart
EARTH_RADIUS_MILES = 3958.8  # used to turn lat/lon points into miles


def fetch_page(park_code, offset):
    """Return one page of trail segments for a park, starting at `offset`.

    Retries up to MAX_ATTEMPTS times if the service returns an error status.
    """
    # The settings sent to the service; requests adds them to the end of the URL
    params = {
        "where": f"UNITCODE = '{park_code}'",  # only this park's trails, like a SQL where
        "outFields": "UNITCODE,TRLNAME,TRLSTATUS",  # columns to return
        "returnGeometry": "true",  # include each trail's shape, needed to measure it
        "outSR": "4326",  # plain latitude/longitude
        "orderByFields": "OBJECTID",  # a stable order so pages don't overlap
        "resultOffset": offset,  # how many rows to skip, like SQL offset
        "resultRecordCount": PAGE_SIZE,  # rows per page, like SQL limit
        "f": "json",
    }
    # range(1, MAX_ATTEMPTS + 1) counts 1, 2, 3
    for attempt in range(1, MAX_ATTEMPTS + 1):
        # Send the request; give up on it if there's no answer in 120 seconds
        response = requests.get(TRAILS_URL, params=params, timeout=120)
        # 200 means success: turn the JSON text into Python lists and dictionaries
        if response.status_code == 200:
            return response.json()
        print(f"  attempt {attempt} failed ({response.status_code}), waiting 30 seconds...")
        time.sleep(30)
    # Every attempt failed: stop the script with an error message for that status
    response.raise_for_status()


def fetch_trails(park_code):
    """Return every trail segment for a park, reading page by page.

    The service returns at most PAGE_SIZE segments per request and sets
    exceededTransferLimit when there are more, so keep asking for the next page
    until that flag is gone.
    """
    features = []  # "features" is the service's word for rows; here, trail segments
    offset = 0
    # Loop until "break" below
    while True:
        page = fetch_page(park_code, offset)
        # The service can return status 200 with an error in the body
        if "error" in page:
            raise RuntimeError(f"NPS service error for {park_code}: {page['error']}")
        # Add this page's segments to the list. .get(key, []) returns an empty
        # list instead of failing if the key is missing.
        features.extend(page.get("features", []))
        # No more pages: leave the loop
        if not page.get("exceededTransferLimit"):
            break
        # Otherwise skip ahead one page and ask again
        offset += PAGE_SIZE
        time.sleep(1)
    return features


def haversine_miles(lat1, lon1, lat2, lon2):
    """Return the distance in miles between two lat/lon points on the globe.

    Uses the haversine formula, which treats the earth as a sphere. That's
    accurate enough for adding up short trail segments.
    """
    # The math functions expect radians, not degrees, so convert all four values
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def feature_length_miles(feature):
    """Return a trail segment's length in miles by adding up the gaps between its points.

    A segment can have several parts ("paths"), each a list of [lon, lat] points.
    A segment with no shape comes back as 0 miles; stg_trails drops those.
    """
    total = 0.0
    for path in feature.get("geometry", {}).get("paths", []):
        # zip(path, path[1:]) pairs each point with the next one:
        # (point 1, point 2), (point 2, point 3), ... so we measure each gap once
        for (lon1, lat1), (lon2, lat2) in zip(path, path[1:]):
            total += haversine_miles(lat1, lon1, lat2, lon2)
    return total


def write_seed(parks):
    """Build seeds/trails.csv from the saved JSON files: one row per park and trail name."""
    rows = []
    for park in parks:
        code = park["park_code"]
        # Load the segments saved for this park
        with open(OUTPUT_DIR / f"{code}.json", encoding="utf-8") as f:
            features = json.load(f)

        # Trails are split into segments, so add up the miles per trail name.
        # This works like a SQL "sum(miles) group by trail_name". defaultdict(float)
        # starts each new name at 0.0, so += works the first time a name appears.
        miles_by_name = defaultdict(float)
        for feature in features:
            # Use "Unnamed" when the name is missing, and trim spaces
            name = (feature["attributes"].get("TRLNAME") or "Unnamed").strip()
            miles_by_name[name] += feature_length_miles(feature)

        # One output row per trail name, in alphabetical order
        for name in sorted(miles_by_name):
            rows.append({
                "park_code": code,
                "trail_name": name,
                "length_miles": round(miles_by_name[name], 2),
            })

    # Write all parks' rows to the seed CSV, with a header row first
    with open(SEED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["park_code", "trail_name", "length_miles"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} distinct trails to {SEED_FILE.name}")


def main():
    """Download trails for each park that doesn't have a file yet, then rebuild the seed."""
    # Create data/raw/trails if it doesn't exist yet (no error if it does)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # "with open(...) as f" opens the file and closes it automatically afterwards.
    # DictReader turns each CSV row into a dictionary keyed by column name,
    # e.g. {"park_code": "ZION", "park_name": "Zion", ...}
    with open(PARKS_FILE, newline="") as f:
        parks = list(csv.DictReader(f))

    for park in parks:
        code = park["park_code"]
        # f"..." strings fill in the values in {}, e.g. ZION.json
        output_file = OUTPUT_DIR / f"{code}.json"

        # Skip parks already downloaded
        if output_file.exists():
            print(f"Skipping {code}, already saved")
            continue

        print(f"Fetching trails for {code}...")
        features = fetch_trails(code)

        # Save the raw segments, so the seed can be rebuilt without downloading again
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(features, f)

        print(f"  saved {len(features)} trail segments to {output_file.name}")
        # Short pause between parks to go easy on the NPS service
        time.sleep(2)

    write_seed(parks)
    print("Done.")


# Only run main() when this file is run directly (python extract_trails.py),
# not when another script imports it
if __name__ == "__main__":
    main()
