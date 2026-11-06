#!/usr/bin/env python3
"""Local synthetic-only oracle, source-graph, and OOD regression tests."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def load(filename, name):
    spec=importlib.util.spec_from_file_location(name,ROOT/filename)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


m=load("2026-11-06-drag-abstention-multihop-ab.py","evidence_lab")
stress=load("2026-11-06-drag-evidence-ood-stress.py","evidence_stress")


class EvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bm,cls.docs,cls.queries,cls.wrong,cls.sha=m.prepare(
            20261120,"calibration")

    def one(self,kind):
        return next(q for q in self.queries if q["class"]==kind)

    def run_arm(self,kind,arm="gate_follow"):
        return m.run_query(arm,self.bm,self.docs,self.one(kind),1.0,self.wrong)[0]

    def test_link_ids_with_hyphens(self):
        q=self.one("linked_pair")
        selected=[self.bm.documents[i]["id"]
                  for i in self.bm.ranked(q["query"])[:3]]
        anchor=m.gate_candidate(self.docs,selected,q["query"],1.0)
        self.assertEqual(anchor,q["gold"][0])
        self.assertEqual(m.linked_document(self.docs,anchor),q["gold"][1])

    def test_absent_broken_and_wrong_rejected(self):
        for group in ("absent","cross_pair","missing_link","wrong_link"):
            with self.subTest(kind=group):
                self.assertEqual(self.run_arm(group),[])

    def test_correct_link_and_wrong_link_control(self):
        q=self.one("linked_pair")
        self.assertEqual(set(self.run_arm("linked_pair")),set(q["gold"]))
        self.assertFalse(set(q["gold"]).issubset(
            set(self.run_arm("linked_pair","wrong_link_control"))))

    def test_gold_mutation_changes_oracle_not_retrieval(self):
        q=self.one("single")
        pred=self.run_arm("single")
        good=m.summarize([q],{q["id"]:{"docs":pred}})
        mutated=dict(q,gold=["document-not-present"])
        bad=m.summarize([mutated],{q["id"]:{"docs":pred}})
        self.assertEqual(good["recall_at3"],1.0)
        self.assertEqual(bad["recall_at3"],0.0)

    def test_same_seed_reproducible(self):
        self.assertEqual(self.sha,m.prepare(20261120,"calibration")[4])

    def test_format_shift_preserves_bm25(self):
        originals,questions=m.case_fixture(20261231,"holdout")
        before=m.BM25(originals)
        after=m.BM25(stress.mutate(originals,"format_shift"))
        for q in questions:
            self.assertEqual(
                [before.documents[i]["id"] for i in before.ranked(q["query"])[:3]],
                [after.documents[i]["id"] for i in after.ranked(q["query"])[:3]])

    def test_spoofed_evidence_breaks_model(self):
        run=stress.run_one(20261231,1.0)
        self.assertLess(
            run["mutations"]["forged_observation"]["arms"]["gate_follow"]["citation_precision"],
            1.0)


if __name__=="__main__":
    unittest.main()
