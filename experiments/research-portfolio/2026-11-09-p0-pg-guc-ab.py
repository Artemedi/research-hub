#!/usr/bin/env python3
"""P0 direct GUC reader versus already existing source MCP wrapper.

Original source is AST-extracted from pinned Git archive, no FastMCP import,
no PostgreSQL connection, and no new read adapter implemented. This is
an offline equivalence/cost ablation, not a model or database improvement.
"""
import argparse
import ast
import asyncio
import hashlib
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
from types import SimpleNamespace

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    scripts=a.source/"Wiki_PG/scripts"
    ingest=a.source/"Wiki_PG/ingestion"
    sys.path.insert(0,str(scripts))
    sys.path.insert(0,str(ingest))
    import pg_config_lookup as config
    code=ingest/"mcp_wiki_server.py"
    source_bytes=code.read_bytes()
    tree=ast.parse(source_bytes.decode("utf8"),filename=str(code))
    selected=[]
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in ("_pg_setting_result","get_postgres_setting"):
            node.decorator_list=[]
            selected.append(node)
    assert {n.name for n in selected}=={"_pg_setting_result","get_postgres_setting"}
    m=ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[]))
    records=[]
    direct_ns=[]
    wrapper_ns=[]
    categories=["valid"]*40+[
        "bad_parameter","bad_date","missing_host","wrong_port",
        "invalid_snapshot","no_snapshot","no_setting","ambiguous_snapshot"
    ]
    for i,typ in enumerate(categories):
        with tempfile.TemporaryDirectory(prefix="p0-pg-setting-") as tmp:
            root=Path(tmp)/"Wiki_PG"
            alias=root/"operations/clusters/registry.yaml"
            alias.parent.mkdir(parents=True)
            alias.write_text("clusters:\n  DEMO_136: sandbox\naliases:\n  203.0.113.36: DEMO_136\n",encoding="utf8")
            dest=root/"raw/sysconfig-report"/"Sandbox"/"203.0.113.36"/"2026/11"
            dest.mkdir(parents=True)
            applied=str(200+i*7)
            file=dest/"203.0.113.36_sysconfig_report_2026-11-09_08-00-00.json"
            obj={"postgres_settings":{"instances":[{"port":"5432","settings":[
                {"name":"max_connections","setting":applied,"unit":None,"boot_val":"100",
                 "source":"configuration file","sourcefile":"/synthetic/postgresql.conf","sourceline":"12"}
            ],"not_applied_config_lines":[{"name":"max_connections","setting":"9999"}]}]}}
            file.write_text(json.dumps(obj),encoding="utf8")
            if typ=="invalid_snapshot":
                file.write_text("{bad json",encoding="utf8")
            if typ=="no_snapshot":
                file.unlink()
            if typ=="no_setting":
                obj["postgres_settings"]["instances"][0]["settings"]=[]
                file.write_text(json.dumps(obj))
            if typ=="ambiguous_snapshot":
                alt=dest.parent.parent/"DEMO_136"/"2026/11"
                alt.mkdir(parents=True)
                extra=json.loads(json.dumps(obj))
                extra["postgres_settings"]["instances"][0]["settings"][0]["setting"]="999"
                (alt/file.name.replace("203.0.113.36","DEMO_136")).write_text(json.dumps(extra))
            host="Missing_999" if typ=="missing_host" else "DEMO_136"
            parameter="../../etc" if typ=="bad_parameter" else "max_connections"
            port="5433" if typ=="wrong_port" else "5432"
            date="2026-02-30" if typ=="bad_date" else None
            argv=(root,host,parameter,port,None,date)
            t0=time.perf_counter_ns()
            direct=config.collect(*argv)
            direct_ns.append(time.perf_counter_ns()-t0)
            def fake_output(data):
                return SimpleNamespace(structuredContent=data,isError=False)
            g={"asyncio":asyncio,"pg_config":config,"WIKI_ROOT":root,
               "_tool_result":fake_output,"json":json}
            exec(compile(m,str(code),"exec"),g)
            t0=time.perf_counter_ns()
            wrapped=asyncio.run(g["get_postgres_setting"](
                host,parameter,pg_port=port,snapshot_date=date))
            wrapper_ns.append(time.perf_counter_ns()-t0)
            payload=wrapped.structuredContent
            assert payload["contract_version"]=="1.0"
            assert payload["status"]==direct["status"]
            status=direct["status"]
            value=direct.get("setting")
            wrapper_value=(payload.get("data") or [{}])[0].get("setting")
            expected=applied if typ=="valid" else None
            assert (status=="ok")==(typ=="valid"),(typ,status)
            assert value==expected
            assert wrapper_value==expected
            records.append({"id":i,"category":typ,"gold_status":"ok" if typ=="valid" else status,
                            "gold_setting":expected,"baseline_status":status,
                            "baseline_value":value,"wrapper_status":payload["status"],
                            "wrapper_value":wrapper_value,
                            "wrapper_source_present":bool(payload.get("sources")),
                            "same_value":value==wrapper_value})
    def p95(xs):return int(sorted(xs)[int((len(xs)-1)*.95)])
    result={
        "protocol":"sql","pair":"mcp-toolbox-postgres/Wiki_PG",
        "scope":"DIRECT_PINNED_COLLECT_VS_EXISTING_AST_EXTRACTED_MCP_GUC_TOOL_MOCK_TRANSPORT",
        "source_git_sha":"d55721bb99bff25fae352341cfd630c048693d6b",
        "source_file":"Wiki_PG/ingestion/mcp_wiki_server.py",
        "source_file_sha256":sha(source_bytes),
        "baseline":{"valid_correct":sum(r["category"]=="valid" and r["baseline_value"]==r["gold_setting"] for r in records),
                    "invalid_non_ok":sum(r["category"]!="valid" and r["baseline_status"]!="ok" for r in records)},
        "candidate":{"valid_correct":sum(r["category"]=="valid" and r["wrapper_value"]==r["gold_setting"] for r in records),
                     "invalid_non_ok":sum(r["category"]!="valid" and r["wrapper_status"]!="ok" for r in records)},
        "records":records,
        "timing":{"unit":"nanoseconds_per_case_including_IO",
                  "samples_per_arm":len(records),
                  "p95_baseline_ns":p95(direct_ns),"p95_candidate_ns":p95(wrapper_ns)},
        "negative_controls":[c for c in categories if c!="valid"],
        "limitations":[
            "This MCP get_postgres_setting method ALREADY exists in source; it is not a new candidate implementation.",
            "Only AST-extracted original async source and real pg_config_lookup.collect executed with fake transport.",
            "No FastMCP installed and no end-to-end MCP, Postgres, or live snapshot request executed.",
            "Unit-sample timing includes asyncio.run and thread startup, not in-process production throughput.",
        ],
    }
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("PG_GUC_OFFLINE_BASELINE_VS_EXISTING_WRAPPER",result["baseline"],result["candidate"],result["timing"])

if __name__=="__main__":main()
