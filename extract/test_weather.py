# extract/test_weather.py
"""Quick manual check that the Open-Meteo historical API is up and returns data.

Asks for one week of weather at Zion and prints the raw response, using the
same settings as extract_weather.py. It isn't part of the pipeline or run by
dbt; run it by hand if the weather download starts failing.

Usage:
    python extract/test_weather.py
"""
# Installed from requirements.txt; makes the web request
import requests

url = "https://archive-api.open-meteo.com/v1/archive"

# The settings sent to the API, for Zion National Park.
# requests adds them to the end of the URL, e.g. ...archive?latitude=37.3&...
params = {
    "latitude": 37.30,
    "longitude": -113.03,
    "start_date": "2026-10-01",
    "end_date": "2026-10-07",
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
    "temperature_unit": "fahrenheit",
    "precipitation_unit": "inch",
    "timezone": "auto",
}

# Send the request; give up if there's no answer in 30 seconds
response = requests.get(url, params=params, timeout=30)
# Stop with an error message if the request failed (anything other than success)
response.raise_for_status()
# Turn the JSON text into Python lists and dictionaries
data = response.json()

print(data)
