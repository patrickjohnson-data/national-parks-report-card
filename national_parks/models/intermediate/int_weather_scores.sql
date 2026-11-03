-- models/intermediate/int_weather_scores.sql
with scored as (
    select park_code
        ,month_number
        ,month_name
        ,avg_max
        ,avg_min
        ,avg_precip
        ,case
            when avg_max between 60 and 80 then 50
            when avg_max between 50 and 90 then 30
            else 10
         end as high_points
        ,case
            when avg_min between 40 and 60 then 20
            when avg_min between 32 and 70 then 10
            else 0
         end as low_points
        ,case
            when avg_precip < 0.05 then 30
            when avg_precip < 0.15 then 15
            else 0
         end as rain_points
    from {{ ref('int_park_weather_monthly') }}
)

select *
    ,high_points + low_points + rain_points as weather_score
    ,case
        when high_points + low_points + rain_points >= 90 then 'A'
        when high_points + low_points + rain_points >= 75 then 'B'
        when high_points + low_points + rain_points >= 60 then 'C'
        else 'D'
     end as weather_grade
from scored