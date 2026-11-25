"""Run a synthetic incremental-state contract through PostgreSQL and DuckDB."""

import json
from pathlib import Path
from queue import Empty, Queue
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic, sleep

import duckdb


IMAGE = "postgres@sha256:c699303802144847d238196173655dbbecf7a96aeca1565f2b02eb671a1f0b6b"
SCHEMA = "CREATE TABLE events(id integer PRIMARY KEY, bucket integer NOT NULL, amount bigint);"
SEED = """INSERT INTO events
SELECT i, i % 40, CASE WHEN i % 7 = 0 OR i % 40 = 39 THEN NULL ELSE i % 101 - 50 END
FROM generate_series(1, 2000) AS g(i);"""
CHANGE = """INSERT INTO events VALUES (2001, 1, 71), (2002, 87, NULL);
UPDATE events SET bucket = 2, amount = NULL WHERE id = 1;
DELETE FROM events WHERE id = 2;"""
RESEED = "INSERT INTO events VALUES (7, 8, NULL), (8, 8, 5), (9, 1, NULL);"
GROUPS = """SELECT bucket, count(*) n, count(amount) known, sum(amount) total
FROM events GROUP BY bucket"""
QUERIES = [
    ("all_rows", "SELECT count(*) FROM events", "SELECT coalesce(sum(n),0) FROM buckets"),
    ("known_amounts", "SELECT count(amount) FROM events", "SELECT coalesce(sum(known),0) FROM buckets"),
    ("total_by_bucket", "SELECT sum(amount) FROM events WHERE bucket=39",
     "SELECT sum(total) FILTER (WHERE known>0) FROM buckets WHERE bucket=39"),
    ("min_bucket_total", f"SELECT min(total) FROM ({GROUPS}) g",
     "SELECT min(total) FILTER (WHERE known>0) FROM buckets"),
    ("number_of_buckets", "SELECT count(DISTINCT bucket) FROM events", "SELECT count(*) FROM buckets"),
    ("range_count", "SELECT count(*) FROM events WHERE bucket BETWEEN 1 AND 8",
     "SELECT coalesce(sum(n),0) FROM buckets WHERE bucket BETWEEN 1 AND 8"),
    ("empty_bucket", "SELECT sum(amount) FROM events WHERE bucket=-1",
     "SELECT sum(total) FILTER (WHERE known>0) FROM buckets WHERE bucket=-1"),
    ("null_rows", "SELECT id FROM events WHERE amount IS NULL AND bucket=8 ORDER BY id", None),
]
REBUILD = """DELETE FROM buckets;
INSERT INTO buckets SELECT bucket, n, known, coalesce(total,0) FROM (""" + GROUPS + """) g;
UPDATE cache_status SET valid=true;"""
MAINTENANCE = """
CREATE TABLE buckets(bucket integer PRIMARY KEY, n bigint, known bigint, total numeric);
CREATE TABLE cache_status(valid boolean NOT NULL);
INSERT INTO cache_status VALUES (false);
CREATE FUNCTION maintain_buckets() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT (SELECT valid FROM cache_status) THEN RETURN NULL; END IF;
    IF TG_OP <> 'INSERT' THEN
        UPDATE buckets SET n=n-1, known=known-(OLD.amount IS NOT NULL)::int,
               total=total-coalesce(OLD.amount,0) WHERE bucket=OLD.bucket;
        DELETE FROM buckets WHERE bucket=OLD.bucket AND n=0;
    END IF;
    IF TG_OP <> 'DELETE' THEN
        INSERT INTO buckets VALUES (NEW.bucket, 1, (NEW.amount IS NOT NULL)::int, coalesce(NEW.amount,0))
        ON CONFLICT (bucket) DO UPDATE SET n=buckets.n+1, known=buckets.known+excluded.known,
                                         total=buckets.total+excluded.total;
    END IF;
    RETURN NULL;
END $$;
CREATE FUNCTION invalidate_buckets() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    UPDATE cache_status SET valid=false;
    RETURN NULL;
END $$;
CREATE TRIGGER events_maintain AFTER INSERT OR UPDATE OR DELETE ON events
FOR EACH ROW EXECUTE FUNCTION maintain_buckets();
CREATE TRIGGER events_invalidate AFTER TRUNCATE ON events
FOR EACH STATEMENT EXECUTE FUNCTION invalidate_buckets();
"""


def docker(*args, check=True):
    return subprocess.run(["docker", *args], capture_output=True, text=True, encoding="utf-8",
                          check=check, timeout=40)


