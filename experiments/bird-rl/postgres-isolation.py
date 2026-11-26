"""Compare three PostgreSQL trajectory boundaries in disposable offline containers."""
from contextlib import contextmanager
import hashlib
import json
from statistics import median
import subprocess
import time
from uuid import uuid4

IMAGE = "postgres@sha256:c699303802144847d238196173655dbbecf7a96aeca1565f2b02eb671a1f0b6b"
SUITE = uuid4().hex[:12]
ROWS = 20_000
TRAJECTORIES = 3
BASE = "bird_seed"
SEED_SQL = f"""
CREATE TABLE tasks (id integer PRIMARY KEY, status text NOT NULL);
INSERT INTO tasks SELECT n, 'ready' FROM generate_series(1, {ROWS}) AS s(n);
CREATE SEQUENCE task_token START WITH 1;
"""
STATE_SQL = """
SELECT json_build_object(
  'rows', (SELECT count(*) FROM tasks),
  'done', (SELECT count(*) FROM tasks WHERE status = 'done'),
  'table_hash', (SELECT md5(string_agg(id::text || ':' || status, ',' ORDER BY id)) FROM tasks),
  'sequence', (SELECT json_build_array(last_value, is_called) FROM task_token),
  'marker', to_regclass('public.trajectory_marker') IS NOT NULL
);
"""
RESOURCE_SQL = """
SELECT json_build_object(
  'wal_lsn', pg_current_wal_insert_lsn()::text,
  'reads', coalesce(sum(reads), 0),
  'writes', coalesce(sum(writes), 0),
  'extends', coalesce(sum(extends), 0)
) FROM pg_stat_io WHERE backend_type = 'client backend';
"""


def docker(*args, input_text=None):
    completed = subprocess.run(["docker", *args], input=input_text, text=True,
                               capture_output=True, timeout=65, check=False)
    if completed.returncode:
        raise RuntimeError(f"docker {args[0]} returned {completed.returncode}: "
                           f"{completed.stderr.strip()[-1500:]}")
    return completed.stdout.strip()


@contextmanager
def cluster(arm):
    name = f"bird-rl-{SUITE}-{arm}"
    docker("run", "--detach", "--rm", "--pull", "never", "--name", name,
           "--label", f"org.research-hub.bird-rl={SUITE}", "--network", "none",
           "--cpus", "2", "--memory", "512m",
           "--tmpfs", "/var/lib/postgresql:rw,nosuid,nodev,mode=1777,size=256m",
           "-e", "POSTGRES_PASSWORD=synthetic-test-only", IMAGE, "postgres",
           "-c", "listen_addresses=", "-c", "autovacuum=off", "-c", "shared_buffers=32MB")
    try:
        until = time.monotonic() + 40
        while time.monotonic() < until:
            if docker("exec", name, "cat", "/proc/1/comm") == "postgres":
                ready = subprocess.run(
                    ["docker", "exec", name, "pg_isready", "-q", "-U", "postgres"],
                    timeout=5, check=False,
                )
                if ready.returncode == 0:
                    break
            time.sleep(0.20)
        else:
            raise RuntimeError("The isolated PostgreSQL instance did not start.")
        yield name
    finally:
        docker("stop", "--timeout", "5", name)


def sql(name, database, query):
    return docker("exec", "-i", name, "psql", "-XqAt", "-v", "ON_ERROR_STOP=1",
                  "-U", "postgres", "-d", database, input_text=query)


def seed(name):
    sql(name, "postgres", f"CREATE DATABASE {BASE};")
    sql(name, BASE, SEED_SQL)


def state(name, database):
    return json.loads(sql(name, database, STATE_SQL))


def counters(name):
    return json.loads(sql(name, "postgres", RESOURCE_SQL))


def lsn(value):
    high, low = value.split("/")
    return (int(high, 16) << 32) + int(low, 16)


def delta(before, after):
    result = {key: after[key] - before[key] for key in ("reads", "writes", "extends")}
    result["wal_bytes"] = lsn(after["wal_lsn"]) - lsn(before["wal_lsn"])
    assert all(value >= 0 for value in result.values())
    return result


def end_storage(name, database):
    db_size = sql(name, database, "SELECT pg_database_size(current_database());")
    memory = docker("exec", name, "cat", "/sys/fs/cgroup/memory.current")
    data = docker("exec", name, "du", "-sB1", "/var/lib/postgresql/18/docker")
    return dict(database_bytes=int(db_size), cgroup_memory_bytes=int(memory),
                pgdata_allocated_bytes=int(data.split()[0]))


