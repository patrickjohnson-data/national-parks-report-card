-- tests/assert_stg_nps_visits_one_row_per_park_month.sql
-- Fails if a park has more than one visits row for the same year and month.
select park_code, visit_year, visit_month, count(*) as row_count
from {{ ref('stg_nps_visits') }}
group by park_code, visit_year, visit_month
having count(*) > 1