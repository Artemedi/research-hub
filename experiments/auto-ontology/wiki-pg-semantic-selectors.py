"""Compare literal and curated terminology before an exact Wiki_PG evidence query."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
ALPHA, BETA = "FixtureAlpha", "FixtureBeta"
ALIAS_A, ALIAS_B = "Учебный-Альфа", "Учебный-Бета"
EARLY, LATE = "2026-11-23T00:00:00Z", "2026-11-25T00:00:00Z"
FIELDS = {"work_mem", "shared_buffers"}
TERMS = {
    "рабочая память": ("work_mem",),
    "общие буферы": ("shared_buffers",),
    "память": ("shared_buffers", "work_mem"),
}


def capture(root, host, stamp, values):
    path = root / "raw/sysconfig-report/fixture" / host / (stamp.replace(":", "-") + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "report_meta": {"timestamp_utc": stamp, "script_version": "fixture"},
        "postgres_settings": {"instances": [{"port": "5432", "settings": [
            {"name": name, "setting": str(value), "unit": "kB"}
            for name, value in values.items()
        ]}]},
    }), encoding="utf-8")
    return path


def query_state(service, host, port, field):
    result = service.state(host, scope="pg_setting", port=port, fields=[field], at=LATE)
    if not result["data"] or result["data"][0]["status"] == "missing":
        return None, "missing"
    row, = result["data"]
    source, = result["sources"]
    return (int(row["value_num"]), result["scope"]["host"], result["scope"]["port"],
            source["observed_at"], source["source_file"], source["sha256"]), "exact"


def select(service, host, port, term, semantic):
    if term in FIELDS:
        return query_state(service, host, port, term)
    matches = TERMS.get(term.strip().casefold(), ()) if semantic else ()
    if not matches:
        return None, "unknown_term"
    if len(matches) != 1:
        return None, "ambiguous_term"
    return query_state(service, host, port, matches[0])


def trial(build, Query, seed):
    with TemporaryDirectory() as folder:
        root = Path(folder)
        registry = root / "operations/clusters/registry.yaml"
        registry.parent.mkdir(parents=True)
        registry.write_text(f"clusters:\n  {ALPHA}: fixture\n  {BETA}: fixture\n"
                            f"aliases:\n  {ALIAS_A}: {ALPHA}\n  {ALIAS_B}: {BETA}\n", encoding="utf-8")
        a_value, b_value = 4096 + seed * 16, 8192 + seed * 16
        capture(root, ALPHA, EARLY, {"shared_buffers": 16384, "work_mem": 2048})
        a = capture(root, ALPHA, LATE, {"work_mem": a_value})
        b = capture(root, BETA, LATE, {"work_mem": b_value, "shared_buffers": 32768})
        if build(root)["state"] != "complete":
            raise AssertionError("Catalogue build failed")

        def oracle(path, host, value):
            return value, host, "5432", LATE, path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()

        cases = {
            "canonical": (ALPHA, "5432", "work_mem", oracle(a, ALPHA, a_value), "exact", "exact"),
            "native_host_alias": (ALIAS_A.lower(), "5432", "work_mem", oracle(a, ALPHA, a_value), "exact", "exact"),
            "business_term": (ALIAS_A, "5432", "РАБОЧАЯ ПАМЯТЬ", oracle(a, ALPHA, a_value), "unknown_term", "exact"),
            "other_host_same_term": (ALIAS_B, "5432", "рабочая память", oracle(b, BETA, b_value), "unknown_term", "exact"),
            "ambiguous_term": (ALIAS_A, "5432", "память", None, "unknown_term", "ambiguous_term"),
            "unknown_term": (ALIAS_A, "5432", "размер журнала", None, "unknown_term", "unknown_term"),
            "missing_without_fallback": (ALIAS_A, "5432", "общие буферы", None, "unknown_term", "missing"),
            "wrong_port": (ALIAS_B, "5433", "рабочая память", None, "unknown_term", "missing"),
        }
        service = Query(root)
        try:
            rows = []
            for case, (host, port, term, expected, literal_status, semantic_status) in cases.items():
                literal = select(service, host, port, term, semantic=False)
                semantic = select(service, host, port, term, semantic=True)
                baseline = expected if literal_status == "exact" else None
                if (literal, semantic) != ((baseline, literal_status), (expected, semantic_status)):
                    raise AssertionError((case, seed, literal, semantic))
                rows.append({"case": case, "literal_decision": literal[1], "semantic_decision": semantic[1],
                             "exact_source_checked": expected is not None})
            return {"fixture": seed, "cases": rows}
        finally:
            service.close()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("wiki_checkout", type=Path)
    source = cli.parse_args().wiki_checkout.resolve()
    git = ["git", "-C", str(source)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != REVISION
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        cli.error(f"Expected clean Wiki_PG checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "Wiki_PG/ingestion"))
    from build_system_store import build
    from system_queries import SystemQueries

    seeds = (2, 4, 11, 14, 19, 23)
    rows = [trial(build, SystemQueries, seed) for seed in seeds]
    if rows != [trial(build, SystemQueries, seed) for seed in seeds]:
        raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_revision": REVISION, "repeat_count": 2, "status": "PASS",
                      "fixtures": rows}, indent=2))


if __name__ == "__main__":
    main()
