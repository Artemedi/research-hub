#!/usr/bin/env python3
"""Thirty real MCP Toolbox PG settings compared to independent live SQL oracle.

One ephemeral rootless Podman PG18, --network none, no published ports, fixed
parameterized SELECT and synthetic read-only credentials only.
"""
import asyncio,hashlib,json,os,pathlib,subprocess,time,statistics
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=pathlib.Path(os.environ["TOOLBOX_LAB_DIR"])
OUT=pathlib.Path(os.environ.get("OUTPUT",str(pathlib.Path.cwd()/"toolbox-30-settings.json")))
IMAGE="docker.io/library/postgres:18"
NAME="research-toolbox-pg-20261107"
PASSWORD="synthetic-fixture-no-secret"
BIN=ROOT/"toolbox"
BIN_HASH="f6fac005c39898a379523700727a2a3d0a2828f579bec22cc0efe74e0652062d"
assert hashlib.sha256(BIN.read_bytes()).hexdigest()==BIN_HASH
SETTINGS=[
 "max_connections","shared_buffers","work_mem","maintenance_work_mem",
 "autovacuum","autovacuum_naptime","autovacuum_vacuum_scale_factor",
 "autovacuum_analyze_scale_factor","autovacuum_freeze_max_age",
 "vacuum_freeze_min_age","checkpoint_timeout","max_wal_size","min_wal_size",
 "wal_level","wal_compression","wal_buffers","synchronous_commit",
 "synchronous_standby_names","max_replication_slots","max_wal_senders",
 "hot_standby","idle_in_transaction_session_timeout","statement_timeout",
 "lock_timeout","deadlock_timeout","effective_cache_size","random_page_cost",
 "seq_page_cost","effective_io_concurrency","max_parallel_workers"
]
assert len(SETTINGS)==30 and len(set(SETTINGS))==30

