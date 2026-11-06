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
        ,coalesce(h.trail_count, 0) as trail_count
        ,coalesce(h.trail_miles, 0) as trail_miles
        ,coalesce(h.hiking_score, 40) as hiking_score
        ,coalesce(h.hiking_grade, 'D') as hiking_grade
        ,round(
            w.weather_score * 0.4
            + c.crowd_score * 0.4
            + coalesce(h.hiking_score, 40) * 0.2
         ) as overall_score
    from {{ ref('int_weather_scores') }} w
    inner join {{ ref('int_crowd_scores') }} c
        on w.park_code = c.park_code
        and w.month_number = c.month_number
    left join {{ ref('int_hiking_scores') }} h
        on w.park_code = h.park_code
    inner join {{ ref('parks') }} p
        on w.park_code = p.park_code
),

ranked as (
    select *
        ,percent_rank() over (order by overall_score desc) as score_rank
    from combined
)

select *
    ,case
        when score_rank <= 0.10 then 'A'
        when score_rank <= 0.40 then 'B'
        when score_rank <= 0.80 then 'C'
        else 'D'
     end as overall_grade
from ranked