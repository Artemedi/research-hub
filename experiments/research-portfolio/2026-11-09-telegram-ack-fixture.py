#!/usr/bin/env python3
"""Execute only AST-extracted original Telegram send/state functions with mocked I/O.

Never imports the original module, invokes its main(), or uses an actual HTTP
client. Run under network-denied bubblewrap and in an empty temp filesystem.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import urllib.request

SOURCE_COMMIT="a838ca6671cada5307825d3b5c433ce7083e1e76"

def functions_from_source(path):
    raw=path.read_bytes()
    tree=ast.parse(raw.decode("utf8"),filename=str(path))
    funcs={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
    chosen=["send_telegram","save_post_state","load_post_state"]
    assert all(f in funcs for f in chosen)
    bundle=ast.Module(body=[funcs[f] for f in chosen],type_ignores=[])
    ast.fix_missing_locations(bundle)
    return compile(bundle,str(path),"exec"),hashlib.sha256(raw).hexdigest()

class Ack:
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def read(self):
        return b'{"ok":true,"result":{"message_id":1234}}'

def exercise(code):
    records={}
    for scenario in ("ack_normal","remote_commit_ack_lost","no_remote_commit"):
        committed=[]
        state={}
        with TemporaryDirectory(prefix="telegram-offline-") as tmp:
            def urlopen(request):
                assert request.full_url.startswith("https://api.telegram.org/botFAKE/sendMessage")
                assert json.loads(request.data)["text"]=="Synthetic post"
                if scenario=="no_remote_commit" and len(committed)==0 and not state.get("previous_failure"):
                    state["previous_failure"]=True
                    raise TimeoutError("offline no effect")
                committed.append("Synthetic post")
                if scenario=="remote_commit_ack_lost" and len(committed)==1:
                    raise TimeoutError("offline ack lost AFTER server commit")
                return Ack()
            http=types.SimpleNamespace(request=types.SimpleNamespace(
                Request=urllib.request.Request,urlopen=urlopen))
            g={"TG_BOT_TOKEN":"FAKE","TG_CHAT_ID":"FAKECHAT",
               "TG_THREAD_ID":None,"urllib":http,"json":json,
               "datetime":datetime,"timezone":timezone,
               "os":__import__("os"),
               "POST_STATE_FILE":str(Path(tmp)/"post_state.json")}
            exec(code,g)
            first_failed=False
            try:g["send_telegram"]("Synthetic post")
            except TimeoutError:first_failed=True
            if not first_failed:
                g["save_post_state"]("synthetic-channel",datetime(2026,11,9,tzinfo=timezone.utc))
            before=g["load_post_state"]()
            if first_failed:
                # Simulates the pre-existing main.py decision to retry next run:
                # absence of local state does not prove absence of remote effect.
                assert not before
                g["send_telegram"]("Synthetic post")
                g["save_post_state"]("synthetic-channel",datetime(2026,11,9,tzinfo=timezone.utc))
            after=g["load_post_state"]()
            records[scenario]={
                "first_attempt_error":first_failed,
                "remote_effect_count":len(committed),
                "state_recorded_before_retry":bool(before),
                "state_recorded_after_retry":bool(after),
                "duplicate_remote_effect":len(committed)>1,
            }
    assert records["ack_normal"]["remote_effect_count"]==1
    assert records["remote_commit_ack_lost"]["remote_effect_count"]==2
    assert records["remote_commit_ack_lost"]["duplicate_remote_effect"]
    assert records["no_remote_commit"]["remote_effect_count"]==1
    return records

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    code,sha=functions_from_source(a.source)
    records=exercise(code)
    payload={
        "status":"SOURCE_FUNCTIONS_REPRODUCED_MOCK_ONLY",
        "source_repo":"Artemedi/TelegramBot","source_git_sha":SOURCE_COMMIT,
        "source_file":"main.py","source_file_sha256":sha,
        "execution_mode":"AST-extracted exact 3 original functions, network unshared, mock urlopen, fake credentials",
        "records":records,
        "finding":"An acknowledged remote commit with lost HTTP acknowledgment leaves no local post state; unguarded retry repeats side effect.",
        "limits":["Caller retry decision simulated based on inspected main.py branch, not a full integration E2E.",
                  "No production credentials, real channel or live network calls used.",
                  "A durable outbox alone cannot guarantee true exactly-once without a remote dedupe/reconciliation primitive.",
                  "No candidate implementation or claimed improvement was run."],
    }
    a.out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("TELEGRAM_OFFLINE_SOURCE_PROBE",records)
if __name__=="__main__":
    main()
