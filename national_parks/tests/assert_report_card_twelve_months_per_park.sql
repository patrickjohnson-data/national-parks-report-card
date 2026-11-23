-- tests/assert_report_card_twelve_months_per_park.sql
-- Fails if a park doesn't have exactly 12 months.
select park_code, count(*) as month_count
from {{ ref('fct_park_report_card') }}
group by park_code
having count(*) != 12