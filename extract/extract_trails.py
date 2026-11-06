# extract/extract_trails.py
import csv
import json
import time
from pathlib import Path

import requests

# Paths are relative to this script, so it works from any folder
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
PARKS_FILE = REPO_ROOT / "national_parks" / "seeds" / "parks.csv"
SEED_FILE = REPO_ROOT / "national_parks" / "seeds" / "trails.csv"
OUTPUT_DIR = REPO_ROOT / "data" / "raw" / "trails"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "national-parks-report-card (github.com/patrickjohnson-data)"}
RADIUS_METRES = 20000
MAX_ATTEMPTS = 3


def build_query(lat, lon):
    return f"""
[out:json][timeout:90];
way["highway"~"path|footway"]["name"](around:{RADIUS_METRES},{lat},{lon});
out tags;
"""


def fetch_trails(lat, lon):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = requests.post(
            OVERPASS_URL,
            data={"data": build_query(lat, lon)},
            headers=HEADERS,
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()
        print(f"  attempt {attempt} failed ({response.status_code}), waiting 30 seconds...")
        time.sleep(30)
    response.raise_for_status()


def write_seed(parks):
    rows = []
    for park in parks:
        code = park["park_code"]
        with open(OUTPUT_DIR / f"{code}.json", encoding="utf-8") as f:
            data = json.load(f)

        # One trail is often split into many pieces with the same name,
        # so a set keeps each name only once
        names = {element["tags"]["name"].strip() for element in data["elements"]}
        for name in sorted(names):
            rows.append({"park_code": code, "trail_name": name})

    with open(SEED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["park_code", "trail_name"])
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
        data = fetch_trails(park["latitude"], park["longitude"])

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"  saved {len(data['elements'])} trail pieces to {output_file.name}")
        time.sleep(5)

    write_seed(parks)
    print("Done.")


if __name__ == "__main__":
    main()