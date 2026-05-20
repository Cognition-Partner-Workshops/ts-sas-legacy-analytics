{#
  validate_params — Replaces SAS %parmv macro.
  Validates a dbt variable or parameter value at compile time.
  Raises a compilation error when a required parameter is missing
  or when the value is not in an allowed list.

  Usage:
    {{ validate_params('run_date', var('run_date'), required=True) }}
    {{ validate_params('region', var('region', 'ALL'), valid_values=['ALL','NE','SE','MW','SW','W','NW']) }}
#}

{% macro validate_params(param_name, param_value, required=false, valid_values=none) %}

  {%- if required and (param_value is none or param_value | trim == '') -%}
    {{ exceptions.raise_compiler_error(
         "Parameter '" ~ param_name ~ "' is required but was not provided."
       ) }}
  {%- endif -%}

  {%- if valid_values is not none and param_value is not none and param_value | trim != '' -%}
    {%- if param_value not in valid_values -%}
      {{ exceptions.raise_compiler_error(
           "Parameter '" ~ param_name ~ "' has invalid value '" ~ param_value
           ~ "'. Allowed values: " ~ valid_values | join(', ')
         ) }}
    {%- endif -%}
  {%- endif -%}

{% endmacro %}
