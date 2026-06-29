{{ config(
    materialized='table',
    post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_comments_labels ON {{ this }} (labels)",
      "ANALYZE {{ this }}"
    ]
) }}

WITH batch_data AS (
  SELECT
    md5(input_ids || labels::text)::varchar(255) AS id, -- Generate deterministic ID for batch
    labels::int,
    input_ids::text,
    attention_mask::text
  FROM {{ source('staging', 'batch') }}
  WHERE labels IS NOT NULL
),

stream_data AS (
  SELECT
    id::varchar(255),
    labels::int,
    input_ids::text,
    attention_mask::text
  FROM {{ source('staging', 'streaming') }}
  WHERE labels IS NOT NULL
)

SELECT * FROM batch_data
UNION ALL
SELECT * FROM stream_data
