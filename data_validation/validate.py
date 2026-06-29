"""
data_validation/validate.py
---------------------------
CLI entry-point for Great Expectations validation.

Validates two data sources:
  1. PostgreSQL staging table  (staging.text_comment_1)
  2. Kafka CSV filesystem dump (../data/kafka/streaming.csv)

Usage (from data_validation/ directory):
    python validate.py --source postgres
    python validate.py --source kafka
    python validate.py --source all      # default

Environment variables (required for postgres):
    PG_USER, PG_PASSWORD, PG_HOST, PG_PORT, PG_DB
"""

from __future__ import annotations

import argparse
import os
import sys

from great_expectations.data_context import FileDataContext

from validators import apply_expectations

# ---------------------------------------------------------------------------
# Constants — must match gx/great_expectations.yml
# ---------------------------------------------------------------------------

GX_ROOT = os.path.join(os.path.dirname(__file__), "gx")

PG_DATASOURCE   = "postgres_staging"
PG_ASSET        = "text_comment_1"
PG_CHECKPOINT   = "postgres_staging_checkpoint"
PG_SUITE        = "toxic_comment_suite"

KAFKA_DATASOURCE = "kafka_filesystem"
KAFKA_ASSET      = "streaming_csv"
KAFKA_CHECKPOINT = "kafka_streaming_checkpoint"
KAFKA_SUITE      = "toxic_comment_suite"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_context() -> FileDataContext:
    return FileDataContext.create(project_root_dir=GX_ROOT)


def _build_validator(context, datasource_name: str, asset_name: str, suite_name: str):
    """Fetch batch request, register/update suite, return validator."""
    asset = context.get_datasource(datasource_name).get_asset(asset_name)
    batch_request = asset.build_batch_request()
    context.add_or_update_expectation_suite(suite_name)
    return context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name,
    )


def _run_checkpoint(context, checkpoint_name: str, validator) -> bool:
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
    print("\n=== Validating PostgreSQL staging source ===")

    validator = _build_validator(context, PG_DATASOURCE, PG_ASSET, PG_SUITE)
    print(validator.head())

    apply_expectations(validator, pg_format=True)
    validator.save_expectation_suite(discard_failed_expectations=False)

    return _run_checkpoint(context, PG_CHECKPOINT, validator)


def validate_kafka(context: FileDataContext) -> bool:
    print("\n=== Validating Kafka filesystem source ===")

    asset = context.get_datasource(KAFKA_DATASOURCE).get_asset(KAFKA_ASSET)
    batch_request = asset.build_batch_request()

    batches = asset.get_batch_list_from_batch_request(batch_request)
    print(f"Found {len(batches)} batch(es):")
    for b in batches:
        print(f"  {b.batch_spec}")

    context.add_or_update_expectation_suite(KAFKA_SUITE)
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=KAFKA_SUITE,
    )
    print(validator.head())

    apply_expectations(validator, pg_format=False)
    validator.save_expectation_suite(discard_failed_expectations=False)

    return _run_checkpoint(context, KAFKA_CHECKPOINT, validator)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run GX data validation for the Toxic Comment platform."
    )
    parser.add_argument(
        "--source",
        choices=["postgres", "kafka", "all"],
        default="all",
        help="Which data source to validate (default: all)",
    )
    args = parser.parse_args()

    context = _get_context()
    results: list[bool] = []

    if args.source in ("postgres", "all"):
        results.append(validate_postgres(context))

    if args.source in ("kafka", "all"):
        results.append(validate_kafka(context))

    print("\n=== Validation Summary ===")
    if all(results):
        print("PASSED")
        return 0
    else:
        print("FAILED — see Data Docs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
