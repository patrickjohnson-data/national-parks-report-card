-- models/marts/fct_park_report_card.sql
{{ config(materialized='table') }}

with combined as (
    select p.park_code
        ,p.park_name
        ,p.state
        ,w.month_number
        ,w.month_name
        ,w.avg_max
        ,w.avg_min
        ,w.avg_precip
        ,w.weather_score
        ,w.weather_grade
        ,c.avg_visits
        ,c.crowd_pct
        ,c.crowd_score
        ,c.crowd_grade
        ,h.trail_count
        ,h.trail_miles
        ,h.hiking_score
        ,h.hiking_grade
        ,round(
            w.weather_score * 0.4
            + c.crowd_score * 0.4
            + h.hiking_score * 0.2
         ) as overall_score
    from {{ ref('int_weather_scores') }} w
    inner join {{ ref('int_crowd_scores') }} c
        on w.park_code = c.park_code
        and w.month_number = c.month_number
    inner join {{ ref('int_hiking_scores') }} h
        on w.park_code = h.park_code
    inner join {{ ref('parks') }} p
        on w.park_code = p.park_code
)

select *
    ,case
        when overall_score >= 90 then 'A'
        when overall_score >= 75 then 'B'
        when overall_score >= 60 then 'C'
        else 'D'
     end as overall_grade
from combined