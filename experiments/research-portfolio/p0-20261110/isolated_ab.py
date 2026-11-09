#!/usr/bin/env python3
"""Three source-backed paired offline AB *subsystem* probes.

Designed to be invoked ONLY in bwrap --unshare-net with Git-archive read-only
pinned target files in /source. Never imports target module top-level. The
independent gold labels come from seeded synthetic fixtures, not the variant
implementation. No real external effects are possible with fake transports.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import tempfile
import time
import types
import urllib.request

FILES = {
    "TelegramBot": "main.py",
    "agent-config": "tools/review.py",
    "Wiki_PG": "Wiki_PG/ingestion/retrieval_service.py",
}
DATE="2026-11-10"

def percentile(values, p):
    values=sorted(values)
    return values[(len(values)-1)*p//100] if values else None

def stats_ns(timings):
    return {"p50_us":round(statistics.median(timings)/1000,3),
            "p95_us":round(percentile(timings,95)/1000,3)}

def original_functions(path, names, globals_map=None):
    data=path.read_bytes()
    tree=ast.parse(data.decode("utf8"),filename=str(path))
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(selected)==len(names) and {n.name for n in selected}==set(names)
    module=ast.Module(body=selected,type_ignores=[])
    code=compile(ast.fix_missing_locations(module),str(path),"exec")
    ns=dict(globals_map or {})
    exec(code,ns)
    return ns, hashlib.sha256(data).hexdigest()

class OfflineHTTP:
    """Injected after source extraction; not a network client."""
    def __init__(self,mode):
        self.mode=mode
        self.calls=0
        self.commits=0
    def response_urlopen(self,req):
        class Response:
            def __enter__(self_):return self_
            def __exit__(self_,*args):return False
            def read(self_):return b'{"ok":true}'
        self.urlopen_called(req)
        return Response()
    def urlopen_called(self,req):
        assert req.full_url=="https://api.telegram.org/botOFFLINE_FAKE/sendMessage"
        assert json.loads(req.data)["text"]=="SYNTHETIC REPLAY"
        self.calls+=1
        if self.calls==1 and self.mode=="before_commit_timeout":
            raise TimeoutError("fixture: before commit")
        self.commits+=1
        if self.calls==1 and self.mode=="commit_lost_ack":
            raise TimeoutError("fixture: lost ack")

def telegram_code(source):
    ns, sha=original_functions(
        source,{"send_telegram","save_post_state","load_post_state"},
        {"json":json,"datetime":datetime,"timezone":timezone,"os":__import__("os")})
    return ns,sha

def telegram_trial(ns,mode,arm):
    with tempfile.TemporaryDirectory(prefix="p0-telegram-") as folder:
        remote=OfflineHTTP(mode)
        fake_http=types.SimpleNamespace(
            request=types.SimpleNamespace(
                Request=urllib.request.Request,
                urlopen=remote.response_urlopen))
        ns.update(TG_BOT_TOKEN="OFFLINE_FAKE",TG_CHAT_ID="OFFLINE_FAKE_CHAT",
                  TG_THREAD_ID=None,urllib=fake_http,
                  POST_STATE_FILE=str(Path(folder)/"post_state.json"))
        start=time.perf_counter_ns()
        pending=0
        try:
            ns["send_telegram"]("SYNTHETIC REPLAY")
            ns["save_post_state"]("mock-channel",datetime(2026,11,10,tzinfo=timezone.utc))
        except TimeoutError:
            if arm=="baseline_retry":
                ns["send_telegram"]("SYNTHETIC REPLAY")
                ns["save_post_state"]("mock-channel",datetime(2026,11,10,tzinfo=timezone.utc))
            else:
                # Experimental offline candidate: quarantine UNKNOWN, not replay.
                # This cannot guarantee delivery when original remote never committed.
                manifest=Path(folder)/"outbox_unknown.json"
                manifest.write_text(json.dumps({"key":"synthetic-video","status":"UNKNOWN",
                                               "action":"MANUAL_RECONCILIATION_REQUIRED"}))
                pending=1
        elapsed=time.perf_counter_ns()-start
        local=bool(ns["load_post_state"]())
        return {"remote_commits":remote.commits,"send_attempts":remote.calls,
                "delivered_exactly_once":remote.commits==1,
                "duplicate":remote.commits>1,
                "lost":remote.commits==0,
                "pending_unknown":pending,
                "false_local_success":local and remote.commits==0,
                "elapsed_ns":elapsed}

def telegram(source):
    ns,sha=telegram_code(source)
    modes=["ack","commit_lost_ack","before_commit_timeout"]
    by_arm={}
    for arm in ("baseline_retry","candidate_quarantine"):
        results=[]; timings=[]
        for i in range(120):
            mode=modes[i%3]
            r=telegram_trial(ns,mode,arm)
            results.append((mode,r));timings.append(r["elapsed_ns"])
        by_arm[arm]={
            "cases":120,
            "duplicate_cases":sum(r["duplicate"] for _,r in results),
            "lost_delivery_cases":sum(r["lost"] for _,r in results),
            "exactly_once_cases":sum(r["delivered_exactly_once"] for _,r in results),
            "quarantined_unknown_cases":sum(r["pending_unknown"] for _,r in results),
            "false_local_success":sum(r["false_local_success"] for _,r in results),
            "total_remote_commits":sum(r["remote_commits"] for _,r in results),
            "total_attempts":sum(r["send_attempts"] for _,r in results),
            "case_types":{m:{
                "runs":sum(mode==m for mode,_ in results),
                "duplicates":sum(r["duplicate"] for mode,r in results if mode==m),
                "missing":sum(r["lost"] for mode,r in results if mode==m),
            } for m in modes},
            "timing":stats_ns(timings)}
    assert by_arm["baseline_retry"]["duplicate_cases"]==40
    assert by_arm["baseline_retry"]["lost_delivery_cases"]==0
    assert by_arm["candidate_quarantine"]["duplicate_cases"]==0
    assert by_arm["candidate_quarantine"]["lost_delivery_cases"]==40
    return {
        "source_name":"TelegramBot",
        "executed_source_functions":["send_telegram","save_post_state","load_post_state"],
        "source_file_sha256":sha,
        "study_id":"exactly-once-limbo","project_id":"TelegramBot",
        "protocol":"delivery",
        "baseline":"original send + original state functions, source main retry branch simulated with a single retry",
        "variant":"outbox UNKNOWN quarantine to prevent blind resend (isolated sidecar policy only)",
        "dataset":"120 predeclared offline cases: 40 ack, 40 remote commit + lost ACK, 40 no remote commit + timeout",
        "independent_oracle":"mock remote committed-send ledger; exactly one remote commit required per case",
        "metrics":by_arm,
        "negative_controls":["ACK lost after commit","timeout before remote commit","normal success"],
        "subsystem_verdict":"REJECT_TREATMENT_DELIVERY_REGRESSION",
        "full_product_verdict":"BLOCKED_FULL_AB",
        "blocking_reason":"Candidate quarantine reduces duplicates by 40/120 but loses 40/120 deliveries; actual Telegram sendMessage lacks independently proven authoritative reconciliation/idempotency for an UNKNOWN outcome.",
        "limits":["No end-to-end original main() execution; caller retry behavior follows source inspection.",
                  "Local candidate is not merged into target repo.",
                  "Mock transport has omniscient oracle unavailable to the Telegram client.",
                  "Microbench timing includes temporary file I/O and not production API latency."],
    }

def agentconfig_trial(ns, arm, files, example):
    candidate=dict(example)
    start=time.perf_counter_ns()
    if arm=="baseline":
        output=ns["check_findings"]([candidate],files)[0]
        decision=bool(output["location_ok"] and output["evidence_found"])
    else:
        # Candidate test-only replacement for file-wide quote matching.
        # Independent of the original validator, but same input/consumer gate.
        by_name=dict(files)
        lines=by_name.get(candidate["file"],"").splitlines()
        q=" ".join(candidate.get("evidence","").split())
        line=candidate.get("line",0)
        decision=bool(1<=line<=len(lines) and q
                      and q in " ".join(lines[line-1].split()))
    elapsed=time.perf_counter_ns()-start
    return decision,elapsed

def agentconfig(source):
    ns,sha=original_functions(source,{"check_findings"})
    scenarios=[]
    for i in range(80):
        typ=("valid" if i<30 else "wrong_line" if i<50
             else "wrong_file" if i<65 else "invented_quote")
        name=f"fixture{i:03}.py"
        quote=f"ALLOW_FIELD_{i:03}"
        if typ=="valid":
            file=f"# HEADER\n{quote} = True\nOTHER = False\n"
            item={"file":name,"line":2,"evidence":f"{quote} = True"}
        elif typ=="wrong_line":
            file=f"# HEADER\nOTHER = False\n{quote} = True\n"
            item={"file":name,"line":2,"evidence":f"{quote} = True"}
        elif typ=="wrong_file":
            file="# HEADER\nOTHER = False\n"
            item={"file":name,"line":2,"evidence":f"{quote} = True"}
        else:
            file="# HEADER\nOTHER = False\n"
            item={"file":name,"line":2,"evidence":"DID_NOT_EXIST = True"}
        scenarios.append((typ,[(name,file)],item,typ=="valid"))
    by_arm={}
    for arm in ("baseline","candidate_same_line"):
        decisions=[];times=[]
        for typ,files,item,truth in scenarios:
            decision,elapsed=agentconfig_trial(ns,arm,files,item)
            decisions.append((typ,decision,truth))
            times.append(elapsed)
        by_arm[arm]={
            "cases":len(decisions),
            "true_accepts":sum(decision and truth for _,decision,truth in decisions),
            "false_accepts":sum(decision and not truth for _,decision,truth in decisions),
            "false_rejects":sum(not decision and truth for _,decision,truth in decisions),
            "true_rejects":sum(not decision and not truth for _,decision,truth in decisions),
            "by_control_type":{m:{
                "cases":sum(typ==m for typ,_,_ in decisions),
                "false_accepts":sum(typ==m and decision and not truth for typ,decision,truth in decisions),
            } for m in ("valid","wrong_line","wrong_file","invented_quote")},
            "timing":stats_ns(times)}
    assert by_arm["baseline"]["false_accepts"]==20
    assert by_arm["candidate_same_line"]["false_accepts"]==0
    assert by_arm["candidate_same_line"]["true_accepts"]==30
    by_arm["candidate_same_line"]["p95_vs_baseline"]=round(
        by_arm["candidate_same_line"]["timing"]["p95_us"]/
        by_arm["baseline"]["timing"]["p95_us"],4)
    by_arm["candidate_same_line"]["synthetic_gate_satisfied"]=(
        by_arm["candidate_same_line"]["false_accepts"]==0
        and by_arm["candidate_same_line"]["true_accepts"]>=by_arm["baseline"]["true_accepts"]
        and by_arm["candidate_same_line"]["p95_vs_baseline"]<=1.25)
    return {
        "source_name":"agent-config",
        "executed_source_functions":["check_findings"],
        "source_file_sha256":sha,
        "study_id":"agent-risk","project_id":"agent-config","protocol":"citation",
        "baseline":"original check_findings() location_ok AND evidence_found flags",
        "variant":"isolated same-line bound quote check, no production patch",
        "dataset":"80 pinned synthetic file-claim pairs, 30 valid, 20 wrong line, 15 wrong source/no quote, 15 invented quote",
        "independent_oracle":"Predeclared truth labels from fixture types and exact target line in independent fixture builder",
        "metrics":by_arm,
        "negative_controls":["right quote wrong line","wrong source file","quote absent"],
        "subsystem_verdict":"PASS_OFFLINE_LINE_BINDING_GUARD",
        "full_product_verdict":"BLOCKED_FULL_AB",
        "blocking_reason":"No integrated consumer, trace corpus or verified downstream acceptance behavior; quality win only on synthetic function-level citations.",
        "limits":["check_findings returns diagnostic fields; downstream auto-acceptance is not established.",
                  "No independent expert assessed real review findings.",
                  "Microbench p95 on synthetic in-process calls is not end-to-end review latency."],
    }

def wiki_trial(rrf, rankings, allowed, arm):
    start=time.perf_counter_ns()
    merged=rrf(*rankings) # pinned original _rrf_fuse()
    if arm=="baseline_rrf":
        selected=merged[:5]
    else:
        # Toy boundary treatment only, no Chroma/dense retrieval mutation.
        selected=[sid for sid in merged if sid in allowed][:5]
    return selected,time.perf_counter_ns()-start

def wiki(source):
    ns,sha=original_functions(source,{"_rrf_fuse"},{"RRF_K":60})
    rrf=ns["_rrf_fuse"]
    scenarios=[]
    for i in range(60):
        good=[f"allowed-{i}-{j}" for j in range(5)]
        bad=[f"forbidden-{i}-{j}" for j in range(3)]
        if i<45:
            rankings=[good,[good[j] for j in (4,0,3,1,2)]]
        else:
            rankings=[[bad[0],good[0],bad[1],good[1],good[2],good[3],good[4],bad[2]],
                      [bad[1],good[0],bad[0],good[1],good[2],good[3],good[4],bad[2]]]
        scenarios.append((rankings,set(good),good,i>=45))
    by_arm={}
    for arm in ("baseline_rrf","candidate_scoped_rrf"):
        results=[];timings=[]
        for rankings,allowed,gold,is_ood in scenarios:
            selected,elapsed=wiki_trial(rrf,rankings,allowed,arm)
            results.append((set(selected),allowed,set(gold),is_ood))
            timings.append(elapsed)
        by_arm[arm]={
            "cases":60,"recall_at_5_total":sum(len(gold & selected) for selected,allowed,gold,ood in results),
            "max_recall_at_5":300,
            "wrong_source_count":sum(len(selected-allowed) for selected,allowed,gold,ood in results),
            "ood_cases_with_wrong_source":sum(ood and bool(selected-allowed) for selected,allowed,gold,ood in results),
            "timing":stats_ns(timings)}
    assert by_arm["baseline_rrf"]["wrong_source_count"]>0
    assert by_arm["candidate_scoped_rrf"]["wrong_source_count"]==0
    assert by_arm["candidate_scoped_rrf"]["recall_at_5_total"]==300
    by_arm["candidate_scoped_rrf"]["p95_vs_baseline"]=round(
        by_arm["candidate_scoped_rrf"]["timing"]["p95_us"]/
        by_arm["baseline_rrf"]["timing"]["p95_us"],4)
    by_arm["candidate_scoped_rrf"]["synthetic_gate_satisfied"]=(
        by_arm["candidate_scoped_rrf"]["wrong_source_count"]==0
        and by_arm["candidate_scoped_rrf"]["recall_at_5_total"]>=by_arm["baseline_rrf"]["recall_at_5_total"]
        and by_arm["candidate_scoped_rrf"]["p95_vs_baseline"]<=1.25)
    return {
        "source_name":"Wiki_PG",
        "executed_source_functions":["_rrf_fuse"],
        "source_file_sha256":sha,
        "study_id":"drag","project_id":"Wiki_PG","protocol":"retrieval",
        "baseline":"pinned pure RRF merge subroutine, top-5 without source admission",
        "variant":"isolated allowlist/filter prior to top-5, not the actual retrieve() pipeline",
        "dataset":"60 frozen source-rank scenarios: 45 allowed-source, 15 adversarial rank-source conflicts",
        "independent_oracle":"Predeclared allowed source-ID set and 5 exact gold IDs per case",
        "metrics":by_arm,
        "negative_controls":["forbidden source dominates two rankers","correct source below bad source","normal all-allowed recall"],
        "subsystem_verdict":"PASS_OFFLINE_RANK_SOURCE_GUARD",
        "full_product_verdict":"BLOCKED_FULL_AB",
        "blocking_reason":"Actual retrieve() performs ChromaDB/dense+BM25 and tenant/filter work; this test executes only pure _rrf_fuse, not the DRAG algorithm nor live retrieval or latency.",
        "limits":["No embeddings, source indexing, model output, ChromaDB or live database.",
                  "The candidate is post-ranking authorization filtering, not upstream DRAG reproduction.",
                  "In-process microbench timings should not be used for deployment sizing."],
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    out=[]
    for app,filename,run in (("TelegramBot",FILES["TelegramBot"],telegram),
                             ("agent-config",FILES["agent-config"],agentconfig),
                             ("Wiki_PG",FILES["Wiki_PG"],wiki)):
        path=args.source/app/filename
        assert path.is_file(),path
        result=run(path)
        result["receipt_version"]=1
        result["snapshot_scope"]="pinned Git source file extracted into read-only mount; only declared function executed"
        result["network_access"]="DENIED_BWRAP_NETWORK_NAMESPACE"
        result["real_model_used"]=False
        result["human_expert_oracle"]=False
        out.append(result)
        print("P0_BOUNDARY_AB", result["study_id"],result["project_id"],
              result["subsystem_verdict"],result["full_product_verdict"])
    args.out.write_text(json.dumps({"date":DATE,"scope":"SUBSYSTEM_OFFLINE_SYNTHETIC_ONLY",
                                   "results":out},ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":
    main()
