-- models/staging/stg_nps_visits.sql
select
    trim(UnitCode) as park_code
    ,Year as visit_year
    ,Month as visit_month
    ,cast(replace(RecreationVisits, ',', '') as int) as recreation_visits
from {{ ref('nps_visits') }}