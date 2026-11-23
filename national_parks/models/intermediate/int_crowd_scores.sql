-- models/intermediate/int_crowd_scores.sql
-- Crowd score per park-month, comparing each month with that park's busiest month.
with scored as (
    select park_code
        ,month_number
        ,month_name
        ,avg_visits
        ,max(avg_visits) over (partition by park_code) as peak_avg_visits
        -- Percent of the park's peak month
        ,round(avg_visits / max(avg_visits) over (partition by park_code) * 100, 1) as crowd_pct
    from {{ ref('int_park_visits_monthly') }}
),

points as (
    select *
        -- Under 5% of peak usually means most of the park is closed or hard to reach
        ,crowd_pct < 5 as is_limited_access
        ,case
            when crowd_pct < 5 then 0
            when crowd_pct < 30 then 100
            when crowd_pct < 60 then 80
            when crowd_pct < 80 then 60
            else 40
         end as crowd_score
    from scored
)

select *
    ,{{ score_to_grade('crowd_score') }} as crowd_grade
from points