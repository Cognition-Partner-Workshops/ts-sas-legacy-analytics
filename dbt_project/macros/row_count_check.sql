{#
  row_count_check — Replaces SAS %nobs macro.
  Returns the row count of a relation. Optionally logs a warning
  when the count falls below a caller-supplied threshold.

  Usage:
    {% set cnt = row_count_check(ref('my_model')) %}
    {% set cnt = row_count_check(source('oracle_dw','cust_accounts'), min_threshold=1000) %}
#}

{% macro row_count_check(relation, min_threshold=none) %}

  {%- call statement('row_count', fetch_result=True) -%}
    select count(*) as row_count from {{ relation }}
  {%- endcall -%}

  {%- set row_count = load_result('row_count')['data'][0][0] | int -%}

  {%- if min_threshold is not none and row_count < min_threshold -%}
    {{ log("WARNING: " ~ relation ~ " has " ~ row_count ~ " rows, below threshold of " ~ min_threshold, info=True) }}
  {%- endif -%}

  {{ return(row_count) }}

{% endmacro %}
