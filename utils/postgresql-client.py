import psycopg2


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
        print(f"✅ Executed: {query.strip()[:80]}")

    def close(self):
        self.conn.close()