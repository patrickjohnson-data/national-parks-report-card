import requests

url = "https://archive-api.open-meteo.com/v1/archive"

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

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
data = response.json()

print(data)