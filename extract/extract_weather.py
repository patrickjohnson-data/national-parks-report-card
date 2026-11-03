import csv
import json
import time
from pathlib import Path

import requests

# Folder locations, worked out from where this script lives
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARKS_FILE = PROJECT_ROOT / "national_parks" / "seeds" / "parks.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "weather"

API_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2020-01-01"
END_DATE = "2025-12-31"


def read_parks():
    """Read parks.csv and return one dictionary per park."""
    with open(PARKS_FILE, newline="") as f:
        return list(csv.DictReader(f))


def fetch_weather(latitude, longitude):
    """Ask Open-Meteo for daily weather at one location."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": "auto",
    }
    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parks = read_parks()

    for park in parks:
        code = park["park_code"]
        print(f"Fetching weather for {park['park_name']} ({code})...")

        data = fetch_weather(park["latitude"], park["longitude"])

        output_file = OUTPUT_DIR / f"{code}.json"
        with open(output_file, "w") as f:
            json.dump(data, f)

        time.sleep(1)  # pause between calls, to be polite to the free API

    print(f"Done. Saved {len(parks)} files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()