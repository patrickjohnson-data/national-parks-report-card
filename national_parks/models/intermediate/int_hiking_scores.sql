-- models/intermediate/int_hiking_scores.sql
with trail_totals as (
    select park_code
        ,count(distinct trail_name) as trail_count
        ,round(sum(length_miles), 1) as trail_miles
    from {{ ref('stg_trails') }}
    group by park_code
),

ranked as (
    select *
        ,round(percent_rank() over (order by trail_miles) * 100, 1) as trail_rank_pct
        ,round(40 + 60 * percent_rank() over (order by trail_miles)) as hiking_score
    from trail_totals
)

select *
    ,{{ score_to_grade('hiking_score') }} as hiking_grade
from ranked