"""
data_validation/validate.py
---------------------------
Reusable validation logic for the Toxic Comment Data Platform.

Wraps Great Expectations to validate two data sources:
  1. PostgreSQL staging table  (staging.text_comment_1)
  2. Kafka CSV filesystem dump (../data/kafka/streaming.csv)

Usage (from data_validation/ directory):
    python validate.py --source postgres
    python validate.py --source kafka
    python validate.py --source all     # default

Environment variables (required for postgres):
    PG_USER, PG_PASSWORD, PG_HOST, PG_PORT, PG_DB
"""

from __future__ import annotations

import argparse
import os
import sys

import great_expectations as gx
from great_expectations.data_context import FileDataContext

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GX_ROOT = os.path.join(os.path.dirname(__file__), "gx")

# Datasource names (must match great_expectations.yml)
PG_DATASOURCE = "postgres_staging"
PG_ASSET = "text_comment_1"

KAFKA_DATASOURCE = "kafka_filesystem"
KAFKA_ASSET = "streaming_csv"

# Expectation suite (shared between both sources)
SUITE_NAME = "toxic_comment_suite"

# Regex patterns for array-format columns
# CSV / Kafka: JSON array  e.g.  [101, 2023, 1010]
JSON_ARRAY_OF_INTS = r"^\s*\[\s*\d+(?:\s*,\s*\d+)*\s*\]\s*$"
JSON_MASK_PATTERN  = r"^\s*\[\s*[01](?:\s*,\s*[01])*\s*\]\s*$"

# PostgreSQL native array  e.g.  {101,2023,1010}
PG_ARRAY_OF_INTS   = r"^\s*\{\s*\d+(?:\s*,\s*\d+)*\s*\}\s*$"
PG_MASK_PATTERN    = r"^\s*\{\s*[01](?:\s*,\s*[01])*\s*\}\s*$"

# UUID v4 pattern (strict)
UUID_V4_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_context() -> FileDataContext:
    """Load the GX FileDataContext from the gx/ directory."""
    return FileDataContext.create(project_root_dir=GX_ROOT)


def build_expectations(validator, *, has_id_col: bool, pg_format: bool) -> None:
    """
    Apply all expectations to a validator.

    Parameters
    ----------
    validator    : GX Validator object
    has_id_col   : Whether the 'id' column exists in this dataset
    pg_format    : If True, use PostgreSQL native array syntax ({...});
                   if False, use JSON array syntax ([...]).
    """
    # --- Required columns: not null -----------------------------------------
    validator.expect_column_values_to_not_be_null("labels")
    validator.expect_column_values_to_not_be_null("input_ids")
    validator.expect_column_values_to_not_be_null("attention_mask")

    # --- Label range: binary classification ----------------------------------
    validator.expect_column_values_to_be_in_set("labels", [0, 1])

    # --- ID column (only present in CSV/Kafka data) --------------------------
    if has_id_col:
        validator.expect_column_values_to_not_be_null("id")
        validator.expect_column_values_to_be_unique("id")
        validator.expect_column_values_to_match_regex("id", UUID_V4_REGEX, mostly=1.0)

    # --- Array-format validation (format depends on source) ------------------
    if pg_format:
        validator.expect_column_values_to_match_regex("input_ids", PG_ARRAY_OF_INTS)
        validator.expect_column_values_to_match_regex("attention_mask", PG_MASK_PATTERN)
    else:
        validator.expect_column_values_to_match_regex("input_ids", JSON_ARRAY_OF_INTS)
        validator.expect_column_values_to_match_regex("attention_mask", JSON_MASK_PATTERN)


def run_checkpoint(
    context: FileDataContext,
    checkpoint_name: str,
    validator,
) -> bool:
    """
    Create-or-update a checkpoint and run it.

    Returns True if validation passed, False otherwise.
    """
    checkpoint = context.add_or_update_checkpoint(
        name=checkpoint_name,
        validator=validator,
    )
    result = checkpoint.run()
    context.view_validation_result(result)
    return result.success


# ---------------------------------------------------------------------------
# Validation flows
# ---------------------------------------------------------------------------

def validate_postgres(context: FileDataContext) -> bool:
    """Validate data in the PostgreSQL staging table."""
    print("\n=== Validating PostgreSQL staging source ===")

    datasource = context.get_datasource(PG_DATASOURCE)
    batch_request = datasource.get_asset(PG_ASSET).build_batch_request()

    context.add_or_update_expectation_suite(SUITE_NAME)
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=SUITE_NAME,
    )

    print("Sample rows:")
    print(validator.head())

    has_id = "id" in validator.columns()
    build_expectations(validator, has_id_col=has_id, pg_format=True)

    # Only save expectations after first run to avoid overwriting with subset
    validator.save_expectation_suite(discard_failed_expectations=False)

    return run_checkpoint(context, "postgres_staging_checkpoint", validator)


def validate_kafka(context: FileDataContext) -> bool:
    """Validate data from the Kafka CSV filesystem dump."""
    print("\n=== Validating Kafka filesystem source ===")

    datasource = context.get_datasource(KAFKA_DATASOURCE)
    asset = datasource.get_asset(KAFKA_ASSET)
    batch_request = asset.build_batch_request()

    # Preview loaded batches
    batches = asset.get_batch_list_from_batch_request(batch_request)
    print(f"Found {len(batches)} batch(es):")
    for b in batches:
        print(f"  {b.batch_spec}")

    context.add_or_update_expectation_suite(SUITE_NAME)
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=SUITE_NAME,
    )

    print("Sample rows:")
    print(validator.head())

    has_id = "id" in validator.columns()
    build_expectations(validator, has_id_col=has_id, pg_format=False)

    validator.save_expectation_suite(discard_failed_expectations=False)

    return run_checkpoint(context, "kafka_streaming_checkpoint", validator)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Great Expectations data validation for the Toxic Comment platform."
    )
    parser.add_argument(
        "--source",
        choices=["postgres", "kafka", "all"],
        default="all",
        help="Which data source to validate (default: all)",
    )
    args = parser.parse_args()

    context = get_context()
    results: list[bool] = []

    if args.source in ("postgres", "all"):
        results.append(validate_postgres(context))

    if args.source in ("kafka", "all"):
        results.append(validate_kafka(context))

    all_passed = all(results)
    print("\n=== Validation Summary ===")
    print("PASSED" if all_passed else "FAILED — see Data Docs for details.")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