def oracle(done, seq, marker):
    rows = ",".join(f"{i}:{'done' if i <= done else 'ready'}" for i in range(1, ROWS + 1))
    digest = hashlib.md5(rows.encode(), usedforsecurity=False).hexdigest()
    return dict(rows=ROWS, done=done, sequence=seq, marker=marker, table_hash=digest)


def workload(name, database, number, retain, setup_ms, setup_delta):
    before = state(name, database)
    before_counters = counters(name)
    count = number * 10
    end = "COMMIT" if retain else "ROLLBACK"
    started = time.perf_counter()
    output = sql(name, database, f"""
    BEGIN;
    SELECT nextval('task_token');
    UPDATE tasks SET status = 'done' WHERE id <= {count};
    CREATE TABLE trajectory_marker (run integer);
    INSERT INTO trajectory_marker VALUES ({number});
    {STATE_SQL}
    {end};
    SELECT pg_stat_force_next_flush();
    """).splitlines()
    workload_ms = (time.perf_counter() - started) * 1000
    after_counters = counters(name)
    inside = json.loads(output[1])
    after = state(name, database)
    expected_before = oracle(0, [1, False] if retain or number == 1 else [number - 1, True],
                             False)
    seq = 1 if retain else number
    assert before == expected_before
    assert int(output[0]) == seq and inside == oracle(count, [seq, True], True)
    assert after == (inside if retain else oracle(0, [seq, True], False))
    return dict(trajectory=number, initial=before, in_transaction=inside, final=after,
                obtained_sequence=seq, setup_ms=round(setup_ms, 2),
                workload_ms=round(workload_ms, 2), setup_delta=setup_delta,
                workload_delta=delta(before_counters, after_counters),
                **end_storage(name, database))


def main():
    rows = dict(fresh_cluster=[], template_clone=[], rollback_shared=[])
    clean = oracle(0, [1, False], False)
    for number in range(1, TRAJECTORIES + 1):
        started = time.perf_counter()
        with cluster(f"fresh-{number}") as name:
            before = counters(name)
            seed(name)
            setup_ms = (time.perf_counter() - started) * 1000
            rows["fresh_cluster"].append(workload(
                name, BASE, number, True, setup_ms, delta(before, counters(name)),
            ))

    with cluster("clone") as name:
        seed(name)
        for number in range(1, TRAJECTORIES + 1):
            before = counters(name)
            database = f"bird_clone_{number}"
            started = time.perf_counter()
            sql(name, "postgres", f"CREATE DATABASE {database} TEMPLATE {BASE} STRATEGY WAL_LOG;")
            setup_ms = (time.perf_counter() - started) * 1000
            rows["template_clone"].append(workload(
                name, database, number, True, setup_ms, delta(before, counters(name)),
            ))
        assert state(name, BASE) == clean
        retained_clone_allocated_bytes = rows["template_clone"][-1]["pgdata_allocated_bytes"]

    with cluster("rollback") as name:
        seed(name)
        for number in range(1, TRAJECTORIES + 1):
            # Reuses the ready database with zero per-trajectory setup.
            rows["rollback_shared"].append(workload(name, BASE, number, False, 0, None))

    expected_sequences = {"fresh_cluster": [1, 1, 1], "template_clone": [1, 1, 1],
                          "rollback_shared": [1, 2, 3]}
    summary = {}
    for arm, samples in rows.items():
        sequences = [sample["obtained_sequence"] for sample in samples]
        assert sequences == expected_sequences[arm]
        summary[arm] = dict(
            initial_state_matches=sum(sample["initial"] == clean for sample in samples),
            obtained_sequence=sequences,
            setup_ms_median=median(sample["setup_ms"] for sample in samples),
            workload_ms_median=median(sample["workload_ms"] for sample in samples),
            workload_wal_bytes_median=median(sample["workload_delta"]["wal_bytes"]
                                             for sample in samples),
        )
    print(json.dumps(dict(image=IMAGE, postgres_version="18.7", trajectories_per_arm=TRAJECTORIES,
                          seed_rows=ROWS, clone_template_unchanged=True,
                          retained_clone_allocated_bytes=retained_clone_allocated_bytes,
                          summary=summary, samples=rows), indent=2))


if __name__ == "__main__":
    main()
