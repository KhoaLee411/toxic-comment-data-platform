{{ config(
    materialized='table',
    alias='table_clean',
    post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_table_clean_labels ON {{ this }} (labels)",
      "ANALYZE {{ this }}"
    ]
) }}

/*
  transform_table_clean
  ---------------------
  Reads from staging.text_comment_1 (PostgreSQL native array columns)
  and converts them to JSONB arrays for downstream ML consumption.

  Source format  : input_ids = {101, 2023, 1010, ...}  (PostgreSQL integer array)
  Output format  : input_ids = [101, 2023, 1010, ...]  (JSONB array)
*/

WITH src AS (
  SELECT
    labels,
    input_ids,
    attention_mask
  FROM {{ source('staging_source', 'text_comment_1') }}
  -- Drop rows with NULL required fields before any casting
  WHERE
    labels IS NOT NULL
    AND input_ids IS NOT NULL
    AND attention_mask IS NOT NULL
    -- Ensure label is valid (binary classification)
    AND labels IN (0, 1)
),

converted AS (
  SELECT
    labels::integer                                    AS labels,
    -- Cast PostgreSQL native integer[] directly to JSONB
    -- array_to_json() produces valid JSON arrays from native PG arrays
    array_to_json(input_ids)::jsonb                    AS input_ids,
    array_to_json(attention_mask)::jsonb               AS attention_mask,
    now()                                              AS dbt_loaded_at
  FROM src
  -- Guard: drop rows where array is empty
  WHERE
    array_length(input_ids, 1) >= 1
    AND array_length(attention_mask, 1) >= 1
)

SELECT
  labels,
  input_ids,
  attention_mask,
  dbt_loaded_at
FROM converted
