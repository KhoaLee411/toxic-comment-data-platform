from __future__ import annotations
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

PROJ_DIR = '/opt/project'
PYTHON = 'python'
MIN_AUC = 0.80

DEFAULT_ARGS = {
    'owner': 'mlops-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'retry_exponential_backoff': True,
    'execution_timeout': timedelta(hours=2),
    'on_failure_callback': lambda ctx: print(f'[FAILED] Task: {ctx["task_instance"].task_id} | Exception: {ctx.get("exception")}')
}

def bash_task(task_id: str, cmd: str, workdir: str = PROJ_DIR, **kwargs) -> BashOperator:
    full_cmd = f"""
        set -euo pipefail
        export IS_DOCKER=true
        if [ -f {PROJ_DIR}/.env ]; then
            export $(grep -v '^#' {PROJ_DIR}/.env | xargs)
        fi
        export POSTGRES_HOST=postgres_datalake
        export POSTGRES_PORT=5432
        cd {workdir}
        {cmd}
    """
    return BashOperator(task_id=task_id, bash_command=full_cmd, **kwargs)

def check_eval_metrics(**ctx):
    import json
    metrics_path = f'{PROJ_DIR}/metrics/eval_metrics.json'
    with open(metrics_path) as f:
        metrics = json.load(f)
    auc = metrics.get('auc', 0.0)
    if auc < MIN_AUC:
        raise ValueError(f'AUC {auc:.4f} below {MIN_AUC}')

with DAG(
    dag_id='end_to_end_ml_pipeline',
    default_args=DEFAULT_ARGS,
    description='Batch ML Pipeline',
    start_date=datetime(2025, 8, 15),
    schedule_interval='@daily',
    catchup=False,
    max_active_runs=1,
    tags=['ml', 'batch'],
) as dag:
    batch_processing = bash_task('batch_processing', cmd=f'echo "Starting Batch..." && {PYTHON} batch_processing/main.py')
    validate_postgres = bash_task('validate_postgres', cmd=f'{PYTHON} data_validation/validate.py --source postgres')

    with TaskGroup('data_transformation') as data_transform:
        dbt_run = bash_task('dbt_run', cmd='dbt run --profiles-dir . --target prod', workdir=f'{PROJ_DIR}/data_transformation')
        dbt_test = bash_task('dbt_test', cmd='dbt test --profiles-dir . --target prod', workdir=f'{PROJ_DIR}/data_transformation')
        dbt_run >> dbt_test

    with TaskGroup('model_experimentation') as model_exp:
        dvc_extract = bash_task('dvc_extract', cmd='dvc repro extract')
        dvc_train = bash_task('dvc_train', cmd='dvc repro train')
        dvc_evaluate = bash_task('dvc_evaluate', cmd='dvc repro evaluate')
        metric_gate = PythonOperator(task_id='metric_gate', python_callable=check_eval_metrics)
        dvc_register = bash_task('dvc_register', cmd='dvc repro register')
        dvc_push = bash_task('dvc_push', cmd="dvc remote modify --local minio_remote endpointurl http://minio:9000 && dvc remote modify --local minio_remote access_key_id admin && dvc remote modify --local minio_remote secret_access_key admin123 && dvc push")
        dvc_extract >> dvc_train >> dvc_evaluate >> metric_gate >> dvc_register >> dvc_push

    batch_processing >> validate_postgres >> data_transform >> model_exp
