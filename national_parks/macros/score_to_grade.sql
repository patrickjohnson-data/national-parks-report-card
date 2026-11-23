-- macros/score_to_grade.sql
-- Turns a score out of 100 into a letter grade on the fixed scale shared by
-- the weather, crowd and hiking scores. The overall grade is curved instead.
{% macro score_to_grade(score) %}
    case
        when {{ score }} >= 90 then 'A'
        when {{ score }} >= 75 then 'B'
        when {{ score }} >= 60 then 'C'
        else 'D'
    end
{% endmacro %}
