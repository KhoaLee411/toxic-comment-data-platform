"""
data_validation/validators.py
------------------------------
Expectation-building logic, separated from I/O concerns.
Each function takes a validator and applies the appropriate expectations
based on data source format (CSV/Kafka vs PostgreSQL).

No GX context is touched here — callers own the lifecycle.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# CSV / Kafka: JSON array format  e.g.  [101, 2023, 1010]
JSON_ARRAY_OF_INTS = r"^\s*\[\s*\d+(?:\s*,\s*\d+)*\s*\]\s*$"
JSON_MASK_PATTERN  = r"^\s*\[\s*[01](?:\s*,\s*[01])*\s*\]\s*$"

# PostgreSQL native array format  e.g.  {101,2023,1010}
PG_ARRAY_OF_INTS   = r"^\s*\{\s*\d+(?:\s*,\s*\d+)*\s*\}\s*$"
PG_MASK_PATTERN    = r"^\s*\{\s*[01](?:\s*,\s*[01])*\s*\}\s*$"

# UUID v4 (strict): version digit must be 4, variant bits 8-b
UUID_V4_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_expectations(validator, *, pg_format: bool) -> None:
    """
    Apply the full expectation suite to *validator*.

    Parameters
    ----------
    validator  : GX Validator
    pg_format  : True  → PostgreSQL native array syntax  {101, 2023}
                 False → JSON array syntax               [101, 2023]

    The 'id' column is detected automatically from the validator's columns.
    """
    _expect_required_columns(validator)
    _expect_label_range(validator)

    if "id" in validator.columns():
        _expect_id_column(validator)
        _expect_array_columns(validator, json_format=True)   # CSV always has JSON arrays
    else:
        _expect_array_columns(validator, json_format=not pg_format)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _expect_required_columns(validator) -> None:
    for col in ("labels", "input_ids", "attention_mask"):
        validator.expect_column_values_to_not_be_null(col)


def _expect_label_range(validator) -> None:
    validator.expect_column_values_to_be_in_set("labels", [0, 1])


def _expect_id_column(validator) -> None:
    validator.expect_column_values_to_not_be_null("id")
    validator.expect_column_values_to_be_unique("id")
    validator.expect_column_values_to_match_regex("id", UUID_V4_REGEX, mostly=1.0)


def _expect_array_columns(validator, *, json_format: bool) -> None:
    if json_format:
        validator.expect_column_values_to_match_regex("input_ids",      JSON_ARRAY_OF_INTS)
        validator.expect_column_values_to_match_regex("attention_mask", JSON_MASK_PATTERN)
    else:
        validator.expect_column_values_to_match_regex("input_ids",      PG_ARRAY_OF_INTS)
        validator.expect_column_values_to_match_regex("attention_mask", PG_MASK_PATTERN)
