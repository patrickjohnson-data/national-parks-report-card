-- models/intermediate/int_park_weather_monthly.sql
select park_code
    ,month(weather_date) as month_number
    ,monthname(weather_date) as month_name
    ,round(avg(temp_max_f), 1) as avg_max
    ,round(avg(temp_min_f), 1) as avg_min
    ,round(avg(precipitation_in), 2) as avg_precip
from {{ ref('stg_weather') }}
group by park_code
    ,month(weather_date)
    ,monthname(weather_date)