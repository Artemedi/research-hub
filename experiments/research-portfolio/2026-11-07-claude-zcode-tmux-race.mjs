#!/usr/bin/env node
/** Deterministic tmux capture-pane TOCTOU control on actual WorkerManager.
 * A private wrapper injects exactly one capture-pane exit failure; no ZCode.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';

const source=path.resolve(process.env.CLAUDE_SWARM_SOURCE||'');
const output=path.resolve(process.env.OUTPUT||'');
const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8'}).trim();
assert.equal(git(source,'rev-parse','HEAD'),'31f19199bf3557cda4860231186a06b72c8edb94');
const {WorkerManager}=await import(pathToFileURL(path.join(source,'dist/workers/manager.js')).href);
const {StateManager}=await import(pathToFileURL(path.join(source,'dist/state/manager.js')).href);
const root=fs.mkdtempSync(path.join(os.tmpdir(),'research-tmux-race-'));
const repo=path.join(root,'synthetic');
const preserved=Object.fromEntries(['PATH','TMUX_TMPDIR','CLAUDE_SWARM_PERMISSION_MODE',
  'CLAUDE_SWARM_ALLOWED_TOOLS','CLAUDE_SWARM_MCP_SERVERS',
  'RESEARCH_FAULT_ONCE'].map(k=>[k,process.env[k]]));
const realTmux=execFileSync('which',['tmux'],{encoding:'utf8'}).trim();
const cases=[];
const check=(id,actual,expected)=>{
  cases.push({id,actual,expected,passed:actual===expected});
  assert.equal(actual,expected,id);
};
const wait=ms=>new Promise(r=>setTimeout(r,ms));
try{
  fs.mkdirSync(repo);
  git(root,'init','-q','-b','main',repo);
  git(repo,'config','user.name','Fixture');
  git(repo,'config','user.email','fixture@invalid.example');
  fs.writeFileSync(path.join(repo,'.gitignore'),'.claude/\n');
  fs.writeFileSync(path.join(repo,'README.md'),'synthetic race\n');
  git(repo,'add','.');
  git(repo,'commit','-q','-m','baseline');
  const base=git(repo,'rev-parse','HEAD');
  const bin=path.join(root,'bin');
  fs.mkdirSync(bin);
  const mock=path.join(bin,'claude-code');
  fs.writeFileSync(mock,`#!/bin/sh
set -eu
marker=$(printf '%s\\n' "$*" | awk 'index($0, "- Create a file at: ") {sub(/^.*- Create a file at: /, "");print;exit}')
case "$marker" in /*.done) : ;; *) exit 51;; esac
mkdir -p "$(dirname "$marker")"
printf 'success in synthetic race\\n' > "$marker"
sleep 1
exit 0
`,{mode:0o700});
  fs.copyFileSync(mock,path.join(bin,'claude'));
  const fault=path.join(root,'capture-once');
  fs.writeFileSync(fault,'inject once');
  const tmux=path.join(bin,'tmux');
  fs.writeFileSync(tmux,`#!/bin/sh
if [ "$1" = "capture-pane" ] && [ -f "$RESEARCH_FAULT_ONCE" ]; then
  rm -- "$RESEARCH_FAULT_ONCE"
  exit 1
fi
exec ${JSON.stringify(realTmux)} "$@"
`,{mode:0o700});
  process.env.PATH=bin+path.delimiter+preserved.PATH;
  process.env.RESEARCH_FAULT_ONCE=fault;
  process.env.TMUX_TMPDIR=path.join(root,'tmux');
  fs.mkdirSync(process.env.TMUX_TMPDIR);
  process.env.CLAUDE_SWARM_PERMISSION_MODE='default';
  process.env.CLAUDE_SWARM_ALLOWED_TOOLS='Read';
  delete process.env.CLAUDE_SWARM_MCP_SERVERS;
  const manager=new WorkerManager(repo,new StateManager(repo));
  const start=await manager.startWorker({
    id:'race-one',description:'synthetic tmux session race',status:'pending',attempts:0
  });
  assert(start.success,start.error);
  const first=await manager.checkWorker(start.sessionName);
  check('capture_failure_returns_not_found',first.status,'not_found');
  check('tmux_fault_consumed',fs.existsSync(fault),false);
  // Bounded retry, not blind classification of a transient not_found as crash.
  let status=first.status;
  let retries=0;
  for(let i=0;i<60;i++){
    await wait(110);
    status=(await manager.checkWorker(start.sessionName)).status;
    if(status==='not_found' && retries<3){retries++;continue;}
    if(status!=='running'&&status!=='not_found')break;
  }
  check('retry_recovers_completed',status,'completed');
  const workDir=path.join(repo,'.claude/orchestrator/workers');
  check('done_exit_markers_agree',
    fs.existsSync(path.join(workDir,start.sessionName+'.done'))&&
    fs.readFileSync(path.join(workDir,start.sessionName+'.exit'),'utf8').trim()==='0',
    true);
  check('main_ref_not_mutated',git(repo,'rev-parse','HEAD'),base);
  const record={
    date:'2026-11-07',study:'Synthetic tmux list-sessions/capture-pane race',
    source_pin:'31f19199bf3557cda4860231186a06b72c8edb94',
    cases_total:cases.length,passed:cases.filter(x=>x.passed).length,
    cases,first_status:first.status,after_retry:status,
    model_calls:0,production_writes:0,
    limitation:'Injected capture-pane failure, not real kernel scheduling race; same-UID completion files are not security attestations'
  };
  fs.mkdirSync(path.dirname(output),{recursive:true});
  fs.writeFileSync(output,JSON.stringify(record,null,2)+'\n');
  console.log('RACE',JSON.stringify({cases:record.cases_total,passed:record.passed,
    first:record.first_status,recovered:record.after_retry}));
}finally{
  try{execFileSync(realTmux,['kill-server'],{stdio:'ignore'});}catch{}
  for(const [key,value] of Object.entries(preserved)){
    if(value===undefined)delete process.env[key];else process.env[key]=value;
  }
  fs.rmSync(root,{recursive:true,force:true});
}
