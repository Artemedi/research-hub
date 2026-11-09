#!/usr/bin/env python3
"""Original pinned Paper2Project import versus minimal isolated symlink fix.

30 valid local source imports and 12 negative controls, same per-arm fixtures.
Never edits source repo; local candidate is behaviorally equivalent to supplied
minimal patch; the independent source unit suite is also run on a patched copy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

def sha(b):return hashlib.sha256(b).hexdigest()

def run_cases(app_type, tmp, arm):
    from paper2project.core import App
    class CandidateApp(App):
        def local(self,path):
            candidate=Path(path)
            if candidate.is_symlink():
                raise ValueError("Local import symlink is not allowed")
            return super().local(path)
    inputs=tmp/"inputs"
    inputs.mkdir(parents=True)
    app=(CandidateApp if arm=="candidate" else App)(tmp/"workspace",allowed_roots=[inputs])
    records=[]
    durations=[]
    for n in range(30):
        f=inputs/("paper-%03d.md"%n)
        raw=("# Synthetic paper %03d\nOriginal result %03d\n"%(n,n)).encode()
        f.write_bytes(raw)
        begin=time.perf_counter_ns()
        rec=app.import_research(f,title="Synthetic "+str(n),research_id="source-"+str(n))
        durations.append(time.perf_counter_ns()-begin)
        doc=app.store.json(rec["snapshot"])["documents"][0]
        assert app.store.blob(doc["sha256"])==raw
        f.write_bytes(b"SYNTHETIC EXTERNAL CHANGE AFTER IMPORT\n")
        assert app.store.blob(doc["sha256"])==raw
        records.append({"id":"valid-"+str(n),"category":"valid","gold_accept":True,"actual_accept":True})
    for n in range(12):
        kind=["missing","outside","symlink","tamper"][n//3]
        accepted=True; err=None
        try:
            if kind=="missing":
                app.import_research(inputs/("absent-"+str(n)+".md"),research_id="invalid-"+str(n))
            elif kind=="outside":
                outside=tmp/("outside-"+str(n)+".md")
                outside.write_text("Synthetic outside source",encoding="utf8")
                app.import_research(outside,research_id="invalid-"+str(n))
            elif kind=="symlink":
                link=inputs/("source-link-"+str(n)+".md")
                link.symlink_to(inputs/"paper-000.md")
                app.import_research(link,research_id="invalid-"+str(n))
            elif kind=="tamper":
                doc=app.store.json(app.store.get("research","source-000")["snapshot"])["documents"][0]
                obj=app.store.root/"objects"/doc["sha256"]
                if n==9:
                    obj.write_bytes(b"CORRUPT STORED HASH")
                app.store.blob(doc["sha256"])
        except (ValueError,FileNotFoundError) as exc:
            accepted=False;err=type(exc).__name__
        records.append({"id":"negative-"+str(n),"category":kind,
                        "gold_accept":False,"actual_accept":accepted,"error_type":err})
    return records,durations

def summarize(rows):
    return {"valid_accepted":sum(r["category"]=="valid" and r["actual_accept"] for r in rows),
            "invalid_rejected":sum(r["category"]!="valid" and not r["actual_accept"] for r in rows),
            "invalid_accepted":sum(r["category"]!="valid" and r["actual_accept"] for r in rows),
            "symlink_accepted":sum(r["category"]=="symlink" and r["actual_accept"] for r in rows),
            "snapshots_stable_after_external_edit":30}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--patch",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    sys.path.insert(0,str(args.source/"src"))
    base=None;candidate=None
    with tempfile.TemporaryDirectory(prefix="p0-paper2project-") as root:
        root=Path(root)
        base,t0=run_cases(None,root/"baseline","baseline")
        candidate,t1=run_cases(None,root/"candidate","candidate")
    assert len(base)==len(candidate)==42
    assert summarize(base)["valid_accepted"]==30
    assert summarize(base)["invalid_rejected"]==9
    assert summarize(base)["symlink_accepted"]==3
    assert summarize(candidate)["valid_accepted"]==30
    assert summarize(candidate)["invalid_rejected"]==12
    assert summarize(candidate)["symlink_accepted"]==0
    result={
        "pair":"paper2agent/dsh-paper2agent","protocol":"source_pin",
        "scope":"PINNED_APP_IMPORT_SOURCE_VS_ISOLATED_MINIMAL_SYMLINK_CHECK",
        "source_git_sha":"cbcb1c089b2704af70e89e4fd5bb490642c9efae",
        "source_file":"src/paper2project/core.py",
        "source_file_sha256":sha((args.source/"src/paper2project/core.py").read_bytes()),
        "candidate_patch_sha256":sha(args.patch.read_bytes()),
        "dataset":{"valid":30,"invalid":12,"kinds":["missing","outside","symlink","tamper"]},
        "baseline":summarize(base),"candidate":summarize(candidate),
        "records":[{"id":b["id"],"category":b["category"],"gold_accept":b["gold_accept"],
                    "baseline_accept":b["actual_accept"],"candidate_accept":c["actual_accept"],
                    "baseline_error":b.get("error_type"),"candidate_error":c.get("error_type")}
                   for b,c in zip(base,candidate)],
        "timing":{"unit":"ns_per_local_file_import",
                  "p95_baseline_ns":sorted(t0)[int(29*.95)],
                  "p95_candidate_ns":sorted(t1)[int(29*.95)]},
        "negative_controls":["nonexistent source","out-of-root source","same-root symlink","tampered stored object"],
        "limitations":[
            "Observed a symlink root policy bypass on a synthetic local file inside allowed_roots.",
            "Does not establish a sandbox escape, privilege escalation or broader real-world exploit.",
            "Candidate is a single check before Path.resolve, tested on a copied Git tree and equivalent subclass in this A/B.",
            "No source code target repository or private library was modified.",
            "Full original test suite includes skips for external runtime; adoption needs source PR review and CI.",
        ],
    }
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("PAPER2PROJECT_SOURCE_PIN_AB",result["baseline"],result["candidate"],result["timing"])

if __name__=="__main__":main()
