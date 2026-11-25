"""Isolated synthetic online smoke. Requires an authenticated agy CLI."""
import json
import pathlib
import subprocess
import tempfile
import time

HOOK = '''import json,sys,pathlib
event=sys.argv[1]
data=json.load(sys.stdin)
p=pathlib.Path(__file__).with_name("events.jsonl")
old=p.read_text() if p.exists() else ""
with p.open("a") as f: f.write(json.dumps({"event":event,"has_conversation":bool(data.get("conversationId"))})+"\\n")
if event=="Stop" and '"event": "Stop"' not in old:
    print(json.dumps({"decision":"continue","reason":"Synthetic test: reply with the workspace code followed by GATE-4D2E. Do not use any tools."}))
else: print("{}" if event!="Stop" else '{"decision":"allow"}')
'''
PROMPT = "Synthetic test: reply with the workspace code or UNKNOWN. Do not use any tools, read files, or change anything."
with tempfile.TemporaryDirectory(prefix="agy-research-") as tmp:
    root = pathlib.Path(tmp)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".agents").mkdir()
    (root / "AGENTS.md").write_text("For this synthetic test, when asked for the workspace code, reply RULE-7B9C. Do not read files to obtain this code.\n")
    (root / "hook.py").write_text(HOOK)
    for mode, absolute, fmt in (("plan", False, "json"), ("auto", True, "stream-json"), ("plan", True, "json")):
        path = str(root / "hook.py") if absolute else "./hook.py"
        config = {"research-probe": {event: [{"type":"command","command":f"python3 {path} {event}"}] for event in ("SessionStart","PreInvocation","PostInvocation","Stop")}}
        (root / ".agents/hooks.json").write_text(json.dumps(config))
        journal = root / "events.jsonl"
        journal.unlink(missing_ok=True)
        started = time.monotonic()
        proc = subprocess.run(["agy", "-p", PROMPT, "--mode", mode, "--sandbox", "--print-timeout", "50s", "--output-format", fmt], cwd=root, text=True, capture_output=True, timeout=65)
        if fmt == "json":
            result = json.loads(proc.stdout)
        else:
            result = next((row["result"] for row in map(json.loads, proc.stdout.splitlines()) if row.get("event") == "result"), {})
        events = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
        print(json.dumps({"mode":mode,"absolute":absolute,"format":fmt,"exit":proc.returncode,"seconds":round(time.monotonic()-started,3),"status":result.get("status"),"response":result.get("response"),"usage":result.get("usage"),"events":events}))
