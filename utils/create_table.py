import sys
from pathlib import Path

from loguru import logger

from load_config_from_file import load_cfg
from postgresql_client import PostgreSQLClient

CFG_FILE = "./configs/config.yml"

TABLE_DEFINITIONS: list[tuple[str, str]] = [
    # Bảng staging.batch: Lưu trữ dữ liệu text đã được mã hóa (tokenized) từ luồng Batch.
    # Các trường 'input_ids' và 'attention_mask' là định dạng chuẩn đầu vào cho các mô hình NLP (như BERT, RoBERTa).
    ("staging.batch", """
        CREATE TABLE IF NOT EXISTS staging.batch (
            labels         BIGINT,
            input_ids      TEXT,
            attention_mask TEXT
        );
    """),
    # Bảng stream.raw_comments: Lưu trữ bình luận thô (chưa qua tokenized) theo thời gian thực (real-time).
    # Bảng này thường được đổ dữ liệu trực tiếp từ Kafka/Debezium vào hệ thống.
    ("stream.raw_comments", """
        CREATE TABLE IF NOT EXISTS stream.raw_comments (
            id           SERIAL PRIMARY KEY,
            comment_text TEXT,
            labels       BIGINT,
            created_at   TIMESTAMP DEFAULT NOW()
        );
    """),
    # Bảng production.comments: Bảng đích (Data Warehouse/Production) lưu trữ dữ liệu sạch cuối cùng.
    # Dữ liệu từ các bảng staging và stream sau khi được dbt làm sạch & tokenized sẽ được hợp nhất vào đây
    # để sẵn sàng cho việc huấn luyện (train) Machine Learning hoặc Data Analysis.`
    # Bảng staging.streaming: Lưu dữ liệu stream đã qua Flink tokenize tạm thời
    ("staging.streaming", """
        CREATE TABLE IF NOT EXISTS staging.streaming (
            id             VARCHAR(255) PRIMARY KEY,
            labels         BIGINT,
            input_ids      TEXT,
            attention_mask TEXT,
            inserted_at    TIMESTAMP DEFAULT NOW()
        );
    """),
    ("production.comments", """
        CREATE TABLE IF NOT EXISTS production.comments (
            id             VARCHAR(255) PRIMARY KEY,
            labels         BIGINT,
            input_ids      TEXT,
            attention_mask TEXT,
            inserted_at    TIMESTAMP DEFAULT NOW()
        );
    """),
]


def main():
    cfg = load_cfg(str(CFG_FILE))["dwh"]

    try:
        with PostgreSQLClient(
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            host=cfg.get("host", "localhost"),
            port=cfg.get("port", 5433),
        ) as pc:
            for table_name, ddl in TABLE_DEFINITIONS:
                try:
                    pc.execute_query(ddl)
                    logger.success(f"Table '{table_name}' ready.")
                except Exception as e:
                    logger.error(f"Failed to create table '{table_name}': {e}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()