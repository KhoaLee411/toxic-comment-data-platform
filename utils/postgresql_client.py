import psycopg2
from loguru import logger


class PostgresSQLClient:
    def __init__(self, database, user, password, host="localhost", port=5433):
        self.conn = psycopg2.connect(
            dbname=database,
            user=user,
            password=password,
            host=host,
            port=int(port),
        )
        self.conn.autocommit = True

    def execute_query(self, query: str):
        with self.conn.cursor() as cur:
            cur.execute(query)
        logger.debug(f"Executed: {query.strip()[:80]}")

    def execute_query_params(self, query: str, params):
        with self.conn.cursor() as cur:
            cur.execute(query, params)

    def get_columns(self, table_name: str) -> list[str]:
        if "." in table_name:
            schema, table = table_name.split(".", 1)
        else:
            schema, table = "public", table_name
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s "
                "ORDER BY ordinal_position",
                (schema, table),
            )
            rows = cur.fetchall()
        return [row[0] for row in rows]

    def close(self):
        self.conn.close()
