"""Measure authored tool-schema JSON with the DSH estimate and two local tokenizers."""
import argparse
from itertools import product, takewhile
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import tiktoken

COMMIT = "b6a1635b1200071754e2871b9d9453368e6daf23"
VOCABS = ("cl100k_base", "o200k_base")
DESCRIPTIONS = {
    "en": "Return one synthetic report for the requested period with optional comparison.",
    "ru": "Вернуть сводку измерений за период с возможностью сравнения.",
    "zh": "返回指定时间段的合成测量摘要，并可选择比较两个时间窗口。",
}


def schema(name, description):
    return dict(type="function", function=dict(
        name=name, description=description, parameters=dict(
            type="object", additionalProperties=False, required=["period"],
            properties=dict(period=dict(type="string", description="Fixture period"),
                            compare=dict(type="boolean", description="Include a comparison")),
        ),
    ))


def fixtures():
    for size, (language, description) in product((4, 12, 24), DESCRIPTIONS.items()):
        key = f"{language}-{size}"
        catalog = [schema(f"fixture_{i:02d}", description) for i in range(size)]
        finder = schema("find_fixture", "Return the schema name for a known fixture report.")
        core = [*catalog[:2], finder]
        rare = catalog[-1]
        prefix = [
            dict(role="system", content="Use the listed tools to assemble the synthetic report."),
            dict(role="user", content="Return the requested fixture report for the current period."),
        ]
        discovery_call = dict(role="assistant", content="Find the requested fixture report.")
        discovery_result = dict(role="tool", content=f"Schema available: {rare['function']['name']}.")
        variants = {
            "static": (catalog, prefix),
            "reordered": (list(reversed(catalog)), prefix),
            "stable_reorder": (sorted(reversed(catalog), key=lambda t: t["function"]["name"]), prefix),
            "first": (core, prefix),
            "retry": ([*core, rare], [*prefix, discovery_call, discovery_result]),
        }
        for label, (tools, messages) in variants.items():
            yield dict(id=f"{key}/{label}", tools=tools, messages=messages)


def measure(documents, encoder):
    encode = encoder.encode_ordinary
    groups = {}
    for case in documents:
        group, name = case["id"].split("/")
        groups.setdefault(group, {})[name] = (
            case["estimate_schema_tokens"], len(encode(case["schemas"])),
            encode(case["request"]),
        )
    result = {}
    for group, variants in groups.items():
        estimate, schema_count, full = variants["static"]
        _, _, first = variants["first"]
        _, _, retry = variants["retry"]
        reorder = variants["reordered"][2]
        stable = variants["stable_reorder"][2]
        matching = sum(1 for _ in takewhile(lambda pair: pair[0] == pair[1], zip(full, reorder)))
        assert full == stable
        assert matching < len(full)
        result[group] = dict(
            estimated_schema_tokens=estimate, local_schema_tokens=schema_count,
            estimate_minus_local=estimate - schema_count, static_request=len(full),
            staged_common_request=len(first), staged_rare_requests=len(first) + len(retry),
            common_saving=len(full) - len(first),
            rare_saving=len(full) - len(first) - len(retry),
            changed_order_prefix_tokens=matching, stable_order_prefix_tokens=len(stable),
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dsh_source", type=Path)
    args = parser.parse_args()
    source = args.dsh_source.resolve()

    def git(*items):
        return subprocess.check_output(["git", "-C", str(source), *items], text=True).strip()

    if git("rev-parse", "HEAD") != COMMIT or git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Use a clean DSH Runtime checkout at " + COMMIT)
    js = Path(__file__).resolve().with_name("schema-variants.mjs")
    data = json.dumps(list(fixtures()))
    first = subprocess.check_output(["node", str(js), str(source)], input=data,
                                    text=True, encoding="utf-8")
    assert subprocess.check_output(["node", str(js), str(source)], input=data,
                                   text=True, encoding="utf-8") == first
    parsed = json.loads(first)
    # A missing vocabulary must fail rather than fetching during the experiment.
    with patch("requests.get", side_effect=RuntimeError("Prepare both vocabularies first")):
        results = {name: measure(parsed["documents"], tiktoken.get_encoding(name))
                   for name in VOCABS}
    assert all(group["en-4"]["rare_saving"] < 0 for group in results.values())
    assert all(group["en-24"]["rare_saving"] > 0 for group in results.values())
    assert all(group["ru-24"]["common_saving"] > 0 for group in results.values())
    print(json.dumps(dict(dsh_commit=COMMIT, node=parsed["node"], tiktoken=tiktoken.__version__,
                          provider_requests=0, results=results), indent=2))


if __name__ == "__main__":
    main()
