-- models/intermediate/int_hiking_scores.sql
-- Hiking score per park, ranked by total trail miles. The same score applies to every month.
with trail_totals as (
    select park_code
        ,count(distinct trail_name) as trail_count
        ,round(sum(length_miles), 1) as trail_miles
    from {{ ref('stg_trails') }}
    group by park_code
),

-- Ranking spreads parks evenly from 40 (fewest miles) to 100 (most)
ranked as (
    select *
        ,round(percent_rank() over (order by trail_miles) * 100, 1) as trail_rank_pct
        ,round(40 + 60 * percent_rank() over (order by trail_miles)) as hiking_score
    from trail_totals
)

select *
    ,{{ score_to_grade('hiking_score') }} as hiking_grade
from ranked