"""
data_validation/validate.py
---------------------------
CLI entry-point for Great Expectations validation.

Validates two data sources:
  1. PostgreSQL batch staging table (staging.text_comment_1)
  2. PostgreSQL stream staging table (staging.streaming)

Usage (from data_validation/ directory):
    python validate.py --source postgres
    python validate.py --source stream
    python validate.py --source all      # default
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from great_expectations.data_context import FileDataContext
from validators import apply_expectations

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.load_config_from_file import load_cfg

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_VALIDATION_DIR = os.path.dirname(__file__)

PG_DATASOURCE   = "postgres_staging"
PG_BATCH_ASSET  = "batch"
PG_STREAM_ASSET = "streaming"
SUITE_NAME      = "toxic_comment_suite"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

import great_expectations as gx

def _get_context() -> FileDataContext:
    cfg_file = PROJECT_ROOT / "configs" / "config.yml"
    cfg = load_cfg(str(cfg_file))["dwh"]
    conn_str = f"postgresql+psycopg2://{cfg.get('user', 'k6')}:{cfg.get('password', 'k6')}@{cfg.get('host', 'localhost')}:{cfg.get('port', 5432)}/{cfg.get('database', 'k6')}"
    
    os.environ["DB_URL"] = conn_str
    
    context = gx.get_context(mode="file", project_root_dir=DATA_VALIDATION_DIR)
    
    try:
        ds = context.get_datasource(PG_DATASOURCE)
    except Exception:
        ds = context.data_sources.add_postgres(name=PG_DATASOURCE, connection_string="${DB_URL}")
    
    try:
        ds.get_asset(PG_BATCH_ASSET)
    except Exception:
        ds.add_table_asset(name=PG_BATCH_ASSET, table_name="batch", schema_name="staging")
        
    try:
        ds.get_asset(PG_STREAM_ASSET)
    except Exception:
        ds.add_table_asset(name=PG_STREAM_ASSET, table_name="streaming", schema_name="staging")

    return context


def _build_validator(context, datasource_name: str, asset_name: str, suite_name: str):
    """Fetch batch request, register/update suite, return validator."""
    asset = context.get_datasource(datasource_name).get_asset(asset_name)
    batch_request = asset.build_batch_request()
    
    try:
        suite = context.suites.get(name=suite_name)
    except Exception:
        suite = gx.ExpectationSuite(name=suite_name)
        suite = context.suites.add(suite)
        
    return context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name,
    )


def _run_checkpoint(context, checkpoint_name: str, validator) -> bool:
    result = validator.validate()
    try:
        context.build_data_docs()
    except Exception as e:
        print(f"Warning: Could not build data docs: {e}")
    return result.success


# ---------------------------------------------------------------------------
# Validation flows
# ---------------------------------------------------------------------------

def validate_postgres(context: FileDataContext) -> bool:
    print("\n=== Validating PostgreSQL batch source (batch) ===")
    validator = _build_validator(context, PG_DATASOURCE, PG_BATCH_ASSET, SUITE_NAME)
    # print(validator.head())
    apply_expectations(validator, pg_format=False)
    try:
        suite = validator.expectation_suite
        suite.save()
    except Exception as e:
        print(f"Warning: {e}")
    return _run_checkpoint(context, "postgres_batch_checkpoint", validator)


def validate_stream(context: FileDataContext) -> bool:
    print("\n=== Validating PostgreSQL stream source (staging.streaming) ===")
    validator = _build_validator(context, PG_DATASOURCE, PG_STREAM_ASSET, SUITE_NAME)
    # print(validator.head())
    # Both are Postgres now, so pg_format=True
    apply_expectations(validator, pg_format=False)
    try:
        suite = validator.expectation_suite
        suite.save()
    except Exception as e:
        print(f"Warning: {e}")
    return _run_checkpoint(context, "postgres_stream_checkpoint", validator)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run GX data validation for the Toxic Comment platform."
    )
    parser.add_argument(
        "--source",
        choices=["postgres", "stream", "all"],
        default="all",
        help="Which data source to validate (default: all)",
    )
    args = parser.parse_args()

    context = _get_context()
    results: list[bool] = []

    if args.source in ("postgres", "all"):
        results.append(validate_postgres(context))

    if args.source in ("stream", "all"):
        results.append(validate_stream(context))

    print("\n=== Validation Summary ===")
    if all(results):
        print("PASSED")
        return 0
    else:
        print("FAILED — see Data Docs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
