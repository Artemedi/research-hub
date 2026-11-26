"""Compare raw Markdown markers and source-verified warning blocks in Wiki_PG."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
MARKER = "[!WARNING]"
HOST, PORT = "FixtureHost", "5432"
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
INSTANCE = re.compile(r"^### Инстанс на порту (\d+)$")
CASES = {
    # Marker in indexed fragment, warning in current source.
    "same_fragment": (True, True),
    "instance_header": (False, True),
    "other_instance": (False, False),
    "inline_sample": (True, False),
    "backtick_sample": (True, False),
    "tilde_sample": (True, False),
    "ordinary_note": (False, False),
    "changed_source": (True, False),
}


def visible_lines(lines):
    fence = None
    for line in lines:
        mark = FENCE.match(line)
        if fence:
            if (mark and mark[1][0] == fence[0] and len(mark[1]) >= len(fence)
                    and not mark[2].strip()):
                fence = None
            yield ""
        elif mark:
            fence = mark[1]
            yield ""
        else:
            yield line


def cue(root, row):
    payload = (root / row["source_file"]).read_bytes()
    if sha256(payload).hexdigest() != row["sha256"]:
        return None, "source_changed"
    lines = payload.decode("utf-8").splitlines()
    beginning, end = map(int, row["location"].removeprefix("lines:").split("-"))
    if "\n".join(lines[beginning - 1:end]) != row["text"] or row["pg_port"] != PORT:
        raise AssertionError("Indexed fragment disagrees with its citation or scope")
    visible = list(visible_lines(lines))
    # An instance-wide notice is allowed only in the matching instance's opening block.
    for i in range(beginning - 1, -1, -1):
        scope = INSTANCE.match(visible[i])
        if scope or visible[i].startswith("## "):
            break
    else:
        return None, "outside_instance"
    if not scope or scope[1] != PORT:
        return None, "outside_instance"
    stop = next((j for j in range(i + 1, end) if visible[j].startswith("#")), end)
    allowed = set(range(i + 1, stop)) | set(range(beginning - 1, end))
    for j in sorted(allowed):
        if (visible[j].strip() == "> " + MARKER and j + 1 in allowed
                and visible[j + 1].startswith("> ")):
            return {"type": "warning", "text": visible[j + 1][2:],
                    "source_file": row["source_file"], "sha256": row["sha256"],
                    "location": f"lines:{j + 1}-{j + 2}"}, "verified"
    return None, "no_warning_block"


def source_text(case, query, notice):
    top = "**Date:** 2026-11-25T00:00:00Z\n## PostgreSQL\n"
    instance, fact = f"### Инстанс на порту {PORT}\n", f"#### Observation\n{query} is 4.\n"
    warning = f"> {MARKER}\n> {notice}\n"
    if case == "instance_header":
        return top + instance + warning + fact
    if case == "other_instance":
        return top + "### Инстанс на порту 5433\n" + warning + instance + fact
    if case in {"same_fragment", "changed_source"}:
        return top + instance + fact + warning
    if case == "inline_sample":
        return top + instance + fact + f"Example: `{MARKER}`.\n"
    if case in {"backtick_sample", "tilde_sample"}:
        delimiter = "```" if case == "backtick_sample" else "~~~~"
        return top + instance + fact + delimiter + "text\n" + warning + delimiter + "\n"
    return top + instance + fact + warning.replace(MARKER, "[!NOTE]")


def trial(build, search, seed):
    with TemporaryDirectory() as folder:
        root = Path(folder)
        registry = root / "operations/clusters/registry.yaml"
        registry.parent.mkdir(parents=True)
        registry.write_text(f"clusters:\n  {HOST}: fixture\n", encoding="utf-8")
        directory = root / "raw/deep-report/fixture" / HOST
        directory.mkdir(parents=True)
        notice = f"Confirm the observation against fixture {seed}."
        paths = {}
        for case in CASES:
            path = directory / (case + ".md")
            path.write_text(source_text(case, case.replace("_", "") + str(seed), notice), encoding="utf-8")
            paths[case] = path
        build(root)

        rows = []
        for case, expected in CASES.items():
            query = case.replace("_", "") + str(seed)
            row, = search(root, query, host=HOST, port=PORT, semantic=False)["chunks"]
            native_typed = bool({"warning", "severity", "admonition", "cue", "formatting"} & row.keys())
            if native_typed or row["source_file"] != paths[case].relative_to(root).as_posix():
                raise AssertionError("Unexpected native cue contract or source")
            if case == "changed_source":
                paths[case].write_text(source_text(case, query, "The source is now revised."), encoding="utf-8")
            item, reason = cue(root, row)
            marker = MARKER in row["text"]
            if (marker, bool(item)) != expected or (item and item["text"] != notice):
                raise AssertionError((case, seed, marker, item, reason))
            if case == "changed_source" and reason != "source_changed":
                raise AssertionError("Changed source bypassed the citation check")
            rows.append({"case": case, "native_raw_marker": marker, "native_typed_cue": native_typed,
                         "verified_warning": bool(item), "decision": reason})
        return {"fixture": seed, "cases": rows}


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
    from evidence_search import search

    seeds = (2, 4, 11, 14, 19, 23)
    rows = [trial(build, search, seed) for seed in seeds]
    if rows != [trial(build, search, seed) for seed in seeds]:
        raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_revision": REVISION, "repeat_count": 2, "status": "PASS",
                      "fixtures": rows}, indent=2))


if __name__ == "__main__":
    main()
