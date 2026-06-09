from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="end_to_end_ml_pipeline",
    default_args=default_args,
    description="End-to-End Machine Learning Pipeline Orchestration",
    start_date=datetime(2025, 8, 15),
    schedule_interval="@daily",
    catchup=False,
    tags=["ml", "batch", "validation", "dvc", "minio", "mlflow"],
) as dag:

    with TaskGroup(group_id="data_preparation", tooltip="Batch processing and data staging") as data_prep:
        run_batch_processing = BashOperator(
            task_id="batch_processing",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project/batch_processing
                echo "🚀 Starting Batch Processing..."
                python main.py
            """,
        )

    with TaskGroup(group_id="data_quality", tooltip="Great Expectations validation") as data_quality:
        run_data_validation = BashOperator(
            task_id="validate_postgres",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project/data_validation
                echo "✅ Running Great Expectations validation..."
                python validate.py --source postgres
            """,
        )

    with TaskGroup(group_id="model_experimentation", tooltip="DVC reproduction and tracking") as model_exp:
        run_dvc_repro = BashOperator(
            task_id="dvc_repro",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project
                echo "🔁 Running DVC repro..."
                which dvc
                dvc repro
            """,
        )

        push_dvc_to_remote = BashOperator(
            task_id="dvc_push",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project
                echo "☁️ Pushing DVC outputs to MinIO remote..."
                dvc push
            """,
        )
        
        run_dvc_repro >> push_dvc_to_remote

    # Define the pipeline dependencies
    data_prep >> data_quality >> model_exp
