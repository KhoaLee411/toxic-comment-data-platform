from __future__ import annotations
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJ_DIR = '/opt/project'
PYTHON = 'python'

DEFAULT_ARGS = {
    'owner': 'mlops-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

def bash_task(task_id: str, cmd: str, workdir: str = PROJ_DIR, **kwargs) -> BashOperator:
    full_cmd = f"""
        set -euo pipefail
        export PATH=$HOME/.local/bin:$PATH
        export IS_DOCKER=true
        if [ -f {PROJ_DIR}/.env ]; then
            export $(grep -v '^#' {PROJ_DIR}/.env | xargs)
        fi
        cd {workdir}
        {cmd}
    """
    return BashOperator(task_id=task_id, bash_command=full_cmd, **kwargs)

with DAG(
    dag_id='data_ingestion_pipeline',
    default_args=DEFAULT_ARGS,
    description='Ingest raw CSV data into Delta format and upload to MinIO',
    start_date=datetime(2025, 8, 15),
    schedule_interval=None,  # Trigger manual
    catchup=False,
    tags=['ingestion', 'batch', 'minio'],
) as dag:
    
    ingest_to_datalake = bash_task(
        task_id='ingest_csv_to_minio',
        cmd=f'{PYTHON} utils/csv_to_delta_table.py && {PYTHON} utils/upload_data_to_datalake.py',
    )
