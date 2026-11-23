-- models/intermediate/int_park_visits_monthly.sql
-- Average visits per park per calendar month across 2020-2025.
-- avg() skips the 2020 closure months that staging sets to null.
select v.park_code
,v.visit_month as month_number
,monthname(make_date(v.visit_year, v.visit_month, 1)) as month_name
,round(avg(recreation_visits)) as avg_visits
from {{ ref('stg_nps_visits') }} v
-- Keeps only the 63 parks in the parks seed
inner join {{ ref('parks') }} p 
    on v.park_code = p.park_code
group by  v.park_code
,visit_month 
,monthname(make_date(v.visit_year, v.visit_month, 1)) 

