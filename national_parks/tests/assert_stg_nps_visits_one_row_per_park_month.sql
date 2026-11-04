select park_code, visit_year, visit_month, count(*) as row_count
from {{ ref('stg_nps_visits') }}
group by park_code, visit_year, visit_month
having count(*) > 1