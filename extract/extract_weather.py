# extract/extract_weather.py
import csv
import json
import sys
import time
from pathlib import Path

import requests

# Paths are relative to this script, so it works from any folder
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
PARKS_FILE = REPO_ROOT / "national_parks" / "seeds" / "parks.csv"
OUTPUT_DIR = REPO_ROOT / "data" / "raw" / "weather"

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2020-01-01"
END_DATE = "2025-12-31"
MAX_ATTEMPTS = 5
WAIT_SECONDS = 60


def fetch_weather(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": "auto",
    }
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = requests.get(WEATHER_URL, params=params, timeout=60)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 429:
            print(f"  rate limited (attempt {attempt}), waiting {WAIT_SECONDS} seconds...")
            time.sleep(WAIT_SECONDS)
            continue
        response.raise_for_status()
    response.raise_for_status()


def main():
    # Run with --refresh to download every park again
    refresh = "--refresh" in sys.argv
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(PARKS_FILE, newline="", encoding="utf-8") as f:
        parks = list(csv.DictReader(f))

    for park in parks:
        code = park["park_code"]
        output_file = OUTPUT_DIR / f"{code}.json"

        if output_file.exists() and not refresh:
            print(f"Skipping {code}, already saved")
            continue

        print(f"Fetching weather for {park['park_name']} ({code})...")
        data = fetch_weather(park["latitude"], park["longitude"])

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        time.sleep(3)

    print("Done.")


if __name__ == "__main__":
    main()