-- tests/assert_stg_weather_one_row_per_park_day.sql
-- Fails if a park has more than one weather row for the same day.
select park_code, weather_date, count(*) as row_count
from {{ref('stg_weather')}}
group by park_code, weather_date
having count(*) > 1