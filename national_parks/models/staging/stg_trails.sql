-- models/staging/stg_trails.sql
-- One row per trail segment from the NPS Public Trails seed.
select
    trim(park_code) as park_code
    -- A few segments have no name; keep them because they still add miles
    ,nullif(trim(trail_name), '') as trail_name
    ,length_miles
from {{ ref('trails') }}
-- Drop zero-length segments
where length_miles > 0
