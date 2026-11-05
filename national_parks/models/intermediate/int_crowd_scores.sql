with scored as (
    select park_code
        ,month_number
        ,month_name
        ,avg_visits
        ,max(avg_visits) over (partition by park_code) as peak_avg_visits
        ,round(avg_visits / max(avg_visits) over (partition by park_code) * 100, 1) as crowd_pct
    from {{ ref('int_park_visits_monthly') }}
),

points as (
    select *
        ,case
            when crowd_pct < 30 then 100
            when crowd_pct < 60 then 80
            when crowd_pct < 80 then 60
            else 40
         end as crowd_score
    from scored
)

select *
    ,case
        when crowd_score >= 90 then 'A'
        when crowd_score >= 75 then 'B'
        when crowd_score >= 60 then 'C'
        else 'D'
     end as crowd_grade
from points