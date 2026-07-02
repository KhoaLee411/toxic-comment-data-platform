FROM apache/airflow:2.10.4-python3.11

USER root

RUN apt-get update && \
    apt-get install -y git && \
    apt-get install -y libgomp1 default-jre procps

USER airflow

# Fix bug Airflow với PostgreSQL connection
RUN pip install git+https://github.com/mpgreg/airflow-provider-great-expectations.git@87a42e275705d413cd4482134fc0d94fa1a68e6f

COPY ./requirements-airflow.txt /requirements-airflow.txt
COPY ./requirements-ml.txt /requirements-ml.txt

# 1) Cài phần liên quan trực tiếp tới Airflow VỚI constraints file
#    -> pip khoá sẵn version botocore/boto3/... nên KHÔNG backtrack
RUN pip install --no-cache-dir -r /requirements-airflow.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.11.txt"

# 2) Cài phần ML nặng RIÊNG, không kèm constraints của Airflow
#    (tách ra để pip không phải giải chung 1 đồ thị khổng lồ)
RUN pip install --no-cache-dir -r /requirements-ml.txt

ENV PATH="/home/airflow/.local/bin:$PATH"