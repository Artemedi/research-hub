"""Compare a pinned ID helper with Wiki_PG's handling of synthetic source paths."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

WIKI_REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
YAHONT_REVISION = "367b48da9de2d296f905aca4bf0eb384043bf643"
HELPER_SHA = "511568e3cd0e6b45a81769699b40440b1f77276db26a919aff619977a8e6fea8"


def snapshot(root, search, marker, paths):
    rows = search(root, marker, semantic=False)["chunks"]
    result = {row["source_file"]: row for row in rows}
    if len(rows) != len(paths) or set(result) != set(paths):
        raise AssertionError("Retrieved paths disagree with the independent file list")
    for path, row in result.items():
        data = (root / path).read_bytes()
        if row["sha256"] != sha256(data).hexdigest() or row["text"] != data.decode().rstrip("\n"):
            raise AssertionError("Hit bytes differ from the cited source")
    return result


def trial(build, search, normalize, seed):
    with TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "raw").mkdir()
        first, second = f"operations/item{seed}/part.md", f"operations/item{seed}part.md"
        different = f"operations/item{seed}-part.md"
        if normalize(first) != normalize(second) or normalize(first) == normalize(different):
            raise AssertionError("The original helper disagrees with the path controls")
        marker = f"identityfixture{seed}"
        original = f"# Observation\n{marker} records the initial value.\n"
        for name in (first, second):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(original, encoding="utf-8")

        if build(root)["state"] != "complete":
            raise AssertionError("Initial build failed")
        initial = snapshot(root, search, marker, (first, second))
        if (initial[first]["sha256"] != initial[second]["sha256"]
                or initial[first]["source_id"] == initial[second]["source_id"]):
            raise AssertionError("Different paths were merged")
        scoped, = search(root, marker, source_file=second, semantic=False)["chunks"]
        if scoped["source_id"] != initial[second]["source_id"]:
            raise AssertionError("Explicit source selection returned the wrong document")

        (root / first).write_text(f"# Observation\n{marker} records the revised fixture value.\n", encoding="utf-8")
        if build(root)["state"] != "complete":
            raise AssertionError("Update did not publish a new index")
        updated = snapshot(root, search, marker, (first, second))
        if (updated[first]["source_id"] == initial[first]["source_id"]
                or updated[second]["source_id"] != initial[second]["source_id"]):
            raise AssertionError("The update did not isolate source identity")

        (root / second).unlink()
        if build(root)["state"] != "complete":
            raise AssertionError("Deletion did not publish a new index")
        after = snapshot(root, search, marker, (first,))
        absent = search(root, marker, source_file=second, semantic=False)["chunks"]
        if after[first]["source_id"] != updated[first]["source_id"] or absent:
            raise AssertionError("Removal affected another source or retained the deleted source")
        return {"fixture": seed, "helper_pair_collision": True, "helper_distinct_control": True,
                "wiki_distinct_ids_identical_bytes": True, "scoped_read_preserved_identity": True,
                "only_updated_id_changed": True, "only_deleted_source_disappeared": True}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("wiki_checkout", type=Path)
    cli.add_argument("pinned_yahont_helper", type=Path)
    args = cli.parse_args()
    source = args.wiki_checkout.resolve()
    git = ["git", "-C", str(source)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != WIKI_REVISION
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        cli.error(f"Expected clean Wiki_PG checkout at {WIKI_REVISION}")
    helper = args.pinned_yahont_helper.read_bytes()
    if sha256(helper).hexdigest() != HELPER_SHA:
        cli.error("Yahont helper does not match the reviewed Git blob")
    namespace = {}
    exec(compile(helper, "pinned_yahont_helper", "exec"), namespace)
    normalize = namespace["filter_and_validate_document_id"]
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "Wiki_PG/ingestion"))
    from build_system_store import build
    from evidence_search import search

    rows = [trial(build, search, normalize, seed) for seed in range(1, 11)]
    if rows != [trial(build, search, normalize, seed) for seed in range(1, 11)]:
        raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_revision": WIKI_REVISION, "yahont_revision": YAHONT_REVISION,
                      "yahont_helper_sha256": HELPER_SHA, "repeat_count": 2,
                      "status": "OBSERVED", "fixtures": rows}, indent=2))


if __name__ == "__main__":
    main()
