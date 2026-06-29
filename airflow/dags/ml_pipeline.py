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
                echo "Starting Batch Processing..."
                python main.py
            """,
        )

    with TaskGroup(group_id="data_quality", tooltip="Great Expectations validation") as data_quality:
        # Validate PostgreSQL staging table (populated by batch pipeline)
        validate_postgres = BashOperator(
            task_id="validate_postgres",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project/data_validation
                echo "Running GX validation: postgres..."
                python validate.py --source postgres
            """,
        )

        # Validate Stream (staging.streaming)
        validate_stream = BashOperator(
            task_id="validate_stream",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project/data_validation
                echo "Running GX validation: stream..."
                python validate.py --source stream
            """,
        )

        # Both validations are independent — run in parallel
        [validate_postgres, validate_stream]

    with TaskGroup(group_id="data_transformation", tooltip="dbt transform staging → production") as data_transform:
        run_dbt = BashOperator(
            task_id="dbt_run",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project/data_transformation
                echo "Running dbt models..."
                dbt run --profiles-dir . --target prod
            """,
        )

        run_dbt_test = BashOperator(
            task_id="dbt_test",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project/data_transformation
                echo "Running dbt tests..."
                dbt test --profiles-dir . --target prod
            """,
        )

        run_dbt >> run_dbt_test

    with TaskGroup(group_id="model_experimentation", tooltip="DVC reproduction and tracking") as model_exp:
        run_dvc_repro = BashOperator(
            task_id="dvc_repro",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project
                echo "Running DVC repro..."
                dvc repro
            """,
        )

        push_dvc_to_remote = BashOperator(
            task_id="dvc_push",
            bash_command="""
                export PATH=$HOME/.local/bin:$PATH
                cd /opt/project
                echo "Pushing DVC outputs to MinIO remote..."
                dvc push
            """,
        )

        run_dvc_repro >> push_dvc_to_remote

    # Pipeline: batch → validate → dbt transform → train
    data_prep >> data_quality >> data_transform >> model_exp
