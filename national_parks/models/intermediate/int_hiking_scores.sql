-- models/intermediate/int_hiking_scores.sql
with trail_totals as (
    select park_code
        ,count(distinct trail_name) as trail_count
        ,round(sum(length_miles), 1) as trail_miles
    from {{ ref('stg_trails') }}
    group by park_code
),

compared as (
    select *
        ,max(trail_miles) over () as top_trail_miles
        ,round(trail_miles / max(trail_miles) over () * 100, 1) as trail_pct
    from trail_totals
),

points as (
    select *
        ,case
            when trail_pct >= 75 then 100
            when trail_pct >= 50 then 80
            when trail_pct >= 25 then 60
            else 40
         end as hiking_score
    from compared
)

select *
    ,case
        when hiking_score >= 90 then 'A'
        when hiking_score >= 75 then 'B'
        when hiking_score >= 60 then 'C'
        else 'D'
     end as hiking_grade
from points