class PgSession:
    def __init__(self, container):
        self.process = subprocess.Popen(
            ["docker", "exec", "-i", container, "psql", "-XqAt", "-U", "postgres", "-v", "ON_ERROR_STOP=1"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8",
        )
        self.output = Queue()
        self.reader = Thread(target=self.read_output, daemon=True)
        self.reader.start()

    def read_output(self):
        for line in self.process.stdout:
            self.output.put(line.rstrip("\r\n"))
        self.output.put(None)

    def sql(self, sql):
        self.process.stdin.write(sql + "\n\\echo LAB_SQL_DONE\n")
        self.process.stdin.flush()
        lines = []
        deadline = monotonic() + 20
        while True:
            try:
                line = self.output.get(timeout=max(0, deadline - monotonic()))
            except Empty as error:
                raise TimeoutError("PostgreSQL lab command timed out") from error
            if line == "LAB_SQL_DONE":
                return lines
            if line is None:
                raise RuntimeError("\n".join(lines) or "PostgreSQL lab connection closed")
            lines.append(line)

    def rows(self, query):
        return json.loads("\n".join(self.sql(f"SELECT coalesce(json_agg(q), '[]') FROM ({query}) q;")),
                          object_pairs_hook=lambda pairs: [value for _, value in pairs])

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=6)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=6)
        self.reader.join(timeout=2)
        self.process.stdout.close()


def verify(label, pg, oracle, valid):
    actual_valid, = pg.sql("SELECT valid FROM cache_status;")
    if (actual_valid == "t") != valid:
        raise AssertionError(f"{label}: wrong cache state")
    report, rows = {}, {}
    for name, plain, candidate in QUERIES:
        expected = [list(row) for row in oracle.execute(plain).fetchall()]
        route = "state" if candidate and actual_valid == "t" else "sql"
        rows[name] = pg.rows(candidate if route == "state" else plain)
        if rows[name] != expected or pg.rows(plain) != expected:
            raise AssertionError(f"{label}, {name}: result differs from oracle")
        report[name] = route
    return report, rows


def run(container):
    pg, reader = PgSession(container), None
    oracle = duckdb.connect(config={"threads": 1, "memory_limit": "128MB", "enable_external_access": False})
    reports = {}
    try:
        version, = pg.sql("SHOW server_version_num;")
        if version != "180007" or duckdb.__version__ != "1.5.4":
            raise ValueError("Expected PostgreSQL 18.7 and DuckDB 1.5.4")
        pg.sql(SCHEMA + SEED + MAINTENANCE + REBUILD)
        oracle.execute(SCHEMA + SEED)
        reports["initial"], _ = verify("initial", pg, oracle, True)
        pg.sql("BEGIN;" + CHANGE + "ROLLBACK;")
        reports["rollback"], _ = verify("rollback", pg, oracle, True)

        reader = PgSession(container)
        reader.sql("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY; SELECT count(*) FROM events;")
        pg.sql("BEGIN;" + CHANGE + "COMMIT;")
        reports["held_snapshot"], stale = verify("held_snapshot", reader, oracle, True)
        reader.sql("COMMIT;")
        oracle.execute("BEGIN;" + CHANGE + "COMMIT;")
        reports["after_commit"], current = verify("after_commit", pg, oracle, True)
        if stale["all_rows"] == current["all_rows"]:
            raise AssertionError("The stale-snapshot control did not differ from the new snapshot")

        pg.sql("TRUNCATE events;" + RESEED)
        oracle.execute("TRUNCATE events;" + RESEED)
        reports["fallback"], fallback = verify("fallback", pg, oracle, False)
        if pg.rows(QUERIES[0][2]) == fallback["all_rows"]:
            raise AssertionError("The invalidated state did not differ from the SQL fallback")
        pg.sql("BEGIN;" + REBUILD + "COMMIT;")
        reports["rebuild"], _ = verify("rebuild", pg, oracle, True)
        return dict(postgres=version, image=IMAGE, duckdb=duckdb.__version__,
                    candidate="lab_trigger_maintained_buckets", exact_comparisons=2 * len(QUERIES) * len(reports),
                    stale_result_control_detected=True, forced_stale_fallback_control_detected=True,
                    stages=reports)
    finally:
        if reader:
            reader.close()
        pg.close()
        oracle.close()


def main():
    with TemporaryDirectory(prefix="jetstream-lab-") as folder:
        cidfile = Path(folder) / "container.id"
        try:
            container = docker("run", "--detach", "--cidfile", str(cidfile), "--pull=never",
                               "--network=none", "--cpus=2", "--memory=1g",
                               "-e", "POSTGRES_HOST_AUTH_METHOD=trust", IMAGE,
                               "-c", "listen_addresses=").stdout.strip()
            deadline = monotonic() + 45
            while monotonic() < deadline:
                pid_one = docker("exec", container, "cat", "/proc/1/comm", check=False).stdout.strip()
                if pid_one == "postgres" and docker("exec", container, "pg_isready", "-q", check=False).returncode == 0:
                    result = run(container)
                    sys.stdout.buffer.write((json.dumps(result, indent=2) + "\n").encode("ascii"))
                    return
                sleep(0.4)
            raise TimeoutError("PostgreSQL lab failed to start")
        finally:
            if cidfile.is_file():
                docker("rm", "-fv", cidfile.read_text(encoding="ascii").strip())


if __name__ == "__main__":
    main()
