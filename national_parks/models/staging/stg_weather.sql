with raw as (

    select
        regexp_extract(filename, '([A-Z]{4})\.json$', 1) as park_code,
        daily
    from {{ source('raw', 'weather') }}

),

unpacked as (

    select
        park_code,
        unnest(daily.time) as weather_date,
        unnest(daily.temperature_2m_max) as temp_max_f,
        unnest(daily.temperature_2m_min) as temp_min_f,
        unnest(daily.precipitation_sum) as precipitation_in
    from raw

)

select
    park_code,
    cast(weather_date as date) as weather_date,
    temp_max_f,
    temp_min_f,
    precipitation_in
from unpacked