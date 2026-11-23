-- models/staging/stg_nps_visits.sql
-- One row per park per month of recreation visits from the NPS Stats export.
-- A 2020 month with 0 visits is treated as a COVID closure and set to null,
-- so it doesn't drag down that month's multi-year average.
select
    trim(UnitCode) as park_code
    ,Year as visit_year
    ,Month as visit_month
    -- NPS exports the numbers as text with commas, e.g. "12,640"
    ,case
        when Year = 2020 and cast(replace(RecreationVisits, ',', '') as int) = 0 then null
        else cast(replace(RecreationVisits, ',', '') as int)
     end as recreation_visits
from {{ ref('nps_visits') }}
