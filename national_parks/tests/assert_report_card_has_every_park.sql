-- tests/assert_report_card_has_every_park.sql
-- Fails if a park in the parks seed is missing from the report card.
select p.park_code
from {{ ref('parks') }} p
left join {{ ref('fct_park_report_card') }} r
    on p.park_code = r.park_code
where r.park_code is null