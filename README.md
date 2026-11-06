# National Parks Report Card

I wanted to know the best month to visit each national park, so I built a pipeline that grades all 63 parks for every month of the year on weather, crowds and hiking.

Python pulls the raw data from public sources, DuckDB stores it, and dbt does the cleaning, testing and modeling. Nothing needs an API key, so you can clone it and run it yourself.

Built with Python, dbt Core, DuckDB and SQL.

## Pipeline

```mermaid
flowchart LR
    A[Open-Meteo API] -->|extract_weather.py| B[(raw JSON)]
    C[NPS trails service] -->|extract_trails.py| D[trails seed]
    E[NPS visitor stats] --> F[nps_visits seed]
    G[parks seed] --> H

    B --> H[staging]
    D --> H
    F --> H
    H --> I[intermediate]
    I --> J[fct_park_report_card]
```

The dbt project follows the usual staging, intermediate and marts layout.

- **Staging** cleans each source. `stg_weather` unnests the Open-Meteo JSON into one row per park per day, `stg_nps_visits` strips the commas out of the NPS numbers, and `stg_trails` trims the trail names.
- **Intermediate** averages everything by park and calendar month, then turns the averages into scores out of 100 (`int_weather_scores`, `int_crowd_scores`, `int_hiking_scores`).
- **Marts** has one table, `fct_park_report_card`, with one row per park per month and an overall grade.

## Data sources

- **Weather:** daily highs, lows and rain for 2020 to 2025 from the [Open-Meteo historical API](https://open-meteo.com/).
- **Crowds:** monthly recreation visits for 2020 to 2025 from [NPS Visitor Use Statistics](https://irma.nps.gov/Stats/).
- **Trails:** trail names and lengths from the official [NPS Public Trails dataset](https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Trails_Geographic/FeatureServer/0).

Weather gets downloaded when you run the project. The visitor counts and trails barely change, so I committed them as dbt seeds. That way the project doesn't depend on those sources being up when someone runs it.

## Scoring

Weather, crowds and hiking each get a score out of 100. The overall score weights them 40% weather, 40% crowds and 20% hiking. I weighted hiking lowest because it's the roughest of the three and it doesn't change from month to month.

Weather, crowds and hiking each get their own grade on a fixed scale: A is 90 and up, B is 75 to 89, C is 60 to 74, and D is anything below 60. The overall grade is curved instead, because a park's quietest months are usually its worst-weather months, so almost no month scores high on everything. The top 10% of all park-months get an A, the next 30% a B, the next 40% a C, and the bottom 20% a D.

**Weather.** Points for the average high (50 for 60 to 80°F, 30 for 50 to 90°F, 10 otherwise), the average low (20 for 40 to 60°F, 10 for 32 to 70°F, 0 otherwise) and rain (30 for under 0.05 in a day, 15 for under 0.15, 0 otherwise).

**Crowds.** Each month is compared with that park's own busiest month, so a quiet month at a busy park can still score well. Under 40% of peak gets 100, under 60% gets 80, under 80% gets 60, and anything higher gets 40.

**Hiking.** Parks are ranked by total trail miles, and the rank becomes a score from 40 (fewest miles) to 100 (most). I first compared every park with the one that had the most miles, but Yellowstone is so far ahead that almost every other park ended up at the bottom. Ranking spreads them out evenly. Parks with no trails in the NPS data get 40.

## Running it

I've tested this on Windows with Python 3.14 and dbt Core 1.12. You'll need Python and Git installed.

Clone the repo and install the requirements:

```
git clone https://github.com/patrickjohnson-data/national-parks-report-card.git
cd national-parks-report-card
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Mac or Linux, activate the environment with `source .venv/bin/activate`. If PowerShell won't run the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

Download the weather. The first run fetches all 63 parks and takes several minutes, because the script pauses when Open-Meteo rate limits it:

```
python extract/extract_weather.py
```

Then build everything. dbt commands need to run from the `national_parks` folder:

```
cd national_parks
dbt build
```

That loads the seeds, builds the models and runs the tests. To see the best park months:

```
dbt show --inline "select park_name, month_name, overall_score, overall_grade from {{ ref('fct_park_report_card') }} order by overall_score desc" --limit 20
```

You can also open `national_parks/dev.duckdb` in DBeaver or another DuckDB client, or run `dbt docs generate` and `dbt docs serve` to browse the models and the lineage graph.

## Refreshing the data

`python extract/extract_weather.py --refresh` downloads the weather for every park again. Without `--refresh` it skips parks it already has.

For trails, delete the files in `data/raw/trails` and run `python extract/extract_trails.py`. It rebuilds `seeds/trails.csv`.

The visitor counts are a manual step, because NPS Stats doesn't have a download API. Export the "Query Builder for Public Use Statistics" report as CSV (National Parks only, Recreation Visits) and replace `seeds/nps_visits.csv`. NPS finalizes the numbers once a year, so once a year is enough.

## Tests

`dbt build` runs 30 tests. Besides the usual `not_null`, `unique` and `accepted_values` checks, there are a few custom ones: one row per park per day in the weather, one row per park per month in the report card, exactly 12 months for every park, and no park missing from the final table.

## Limitations

- Crowd numbers are for the whole park. I couldn't find free trail-level crowd data, since AllTrails and Strava don't have public APIs.
- 2020 includes COVID closures, so some 2020 months look quieter than they really were.
- Low visitor numbers don't always mean a good time to visit. Some months are quiet because a park is hard to reach, for example when snow keeps roads closed, so a high crowd score can reward an inaccessible month.
- Weather comes from one point per park, using approximate park centers. Big parks with a lot of elevation change can be much warmer or colder in other areas.
- Hiking rewards total miles, so big parks beat small parks with famous hikes, like Zion. The NPS data may also include some informal trails.
- A few parks have no trails in the NPS data, mostly the marine parks and remote Alaska parks. Sequoia and Kings Canyon are managed together, so their trails may be filed under one code.
- The grades describe a typical month based on past years. They aren't a forecast.

## What I'd add next

- A GitHub Actions schedule to refresh the weather
- Incremental weather loads instead of re-downloading every year
- Snow or elevation in the weather score
- A simple web page to browse the report card
