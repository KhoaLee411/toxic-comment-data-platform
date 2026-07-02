from __future__ import annotations
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJ_DIR = '/opt/project'
PYTHON = 'python'

DEFAULT_ARGS = {
    'owner': 'mlops-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
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

with DAG(
    dag_id='stream_simulation_pipeline',
    default_args=DEFAULT_ARGS,
    start_date=datetime(2025, 8, 15),
    schedule_interval=None,
    catchup=False,
    tags=['stream', 'simulation'],
) as dag_stream:
    stream_processing = bash_task('stream_processing', cmd=f'nohup {PYTHON} stream_processing/main.py > /tmp/flink.log 2>&1 & sleep 10')
    stream_simulation = bash_task('stream_simulation', cmd=f'{PYTHON} utils/simulate_stream.py')
    stream_processing >> stream_simulation

with DAG(
    dag_id='stream_data_quality',
    default_args=DEFAULT_ARGS,
    start_date=datetime(2025, 8, 15),
    schedule_interval='*/2 * * * *',
    catchup=False,
    tags=['stream', 'validation'],
) as dag_val:
    validate_stream = bash_task('validate_stream', cmd=f'{PYTHON} data_validation/validate.py --source stream')
