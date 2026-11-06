-- models/staging/stg_trails.sql
select
    trim(park_code) as park_code
    ,trim(trail_name) as trail_name
    ,length_miles
from {{ ref('trails') }}