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
        export PATH=\/home/khoa-lee/.local/bin:\/home/khoa-lee/.local/bin:/home/khoa-lee/go/bin:/usr/local/go/bin:/usr/lib/jvm/java-17-openjdk-amd64/bin:/home/khoa-lee/.nvm/versions/node/v22.22.3/bin:/home/khoa-lee/miniconda3/bin:/home/khoa-lee/miniconda3/condabin:/home/khoa-lee/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/snap/bin
        export IS_DOCKER=true
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
