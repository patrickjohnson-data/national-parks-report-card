# extract/extract_weather.py
"""Download daily weather for every park from the Open-Meteo historical API.

For each park in seeds/parks.csv, this asks Open-Meteo for daily highs, lows
and precipitation from 2020 to 2025 at the park's latitude and longitude, and
saves the response as data/raw/weather/<PARK_CODE>.json. dbt reads those files
in stg_weather.

Parks that already have a file are skipped, so if the script stops partway you
can run it again and it picks up where it left off.

Usage:
    python extract/extract_weather.py            # download missing parks only
    python extract/extract_weather.py --refresh  # download every park again
"""
# Built-in Python modules
import csv            # read the parks CSV
import json           # save the API response as a .json file
import sys            # read the command-line arguments (for --refresh)
import time           # pause between requests
from pathlib import Path  # build file paths that work on Windows and Mac

# Installed from requirements.txt; makes the web requests
import requests

# Paths are relative to this script, so it works from any folder.
# __file__ is this script's own path; .parent is the folder it's in.
# The / operator joins folder and file names into a full path.
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
PARKS_FILE = REPO_ROOT / "national_parks" / "seeds" / "parks.csv"
OUTPUT_DIR = REPO_ROOT / "data" / "raw" / "weather"

# Open-Meteo's free historical API (no key needed)
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2020-01-01"
END_DATE = "2025-12-31"
# The free tier limits requests per minute. When we hit the limit, wait a
# minute and try again, up to MAX_ATTEMPTS times.
MAX_ATTEMPTS = 5
WAIT_SECONDS = 60


def fetch_weather(lat, lon):
    """Return six years of daily weather for one point as parsed JSON.

    Retries after a pause when Open-Meteo says we're sending too many requests
    (HTTP 429). Any other error, or running out of attempts, raises an exception.
    """
    # The settings sent to the API. requests adds them to the end of the URL,
    # e.g. ...archive?latitude=37.3&longitude=-113.03&...
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": "auto",  # days follow the park's local time, not UTC
    }
    # range(1, MAX_ATTEMPTS + 1) counts 1, 2, 3, 4, 5
    for attempt in range(1, MAX_ATTEMPTS + 1):
        # Send the request; give up on it if there's no answer in 60 seconds
        response = requests.get(WEATHER_URL, params=params, timeout=60)
        # 200 means success: turn the JSON text into Python lists and dictionaries
        if response.status_code == 200:
            return response.json()
        # 429 means "too many requests": wait, then go back to the top of the loop
        if response.status_code == 429:
            print(f"  rate limited (attempt {attempt}), waiting {WAIT_SECONDS} seconds...")
            time.sleep(WAIT_SECONDS)
            continue
        # Any other error won't be fixed by waiting, so stop here.
        # raise_for_status() stops the script with an error message for that status.
        response.raise_for_status()
    # All attempts were rate limited
    response.raise_for_status()


def main():
    """Download weather for each park that doesn't have a file yet."""
    # sys.argv is the list of words typed after "python"; check for --refresh
    refresh = "--refresh" in sys.argv
    # Create data/raw/weather if it doesn't exist yet (no error if it does)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # "with open(...) as f" opens the file and closes it automatically afterwards.
    # DictReader turns each CSV row into a dictionary keyed by column name,
    # e.g. {"park_code": "ZION", "park_name": "Zion", "latitude": "37.30", ...}
    with open(PARKS_FILE, newline="", encoding="utf-8") as f:
        parks = list(csv.DictReader(f))

    for park in parks:
        code = park["park_code"]
        # f"..." strings fill in the values in {}, e.g. ZION.json
        output_file = OUTPUT_DIR / f"{code}.json"

        # Skip parks already downloaded, unless --refresh was given
        if output_file.exists() and not refresh:
            print(f"Skipping {code}, already saved")
            continue

        print(f"Fetching weather for {park['park_name']} ({code})...")
        data = fetch_weather(park["latitude"], park["longitude"])

        # Open the output file for writing ("w") and save the response as JSON
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Short pause between parks to stay under the rate limit
        time.sleep(3)

    print("Done.")


# Only run main() when this file is run directly (python extract_weather.py),
# not when another script imports it
if __name__ == "__main__":
    main()
