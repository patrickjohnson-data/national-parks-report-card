select park_code
    ,monthname(weather_date) as park_month
    ,avg(temp_max_f) as avg_max
    ,avg(temp_min_f) as avg_min
    ,avg(precipitation_in) as avg_precip
    from {{ ref('stg_weather') }}
group by park_code
    ,monthname(weather_date)