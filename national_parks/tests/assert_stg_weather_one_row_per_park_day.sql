select park_code, weather_date, count(*) as row_count
from {{ref('stg_weather')}}
group by park_code, weather_date
having count(*) > 1