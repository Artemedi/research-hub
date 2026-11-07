#!/usr/bin/env python3
"""Second independent full-HTML fixture set, reusing the pinned target-path A/B.

Labels are authored prior to ZCode calls; not independent human annotation.
Requires exact HTML bytes and the existing source-anchored runner beside it.
"""
import importlib.util
from pathlib import Path

baseline = Path(__file__).with_name("2026-11-07-source-anchored-citation-ab.py")
spec = importlib.util.spec_from_file_location("pinned_source_citation_runner", baseline)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.PINS = {
    "2609.40111": "31af8d0a1d4da3a4c4184def8fed7e6f76a6483005804f0868133b682d7aab14",
    "2609.11028": "36ae9bbdd32fb65d502a9644f7e2905b166cdc620d843b8724ce47b510da74b6",
}
_original_source_paragraph = runner.source_paragraph


def one_line_source_paragraph(html, heading, needle):
    anchor, paragraph = _original_source_paragraph(html, heading, needle)
    # Source HTML sometimes contains embedded newlines within a paragraph.
    # Citation start/end refer to *snapshot lines*, so canonicalize whitespace.
    return anchor, " ".join(paragraph.split())


runner.source_paragraph = one_line_source_paragraph
runner.FIXTURES = [
    ("aed-pipeline", "2609.40111", "3.2 AET: a five-stage data generation pipeline",
     "AET connects five stages", [
        ("AET connects five stages", True, "direct"),
        ("Where supported, replay checks a proposed correction from the same checkpoint with matched policy and verifier settings", True, "paraphrase"),
        ("AET contains only three stages, ending before correction replay", False, "wrong_count"),
        ("Replay requires a new checkpoint with deliberately changed policy settings", False, "wrong_protocol"),
    ]),
    ("aed-limits", "2609.40111", "Appendix A Limitations and Reproducibility",
     "Collection size counts error–diagnosis pairs", [
        ("Collection size counts error–diagnosis pairs; it does not count independent executions or training-ready examples", True, "direct"),
        ("The number of error–diagnosis pairs is not the number of independent runs", True, "paraphrase"),
        ("Each error–diagnosis pair represents an independent execution", False, "wrong_denominator"),
        ("All collected error–diagnosis pairs are certified training-ready examples", False, "unsupported_extrapolation"),
    ]),
    ("aed-multiplicity", "2609.40111", "Appendix B Dataset analysis and corrective evidence",
     "Multiple diagnoses add 11,950", [
        ("Multiple diagnoses add 11,950 pairs beyond one per source blob", True, "direct"),
        ("The extra 11,950 diagnosis pairs are not new independent failure observations", True, "paraphrase"),
        ("There are 11,950 additional independent failures proven by the extra diagnoses", False, "wrong_denominator"),
        ("Each source blob has exactly one diagnosis", False, "wrong_multiplicity"),
    ]),
    ("aed-machine-judges", "2609.40111", "G.1 Independent labeling-method study",
     "The two machine judges agree on 154 / 357", [
        ("The two machine judges agree on 154 / 357 modes", True, "direct"),
        ("Of 357 jointly classified cases, the two machine judges assigned the same failure mode in 154", True, "paraphrase"),
        ("The machine judges agreed on all 357 cases", False, "wrong_number"),
        ("The published 154-of-357 agreement is between two human annotators", False, "wrong_actor"),
    ]),
    ("bench-events", "2609.11028", "3.3. Pipeline",
     "Second, trusted probes emit an authority-bearing structural event stream", [
        ("Structural events update lifecycle conformance", True, "direct"),
        ("Audit agents may help interpret evidence without replacing the structural event stream", True, "paraphrase"),
        ("Audit-agent outputs replace the trusted structural events as the authoritative trace", False, "wrong_authority"),
        ("Trusted probes collect no supporting host observations", False, "negation"),
    ]),
    ("bench-trials", "2609.11028", "6.3. RQ2",
     "receive the same pinned, stripped package", [
        ("Both systems receive the same pinned, stripped package and are run for five trials each", True, "direct"),
        ("BenchShield and BenchJack were compared on identical pinned packages with five runs each", True, "paraphrase"),
        ("BenchJack was evaluated on a different task package than BenchShield", False, "wrong_control"),
        ("The RQ2 comparison used a single run per system", False, "wrong_count"),
    ]),
    ("bench-lifecycle-limit", "2609.11028", "7. Discussion",
     "The finite, event-based lifecycle tracks reward-relevant transitions", [
        ("The finite, event-based lifecycle tracks reward-relevant transitions rather than every file, command, or packet", True, "direct"),
        ("The lifecycle abstracts reward-related events, rather than logging every command and packet", True, "paraphrase"),
        ("The lifecycle tracks every file, command, and packet", False, "overclaim"),
        ("The model proves mount and network security without evidence from the backend", False, "unsupported_extrapolation"),
    ]),
    ("bench-control-plane", "2609.11028", "Appendix D A vector below the benchmark",
     "verifier’s validity gate later rejected the placement", [
        ("The verifier’s validity gate later rejected the placement, so the reward is 0.0", True, "direct"),
        ("The sandbox boundary was crossed, but the measured reward remained zero after rejection", True, "paraphrase"),
        ("The boundary crossing increased the measured task reward above zero", False, "wrong_outcome"),
        ("The task explicitly declared and authorized the control-plane handoff channel", False, "wrong_scope"),
    ]),
]
assert len(runner.FIXTURES) == 8

if __name__ == "__main__":
    runner.main()