def command(args,timeout=30,stdin=None):
    return subprocess.run(args,input=stdin,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
def sql(stmt,role="postgres",db="lab",allow_failure=False):
    args=["podman","exec","-i"]
    if role=="observer":args+=["-e","PGPASSWORD="+PASSWORD]
    args += [NAME,"psql","-h","127.0.0.1","-U",role,"-d",db,"-X","-At",
             "-F","|","-v","ON_ERROR_STOP=1"]
    p=command(args+["-c",stmt],timeout=18)
    if p.returncode and not allow_failure:raise RuntimeError("sql failed: "+p.stderr[-550:])
    return p

def payload(result):
    if result.structuredContent is not None:return result.structuredContent
    if not result.content:return None
    return json.loads(result.content[0].text)

async def probe(oracle):
    params=StdioServerParameters(
       command="podman",args=["exec","-i",NAME,"/tmp/toolbox","--config","/tmp/tools.yaml","--stdio"])
    record=[];negatives=[]
    async with stdio_client(params) as (rd,wr):
      async with ClientSession(rd,wr) as client:
       await asyncio.wait_for(client.initialize(),timeout=18)
       manifest=await asyncio.wait_for(client.list_tools(),timeout=12)
       names=[x.name for x in manifest.tools]
       assert names==["get_live_pg_setting"],names
       for setting in SETTINGS:
           st=time.perf_counter_ns()
           res=await asyncio.wait_for(client.call_tool("get_live_pg_setting",{"setting":setting}),timeout=12)
           elapsed=(time.perf_counter_ns()-st)/1e6
           if res.isError:raise AssertionError("MCP_ERROR "+setting)
           data=payload(res)
           assert isinstance(data,dict), (setting,type(data).__name__,str(data)[:130])
           observed={k:str(data.get(k) or "") for k in ("name","setting","unit")}
           expected=oracle[setting]
           if observed!=expected:raise AssertionError((setting,observed,expected))
           record.append({"name":setting,"oracle_sha256":hashlib.sha256(
              json.dumps(expected,sort_keys=True).encode()).hexdigest(),
              "match":True,"call_elapsed_ms":round(elapsed,3)})
       for inp in (
         "work_mem'; DROP TABLE public.fixture; --",
         "setting_does_not_exist_20261107",
         "shared_buffers\x00unexpected"
       ):
           res=await asyncio.wait_for(client.call_tool("get_live_pg_setting",{"setting":inp}),timeout=12)
           if res.isError:
               negatives.append({"kind":"no_match_or_rejected","is_error":True,"no_sql_ddl_executed":True})
           else:
               data=payload(res)
               assert data in ([],{},None),repr(data)
               negatives.append({"kind":"no_match","is_error":False,"no_sql_ddl_executed":True})
    return record,negatives

async def main():
    assert command(["podman","container","exists",NAME],timeout=12).returncode!=0
    image=command(["podman","image","inspect",IMAGE,"--format","{{.Id}}"],timeout=12)
    assert image.returncode==0
    cfg=ROOT/"tools.yaml"
    cfg.write_text(
      "kind: source\nname: lab-postgres\ntype: postgres\n"
      "host: 127.0.0.1\nport: \"5432\"\n"
      "database: lab\nuser: observer\npassword: "+PASSWORD+"\n"
      "---\nkind: tool\nname: get_live_pg_setting\n"
      "type: postgres-sql\nsource: lab-postgres\n"
      "description: Read one setting via a bind parameter.\n"
      "parameters:\n  - name: setting\n    type: string\n    description: PostgreSQL setting name\n"
      "statement: \"SELECT name, setting, unit FROM pg_catalog.pg_settings WHERE name = $1\"\n")
    os.chmod(cfg,0o600)
    result={"date":"2026-11-07","study":"mcp-toolbox-postgres",
       "toolbox_version":"1.15.0+binary.linux.amd64.8e8e569",
       "toolbox_binary_sha256":BIN_HASH,"postgres_image":IMAGE,
       "postgres_image_id":image.stdout.strip(),"network":"none","published_ports":0,
       "private_project_credentials_used":False,
       "tool_spec":"fixed SELECT FROM pg_catalog.pg_settings WHERE name = $1; one bind param",
       "setting_count":len(SETTINGS),"distinct_settings":SETTINGS,
       "separate_direct_sql_oracle":True}
    launch=command(["podman","run","--pull=never","--rm","-d","--name",NAME,
         "--network","none","--memory","1g","--cpus","2","--pids-limit","200",
         "-e","POSTGRES_PASSWORD="+PASSWORD,IMAGE],timeout=30)
    if launch.returncode:raise RuntimeError("container blocked: "+launch.stderr[-450:])
    try:
      ready=False
      for i in range(45):
          p=command(["podman","exec",NAME,"pg_isready","-U","postgres"],timeout=8)
          if p.returncode==0:ready=True;break
          await asyncio.sleep(0.3)
      assert ready
      # Create isolated database and role. Password never reused elsewhere.
      sql("CREATE DATABASE lab",db="postgres")
      sql("CREATE ROLE observer LOGIN PASSWORD '"+PASSWORD+"'")
      sql("ALTER ROLE observer SET default_transaction_read_only=on")
      sql("GRANT CONNECT ON DATABASE lab TO observer")
      sql("CREATE TABLE public.fixture (id integer)")
      sql("INSERT INTO public.fixture VALUES (1)")
      sql("REVOKE ALL ON TABLE public.fixture FROM PUBLIC")
      # Untrusted SQL on observer is not grant-worthy: DML must be rejected
      denied=sql("BEGIN READ WRITE; INSERT INTO public.fixture VALUES (2)",role="observer",allow_failure=True)
      assert denied.returncode!=0 and "permission denied" in denied.stderr.lower(),denied.stderr[-500:]
      init_count=sql("SELECT COUNT(*) FROM public.fixture").stdout.strip()
      assert init_count=="1",init_count
      # Programmatic static selected 30 GUCs with independent oracle.
      items=",".join("'"+x+"'" for x in SETTINGS)
      oracle_sql="SELECT name, setting, COALESCE(unit,'') FROM pg_catalog.pg_settings WHERE name IN ("+items+") ORDER BY name"
      rs=sql(oracle_sql,role="observer")
      oracle={}
      for line in rs.stdout.strip().splitlines():
          xs=line.split("|")
          assert len(xs)==3,line
          oracle[xs[0]]={"name":xs[0],"setting":xs[1],"unit":xs[2]}
      assert len(oracle)==30,(len(oracle),sorted(set(SETTINGS)-set(oracle)))
      cp=command(["podman","cp",str(BIN),NAME+":/tmp/toolbox"],timeout=15)
      assert cp.returncode==0,cp.stderr[-280:]
      cp=command(["podman","cp",str(cfg),NAME+":/tmp/tools.yaml"],timeout=15)
      assert cp.returncode==0,cp.stderr[-280:]
      cli=command(["podman","exec",NAME,"/tmp/toolbox","--version"],timeout=10)
      assert cli.returncode==0,cli.stderr
      results,negatives=await probe(oracle)
      assert len(results)==30 and len(negatives)==3
      assert sql("SELECT count(*) FROM public.fixture").stdout.strip()=="1"
      vals=[x["call_elapsed_ms"] for x in results]
      result.update({
        "oracle_count":len(oracle),"matched_count":len(results),
        "negative_input_cases":negatives,"fixture_count_before_after":"1/1",
        "role_insert_denied":True,
        "call_latency_median_ms":round(statistics.median(vals),3),
        "call_latency_observed_p95_ms":round(sorted(vals)[int(.95*(len(vals)-1))],3),
        "latency_note":"one MCP call per GUC, no warmup/statistical benchmark",
        "results":results,
        "limits":[
          "Only 30 predefined read-only pg_settings names on synthetic PG18 were tested",
          "Raw SQL source is controlled by researcher; never exposed generic execute_sql",
          "Wiki_PG snapshot functionality is not tested in this run; previous 4-GUC lab is separate",
          "Backend uses PostgreSQL role-grants and parameterized fixed statement, not string validation",
          "No external PostgreSQL network, production table or secret was used"
        ]
      })
      OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
      print("MCP_TOOLBOX_30_GUC_PASS",len(results),"negatives",len(negatives),
           "median_ms",result["call_latency_median_ms"],"sha",BIN_HASH[:12],flush=True)
    finally:
      command(["podman","stop","--time","2",NAME],timeout=22)
      if command(["podman","container","exists",NAME],timeout=8).returncode==0:
          command(["podman","rm","-f",NAME],timeout=18)
      assert command(["podman","container","exists",NAME],timeout=8).returncode!=0
      cfg.unlink(missing_ok=True)
if __name__=="__main__":asyncio.run(main())
