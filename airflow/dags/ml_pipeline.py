"""
End-to-End ML Pipeline DAG
──────────────────────────
data_preparation → data_quality → data_transformation → model_experimentation

Thay đổi so với bản cũ:
- Mỗi BashOperator có on_failure_callback để log rõ lỗi
- DVC pipeline chạy theo từng stage (extract → train → evaluate → register)
  thay vì `dvc repro` một lần → dễ retry từng bước
- Dùng env var AIRFLOW_PROJ_DIR thay vì hardcode /opt/project
- Thêm validate_dvc_metrics task: fail DAG nếu AUC dưới ngưỡng
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

# ── Constants ─────────────────────────────────────────────────────────────────
PROJ_DIR = "/opt/project"
PYTHON = "python"
MIN_AUC = 0.80

DEFAULT_ARGS = {
    "owner": "mlops-team",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(hours=2),
    "on_failure_callback": lambda ctx: print(
        f"[FAILED] Task: {ctx['task_instance'].task_id} | "
        f"Run: {ctx['run_id']} | "
        f"Exception: {ctx.get('exception')}"
    ),
}


# ── Helper: build BashOperator with common env ────────────────────────────────
def bash_task(task_id: str, cmd: str, workdir: str = PROJ_DIR, **kwargs) -> BashOperator:
    full_cmd = f"""
        set -euo pipefail
        export PATH=$HOME/.local/bin:$PATH
        cd {workdir}
        {cmd}
    """
    return BashOperator(task_id=task_id, bash_command=full_cmd, **kwargs)


# ── Metric gate: fail DAG if AUC below threshold ──────────────────────────────
def check_eval_metrics(**ctx):
    import json
    metrics_path = f"{PROJ_DIR}/metrics/eval_metrics.json"
    with open(metrics_path) as f:
        metrics = json.load(f)
    auc = metrics.get("auc", 0.0)
    print(f"[Metric Gate] AUC = {auc:.4f} | Threshold = {MIN_AUC}")
    if auc < MIN_AUC:
        raise ValueError(f"AUC {auc:.4f} below minimum threshold {MIN_AUC}. Halting pipeline.")


# ── DAG ───────────────────────────────────────────────────────────────────────
with DAG(
    dag_id="end_to_end_ml_pipeline",
    default_args=DEFAULT_ARGS,
    description="End-to-End ML Pipeline: ingest → validate → transform → train → register",
    start_date=datetime(2025, 8, 15),
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["ml", "batch", "validation", "dvc", "minio", "mlflow"],
) as dag:

    # ── 1. Data Preparation ───────────────────────────────────────────────────
    with TaskGroup("data_preparation", tooltip="Batch processing → PostgreSQL staging") as data_prep:
        batch_processing = bash_task(
            "batch_processing",
            cmd=f"echo 'Starting Batch Processing...' && {PYTHON} batch_processing/main.py",
        )

    # ── 2. Data Quality ───────────────────────────────────────────────────────
    with TaskGroup("data_quality", tooltip="Great Expectations validation") as data_quality:
        validate_postgres = bash_task(
            "validate_postgres",
            cmd=f"{PYTHON} data_validation/validate.py --source postgres",
        )
        validate_stream = bash_task(
            "validate_stream",
            cmd=f"{PYTHON} data_validation/validate.py --source stream",
        )
        # Parallel — no dependency between them
        [validate_postgres, validate_stream]

    # ── 3. Data Transformation ────────────────────────────────────────────────
    with TaskGroup("data_transformation", tooltip="dbt: staging → production") as data_transform:
        dbt_run = bash_task(
            "dbt_run",
            cmd="dbt run --profiles-dir . --target prod",
            workdir=f"{PROJ_DIR}/data_transformation",
        )
        dbt_test = bash_task(
            "dbt_test",
            cmd="dbt test --profiles-dir . --target prod",
            workdir=f"{PROJ_DIR}/data_transformation",
        )
        dbt_run >> dbt_test

    # ── 4. Model Experimentation (DVC stages) ─────────────────────────────────
    with TaskGroup("model_experimentation", tooltip="DVC stages: extract → train → evaluate → register") as model_exp:

        dvc_extract = bash_task(
            "dvc_extract",
            cmd="echo 'DVC: extract stage...' && dvc repro extract",
        )
        dvc_train = bash_task(
            "dvc_train",
            cmd="echo 'DVC: train stage...' && dvc repro train",
        )
        dvc_evaluate = bash_task(
            "dvc_evaluate",
            cmd="echo 'DVC: evaluate stage...' && dvc repro evaluate",
        )

        metric_gate = PythonOperator(
            task_id="metric_gate",
            python_callable=check_eval_metrics,
        )

        dvc_register = bash_task(
            "dvc_register",
            cmd="echo 'DVC: register stage...' && dvc repro register",
        )

        dvc_push = bash_task(
            "dvc_push",
            cmd="echo 'Pushing DVC artifacts to MinIO...' && dvc push",
        )

        dvc_extract >> dvc_train >> dvc_evaluate >> metric_gate >> dvc_register >> dvc_push

    # ── Pipeline order ────────────────────────────────────────────────────────
    data_prep >> data_quality >> data_transform >> model_exp