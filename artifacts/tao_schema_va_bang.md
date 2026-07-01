# Tạo Schema và Bảng (PostgreSQL)

Kết quả thực thi thành công việc tạo các Schema và Bảng vật lý bên trong cơ sở dữ liệu PostgreSQL. Các bảng này đóng vai trò là nơi lưu trữ dữ liệu staging và production cho hệ thống.

**Lệnh thực thi:**

```bash
python utils/create_schema.py && python utils/create_table.py
```

**Output Log:**

```text
2026-07-02 00:04:49.097 | DEBUG    | postgresql_client:execute_query:26 - Executed: CREATE SCHEMA IF NOT EXISTS staging;
2026-07-02 00:04:49.097 | SUCCESS  | __main__:main:26 - Schema 'staging' ready.
2026-07-02 00:04:49.097 | DEBUG    | postgresql_client:execute_query:26 - Executed: CREATE SCHEMA IF NOT EXISTS production;
2026-07-02 00:04:49.097 | SUCCESS  | __main__:main:26 - Schema 'production' ready.
2026-07-02 00:04:49.097 | DEBUG    | postgresql_client:execute_query:26 - Executed: CREATE SCHEMA IF NOT EXISTS stream;
2026-07-02 00:04:49.098 | SUCCESS  | __main__:main:26 - Schema 'stream' ready.
2026-07-02 00:04:49.521 | DEBUG    | postgresql_client:execute_query:26 - Executed: CREATE TABLE IF NOT EXISTS staging.batch (
            labels         INT,

2026-07-02 00:04:49.522 | SUCCESS  | __main__:main:70 - Table 'staging.batch' ready.
2026-07-02 00:04:49.522 | DEBUG    | postgresql_client:execute_query:26 - Executed: CREATE TABLE IF NOT EXISTS stream.raw_comments (
            id           SERIAL
2026-07-02 00:04:49.522 | SUCCESS  | __main__:main:70 - Table 'stream.raw_comments' ready.
2026-07-02 00:04:49.523 | DEBUG    | postgresql_client:execute_query:26 - Executed: CREATE TABLE IF NOT EXISTS staging.streaming (
            id             VARCHA
2026-07-02 00:04:49.523 | SUCCESS  | __main__:main:70 - Table 'staging.streaming' ready.
2026-07-02 00:04:49.523 | DEBUG    | postgresql_client:execute_query:26 - Executed: CREATE TABLE IF NOT EXISTS production.comments (
            id             VARC
2026-07-02 00:04:49.523 | SUCCESS  | __main__:main:70 - Table 'production.comments' ready.
2026-07-02 00:04:49.524 | DEBUG    | postgresql_client:execute_query:26 - Executed: ALTER TABLE stream.raw_comments REPLICA IDENTITY FULL;
2026-07-02 00:04:49.526 | DEBUG    | postgresql_client:execute_query:26 - Executed: DROP PUBLICATION IF EXISTS dbz_publication;
2026-07-02 00:04:49.527 | DEBUG    | postgresql_client:execute_query:26 - Executed: CREATE PUBLICATION dbz_publication FOR TABLE stream.raw_comments;
2026-07-02 00:04:49.527 | SUCCESS  | __main__:main:88 - Publication 'dbz_publication' ready for Debezium CDC.
```
