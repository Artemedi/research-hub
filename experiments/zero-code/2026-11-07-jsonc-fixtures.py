#!/usr/bin/env python3
"""Deterministic, independently gold-labeled synthetic JSONC corpus.

Constructs valid JSONC using only grammar-valid punctuation and comments; gold
comes from Python standard JSON values. No external source or user data.
"""
import hashlib
import json
import os
from pathlib import Path
import random

OUTPUT = Path(os.environ["OUTPUT"])
SEED = 20261107
STYLES = ("plain", "block", "line-lf", "line-crlf", "trailing", "mixed")


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def jsonvalue(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def spaced_comment(style, number):
    if style == "block":
        return "/*label:" + str(number) + "*/ "
    if style == "line-lf":
        return "// line-label " + str(number) + "\n "
    if style == "line-crlf":
        return "// line-label " + str(number) + "\r\n "
    if style == "mixed":
        return "/* before \r\n value " + str(number) + " */ "
    return ""


def render(value, style, ordinal, depth=0):
    if isinstance(value, dict):
        fragments = []
        for k, v in value.items():
            fragments.append(jsonvalue(k) + ":" + spaced_comment(style, ordinal) +
                             render(v, style, ordinal, depth + 1))
        separator = ", " + spaced_comment(style, ordinal)
        trailing = "," if style in ("trailing", "mixed") and fragments else ""
        return "{" + spaced_comment(style, ordinal) + separator.join(fragments) + trailing + "}"
    if isinstance(value, list):
        fragments = [render(v, style, ordinal, depth + 1) for v in value]
        separator = "," + spaced_comment(style, ordinal)
        trailing = "," if style in ("trailing", "mixed") and fragments else ""
        return "[" + spaced_comment(style, ordinal) + separator.join(fragments) + trailing + "]"
    return jsonvalue(value)


def corpus():
    rng = random.Random(SEED)
    special = (
        "https://example.invalid/a//b",
        "/* visible text */ // untouched",
        'escaped " quote, } bracket',
        r"C:\\vendor\\tools\\config",
        "Русский текст, отрицание: НЕ запускать",
        "emoji 🐈 and slash /",
        "backslash and newline: \\n",
        "unicode \\u2028 literal",
    )
    valid = []
    for index in range(20):
        item = {
            "id": index,
            "url": special[index % len(special)],
            "label": special[(index + 3) % len(special)],
            "flag": index % 2 == 0,
            "count": rng.randrange(-5000, 5000),
            "array": [0, index, None, {"inner": special[(index + 5) % len(special)]}],
            "nested": {"zero": 0, "empty": [], "empty-object": {},
                       "slash": "//", "block": "/* */"},
        }
        for style in STYLES:
            variant = render(item, style, index)
            if style == "line-lf":
                variant = "// top of file\n" + variant + "\n// end of file"
            elif style == "line-crlf":
                variant = "// top of file\r\n" + variant + "\r\n// end of file"
            elif style == "mixed":
                variant = "/* header */\n" + variant + "\n/* EOF */"
            valid.append({
                "id": f"v-{index:02}-{style}",
                "text": variant,
                "expected": item,
                "canonical_sha256": sha(jsonvalue(item)),
                "input_sha256": sha(variant),
            })
    invalid_samples = [
        '{"a":', '/* never closed', '{"a":"unfinished}', '{a:1}',
        '[1,,2]', '{"a":1,,}', '{"a": 1/*', '{"a":1} unexpected',
        '{"a":NaN}', '{"a":Infinity}', "{'a':1}", '{"a":undefined}',
        '[1,2,,]', '{"a":+1}', '{"a": 01}', '{"a":.5}',
        '{"a": 1e}', '{"a": True}', '["a",, "b"]', '{"x": "bad\\q"}',
        '// comment only', '[]/* missing', '{"a":1, "b"}', '{"a":[1,2}',
    ]
    invalid = [{"id": f"x-{i:02}", "text": string, "input_sha256": sha(string)}
               for i, string in enumerate(invalid_samples)]
    duplicate = '{"model":"safe","model":"override"}'
    return {
        "seed": SEED,
        "source_purpose": "synthetic JSONC input, no secrets",
        "valid_count": len(valid), "invalid_count": len(invalid),
        "valid": valid, "invalid": invalid,
        "ambiguous_duplicate": {
            "text": duplicate, "input_sha256": sha(duplicate),
            "expected_json_parse_last_wins": {"model": "override"}
        }
    }


def main():
    value = corpus()
    assert len(value["valid"]) == 120 and len(value["invalid"]) == 24
    for row in value["valid"]:
        assert row["canonical_sha256"] == sha(jsonvalue(row["expected"]))
        assert row["input_sha256"] == sha(row["text"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "valid": len(value["valid"]), "invalid": len(value["invalid"]),
        "fixture_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    }))


if __name__ == "__main__":
    main()
