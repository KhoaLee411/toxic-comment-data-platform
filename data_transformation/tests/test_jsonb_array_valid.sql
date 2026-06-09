/*
  test_jsonb_array_valid.sql
  --------------------------
  Singular dbt test: returns rows that FAIL array validation.
  A passing test returns 0 rows.

  Validates that:
    1. input_ids is a JSONB array with at least 1 element
    2. attention_mask is a JSONB array with at least 1 element

  Note: This test runs on the *output* model (production.table_clean),
  where columns are already cast to JSONB. We use jsonb_typeof() and
  jsonb_array_length() directly — no string manipulation needed.
*/

SELECT *
FROM {{ ref('transform_table_clean') }}
WHERE
  -- input_ids must be a non-empty JSONB array
  jsonb_typeof(input_ids) IS DISTINCT FROM 'array'
  OR jsonb_array_length(input_ids) < 1
  -- attention_mask must be a non-empty JSONB array
  OR jsonb_typeof(attention_mask) IS DISTINCT FROM 'array'
  OR jsonb_array_length(attention_mask) < 1
