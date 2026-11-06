-- tests/assert_report_card_one_row_per_park_month.sql
select park_code, month_number, count(*) as row_count
from {{ ref('fct_park_report_card') }}
group by park_code, month_number
having count(*) > 1