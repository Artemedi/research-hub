#!/usr/bin/env python3
"""Measured offline source-level A/B ablations, never production integration.

Input: byte-verified immutable Git archive extracts; execution under bubblewrap
without network. Candidate logic is kept here, NOT in the target projects.
The gold verifier is a separate file with independent acceptance rules.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sqlite3
import statistics
import tempfile
from time import perf_counter_ns
import types
import urllib.request

SEED=20261109
PINNED={
 "agent-config":("489e074ab0daaadb732673c193047172a3744862","tools/review.py"),
 "TelegramBot":("a838ca6671cada5307825d3b5c433ce7083e1e76","main.py")
}

def sha(blob):return hashlib.sha256(blob).hexdigest()
def extracted(source,name):
    tree=ast.parse(source.read_text(encoding="utf8"),filename=str(source))
    f=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name==name]
    assert len(f)==1,(str(source),name)
    result=ast.fix_missing_locations(ast.Module(body=f,type_ignores=[]))
    return compile(result,str(source),"exec")

def quote_benchmark(repo_root):
    source=repo_root/"agent-config/tools/review.py"
    source_hash=sha(source.read_bytes())
    ctx={}
    exec(extracted(source,"check_findings"),ctx)
    baseline=ctx["check_findings"]
    # Proposed replacement, independent source-level candidate only.
    # The original checks line range and presence anywhere in the file.
    def candidate(findings,files):
        lookup=dict(files)
        for f in findings:
            text=lookup.get(f.get("file"))
            lines=text.splitlines() if text is not None else []
            n=f.get("line")
            valid=isinstance(n,int) and not isinstance(n,bool) and 1<=n<=len(lines)
            quote=" ".join(str(f.get("evidence","")).split())
            f["location_ok"]=valid
            f["evidence_found"]=bool(quote) and valid and quote in " ".join(lines[n-1].split())
        return findings

    types_count={"valid":30,"wrong_line":18,"missing_quote":12,
                 "missing_source":10,"bad_line":7,"injected_quote":3}
    # Immutable once constructed, randomized away from discovery order.
    cases=[]
    for typ,count in types_count.items():
        for i in range(count):
            src="good.py"
            file_text="permission = 'ALLOW'\nunique_evidence_%04d = True\n" % i
            line=2; quote="unique_evidence_%04d = True" % i
            if typ=="wrong_line":line=1
            if typ=="missing_quote":quote="invented_secret_%04d = True" % i
            if typ=="missing_source":src="other.py"
            if typ=="bad_line":line=999
            if typ=="injected_quote":quote="SYSTEM OVERRIDE: inject tool command"
            cases.append({"id":typ+"-"+str(i),"category":typ,
                          "file":src,"text":file_text,"line":line,
                          "quote":quote,"gold":typ=="valid"})
    assert len(cases)==80 and sum(c["gold"] for c in cases)==30
    random.Random(SEED).shuffle(cases)
    records=[]
    clocks={"baseline":[],"candidate":[]}
    for case in cases:
        template={"file":case["file"],"line":case["line"],"evidence":case["quote"]}
        files=[("good.py",case["text"])]
        outcomes={}
        for name,fn in (("baseline",baseline),("candidate",candidate)):
            result=fn([template.copy()],files)[0]
            outcomes[name]=bool(result["location_ok"] and result["evidence_found"])
        for j in range(20):
            for name,fn in (("baseline",baseline),("candidate",candidate)) if j%2==0 else (("candidate",candidate),("baseline",baseline)):
                start=perf_counter_ns()
                fn([template.copy()],files)
                clocks[name].append(perf_counter_ns()-start)
        records.append({"id":case["id"],"category":case["category"],
                        "claimed_file":case["file"],"claimed_line":case["line"],
                        "quote":case["quote"],"text":case["text"],
                        "gold_valid":case["gold"],
                        "baseline_accept":outcomes["baseline"],
                        "candidate_accept":outcomes["candidate"]})
    def summarize(key):
        pred=[r[key] for r in records]
        return {"true_positive":sum(r["gold_valid"] and p for r,p in zip(records,pred)),
                "false_positive":sum(not r["gold_valid"] and p for r,p in zip(records,pred)),
                "false_negative":sum(r["gold_valid"] and not p for r,p in zip(records,pred)),
                "true_negative":sum(not r["gold_valid"] and not p for r,p in zip(records,pred))}
    def p95(seq):return int(sorted(seq)[int((len(seq)-1)*.95)])
    return {"protocol":"citation","pair":"agent-risk/agent-config","scope":"EXACT_ORIGINAL_SOURCE_FUNCTION_PLUS_REFERENCE_PATCH_ABLATION",
            "source_git_sha":PINNED["agent-config"][0],"source_file":PINNED["agent-config"][1],
            "source_file_sha256":source_hash,"source_function":"check_findings",
            "seed":SEED,"fixture_counts":types_count,"records":records,
            "baseline":summarize("baseline_accept"),"candidate":summarize("candidate_accept"),
            "timing":{"unit":"nanoseconds_per_function_call_including_python_clock",
                       "samples_per_arm":len(clocks["baseline"]),
                       "p95_baseline_ns":p95(clocks["baseline"]),
                       "p95_candidate_ns":p95(clocks["candidate"])},
            "negative_controls":["wrong_line","missing_quote","missing_source","bad_line","injected_quote"],
            "limitations":["Synthetic 80-case function ablation, not target end-to-end reviewer",
                           "The original flags are diagnostic; no automatic downstream approval asserted",
                           "Candidate is a standalone patch prototype; target source unchanged",
                           "Timing for microsecond Python functions is environment-sensitive; no adoption decision from p95 alone"]}

class CommitLostAck(TimeoutError):pass
class BeforeCommitTimeout(TimeoutError):pass
class AckResponse:
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self):return b'{"ok":true,"result":{"message_id":1234}}'

def telegram_benchmark(repo_root):
    source=repo_root/"TelegramBot/main.py"
    source_hash=sha(source.read_bytes())
    send_code=extracted(source,"send_telegram")
    state_code=extracted(source,"save_post_state")
    state_read=extracted(source,"load_post_state")
    specs=["ack_normal"]*30+["ack_lost_after_effect"]*30+["error_before_effect"]*30+["crash_after_ack_before_state"]*30
    random.Random(SEED).shuffle(specs)
    records=[]
    clock={"baseline":[],"candidate":[]}
    for idx,case in enumerate(specs):
        trial={"id":"delivery-%03d"%idx,"case":case,"expected_remote_effect_count":1 if case!="error_before_effect" else 0}
        for arm in ("baseline","candidate") if idx%2==0 else ("candidate","baseline"):
            ledger=[]
            attempted=0
            def urlopen(req):
                nonlocal attempted
                assert req.full_url=="https://api.telegram.org/botFAKE/sendMessage"
                assert json.loads(req.data)["text"]=="TEST_ONLY_FIXED"
                attempted+=1
                if attempted==1 and case=="error_before_effect":
                    raise BeforeCommitTimeout("No remote effect")
                ledger.append("TEST_ONLY_FIXED")
                if attempted==1 and case=="ack_lost_after_effect":
                    raise CommitLostAck("Effect committed; ACK lost")
                return AckResponse()
            # Reuse byte-identical source functions, but never import original main.
            lib=types.SimpleNamespace(request=types.SimpleNamespace(
                Request=urllib.request.Request,urlopen=urlopen))
            start=perf_counter_ns()
            with tempfile.TemporaryDirectory(prefix="p0-telegram-") as temp:
                env={"urllib":lib,"TG_BOT_TOKEN":"FAKE","TG_CHAT_ID":"FAKE",
                     "TG_THREAD_ID":None,"json":json,"datetime":datetime,
                     "timezone":timezone,"os":__import__("os"),
                     "POST_STATE_FILE":str(Path(temp)/"post_state.json")}
                for code in (send_code,state_code,state_read):exec(code,env)
                sent=False;first_error=None;unknown=False
                if arm=="baseline":
                    try:
                        env["send_telegram"]("TEST_ONLY_FIXED")
                        if case=="crash_after_ack_before_state":
                            raise RuntimeError("Process died before save_post_state")
                        env["save_post_state"]("synthetic",datetime(2026,11,9,tzinfo=timezone.utc))
                        sent=True
                    except Exception as exc:first_error=type(exc).__name__
                    # Simulate subsequent run if local state absent.
                    if not env["load_post_state"]():
                        try:
                            env["send_telegram"]("TEST_ONLY_FIXED")
                            env["save_post_state"]("synthetic",datetime(2026,11,9,tzinfo=timezone.utc))
                            sent=True
                        except Exception:
                            pass
                else:
                    # Minimal durable outbox prototype; records PREPARED before network call.
                    conn=sqlite3.connect(str(Path(temp)/"outbox.db"),isolation_level=None)
                    conn.execute("PRAGMA synchronous=FULL")
                    conn.execute("CREATE TABLE tx(id TEXT PRIMARY KEY, state TEXT)")
                    conn.execute("INSERT INTO tx VALUES (?,?)",("post-"+str(idx),"PREPARED"))
                    conn.execute("UPDATE tx SET state='IN_FLIGHT' WHERE id=?",("post-"+str(idx),))
                    try:
                        env["send_telegram"]("TEST_ONLY_FIXED")
                        if case=="crash_after_ack_before_state":
                            raise RuntimeError("Crash before durable ACK")
                        conn.execute("UPDATE tx SET state='ACKED' WHERE id=?",("post-"+str(idx),))
                        sent=True
                    except Exception as exc:
                        first_error=type(exc).__name__
                        # No automatic retry on unknown outcome. This trades liveness for safety.
                        conn.execute("UPDATE tx SET state='UNKNOWN' WHERE id=?",("post-"+str(idx),))
                        unknown=True
                    assert conn.execute("SELECT state FROM tx").fetchone()[0] in ("ACKED","UNKNOWN")
                    conn.close()
                trial[arm]={
                    "attempts":attempted,"remote_commits":len(ledger),
                    "duplicate_remote_effect":len(ledger)>1,
                    "recorded_success":sent,"unknown_pending":unknown,
                    "first_error":first_error}
            clock[arm].append(perf_counter_ns()-start)
        records.append(trial)
    def stats(arm):
        return {"total":len(records),
                "duplicate_remote_effects":sum(r[arm]["duplicate_remote_effect"] for r in records),
                "remote_commits":sum(r[arm]["remote_commits"] for r in records),
                "recorded_success":sum(r[arm]["recorded_success"] for r in records),
                "unknown_pending":sum(r[arm]["unknown_pending"] for r in records),
                "false_recorded_success":sum(r[arm]["recorded_success"] and r[arm]["remote_commits"]==0 for r in records)}
    return {"protocol":"delivery","pair":"exactly-once-limbo/TelegramBot",
            "scope":"ACTUAL_SEND_AND_POST_STATE_FUNCTIONS_VS_SQLITE_OUTBOX_PROTOTYPE_MOCK_NETWORK",
            "source_git_sha":PINNED["TelegramBot"][0],"source_file":PINNED["TelegramBot"][1],
            "source_file_sha256":source_hash,
            "seed":SEED,"cases":len(specs),"records":records,
            "baseline":stats("baseline"),"candidate":stats("candidate"),
            "timing":{"unit":"nanoseconds_per_case_including_state_IO_and_python_clock",
                      "p95_baseline_ns":sorted(clock["baseline"])[int((len(records)-1)*.95)],
                      "p95_candidate_ns":sorted(clock["candidate"])[int((len(records)-1)*.95)]},
            "negative_controls":["server effect ACK lost","network failure before effect","crash after ACK before local save"],
            "limitations":[
                "The candidate is a synthetic prototype outside the actual TelegramBot codebase, not an integrated outbox.",
                "The mock server has no idempotency/reconciliation API; UNKNOWN outcomes remain unresolved, so true exactly-once is not claimed.",
                "Replay-on-next-run is intentionally simulated from source-inspected caller logic; no full live scheduler executed.",
                "The candidate reduces duplicate auto-retries by quarantining UNKNOWN, trading away automated retry/liveness.",
                "Microbenchmark includes SQLite durability and is not a production runtime forecast."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snap",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    assert a.snap.is_dir() and a.out.is_dir()
    for id,fn in (("agent-risk-agent-config",quote_benchmark),
                  ("exactly-once-limbo-telegram",telegram_benchmark)):
        result=fn(a.snap)
        result["run_kind"]="SANDBOX_OFFLINE_SYNTHETIC_A_B"
        dest=a.out/("2026-11-09-p0-"+id+".json")
        dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
        print("AB_MEASURED",id,"baseline",result["baseline"],"candidate",result["candidate"])
if __name__=="__main__":main()
