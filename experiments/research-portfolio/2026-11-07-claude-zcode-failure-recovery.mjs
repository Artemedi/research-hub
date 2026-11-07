#!/usr/bin/env node
/** Fault-injection for patched Claude Swarm + evidence checkpoint contract.

* Runs the real WorkerManager and TaskLockManager with a disposable Git/tmux,
* mock CLI exit7/exit0. No model, real credentials or project code touched.
*/
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';

const source=path.resolve(process.env.CLAUDE_SWARM_SOURCE||'');
const output=path.resolve(process.env.OUTPUT||'');
const sha=x=>createHash('sha256').update(x).digest('hex');
const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8'}).trim();
assert.equal(git(source,'rev-parse','HEAD'),'31f19199bf3557cda4860231186a06b72c8edb94');
const {WorkerManager}=await import(pathToFileURL(path.join(source,'dist/workers/manager.js')).href);
const {WorktreeManager}=await import(pathToFileURL(path.join(source,'dist/workers/worktree-manager.js')).href);
const {TaskLockManager}=await import(pathToFileURL(path.join(source,'dist/workers/lock-manager.js')).href);
const {StateManager}=await import(pathToFileURL(path.join(source,'dist/state/manager.js')).href);

const root=fs.mkdtempSync(path.join(os.tmpdir(),'research-failure-inject-'));
const repo=path.join(root,'synthetic');
const original={PATH:process.env.PATH,TMUX_TMPDIR:process.env.TMUX_TMPDIR,
  RESEARCH_RECOVERY_RESULT_DIR:process.env.RESEARCH_RECOVERY_RESULT_DIR,
  CLAUDE_SWARM_PERMISSION_MODE:process.env.CLAUDE_SWARM_PERMISSION_MODE,
  CLAUDE_SWARM_ALLOWED_TOOLS:process.env.CLAUDE_SWARM_ALLOWED_TOOLS,
  CLAUDE_SWARM_MCP_SERVERS:process.env.CLAUDE_SWARM_MCP_SERVERS};
const cases=[];
function check(id,actual,expected,note){
  cases.push({id,actual,expected,matched:actual===expected,note});
  assert.equal(actual,expected,id);
}
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function statusOf(worker,sessionName){
  for(let i=0;i<120;i++){
    await pause(100);
    const state=(await worker.checkWorker(sessionName)).status;
    if(state!=='running')return state;
  }
  return 'running';
}
try{
  fs.mkdirSync(repo);
  git(root,'init','-q','-b','main',repo);
  git(repo,'config','user.email','test@invalid.example');
  git(repo,'config','user.name','Test');
  fs.writeFileSync(path.join(repo,'.gitignore'),'.claude/\n');
  fs.writeFileSync(path.join(repo,'README.md'),'synthetic failure recovery\n');
  git(repo,'add','.');
  git(repo,'commit','-q','-m','baseline');
  const originalHead=git(repo,'rev-parse','HEAD');
  const outDir=path.join(root,'verified');
  fs.mkdirSync(outDir);
  const binDir=path.join(root,'bin');
  fs.mkdirSync(binDir);
  const mock=path.join(binDir,'claude');
  fs.writeFileSync(mock,`#!/bin/sh
set -eu
marker=$(printf '%s\\n' "$*" | awk 'index($0, "- Create a file at: ") {sub(/^.*- Create a file at: /, "");print;exit}')
case "$marker" in /*.done) : ;; *) exit 85;; esac
case "$(basename "$PWD")" in
  failure-1)
    printf 'uncommitted worker progress\\n' > partial.txt
    mkdir -p "$(dirname "$marker")"
    printf 'stale done after failed CLI\\n' > "$marker"
    exit 7 ;;
  recovered-2)
    if test -e "$RESEARCH_RECOVERY_RESULT_DIR/recovered-2.json"; then exit 24; fi
    printf '{"labels":[{"id":"case-yes","decision":"SUPPORTED"},{"id":"case-no","decision":"NOT_SUPPORTED"}]}\\n' > "$RESEARCH_RECOVERY_RESULT_DIR/recovered-2.json"
    mkdir -p "$(dirname "$marker")"
    printf 'completed after explicit recovery\\n' > "$marker"
    exit 0 ;;
  *) exit 89 ;;
esac
`,{mode:0o700});
  fs.copyFileSync(mock,path.join(binDir,'claude-code'));
  const tmuxDir=path.join(root,'private-tmux');
  fs.mkdirSync(tmuxDir);
  process.env.TMUX_TMPDIR=tmuxDir;
  process.env.PATH=binDir+path.delimiter+original.PATH;
  process.env.RESEARCH_RECOVERY_RESULT_DIR=outDir;
  process.env.CLAUDE_SWARM_PERMISSION_MODE='default';
  process.env.CLAUDE_SWARM_ALLOWED_TOOLS='Read';
  delete process.env.CLAUDE_SWARM_MCP_SERVERS;
  const manager=new WorkerManager(repo,new StateManager(repo));
  const wt=new WorktreeManager(repo);
  const locks=new TaskLockManager(repo);

  const first=await manager.startWorker({
    id:'failure-1',description:'mock fail after done',status:'pending',attempts:0
  });
  assert(first.success,first.error);
  const failState=await statusOf(manager,first.sessionName);
  check('nonzero_exit_does_not_complete',failState,'crashed',
    'An exit-7 mock with a done marker must not count as success');
  const dirty=path.join(repo,'.claude/worktrees/failure-1/partial.txt');
  check('failed_worker_dirty_progress_preserved',fs.readFileSync(dirty,'utf8'),
    'uncommitted worker progress\n','Crash does not silently remove a partial file');
  const l1=locks.claimFiles('failure-1',['src/shared.ts'],'failed-session');
  const l2=locks.claimFiles('recovered-2',['src/shared.ts'],'recovery-session');
  check('stale_lock_blocks_new_worker',l1.claimed.length===1&&l2.conflicts.length===1,true,
    'File lock remains until recovery explicitly releases it');
  const duplicate=await manager.startWorker({
    id:'failure-1',description:'unsafe repeated same id',status:'pending',attempts:1
  });
  check('same_feature_retry_rejected',duplicate.success,false,
    'Cannot destroy active dirty worktree by retrying feature id');
  check('same_feature_dirty_retained',fs.existsSync(dirty),true,
    'Worktree data is intact after rejected retry');
  const snapshot=path.join(root,'checkpointed-partial.txt');
  fs.copyFileSync(dirty,snapshot);
  check('checkpoint_matches_original',sha(fs.readFileSync(snapshot)),
    sha(fs.readFileSync(dirty)),'Owner checkpoint before explicit clean');
  const rc=locks.releaseAll('failure-1');
  const acquired=locks.claimFiles('recovered-2',['src/shared.ts'],'recovery-session');
  check('explicit_lock_recovery',rc===1&&acquired.claimed.length===1,true,
    'Manual release allows new worker to claim file');

  const saved=path.join(repo,'.claude/orchestrator/workers',first.sessionName+'.exit');
  const marker=path.join(repo,'.claude/orchestrator/workers',first.sessionName+'.done');
  check('failed_exit_marker_is_7',fs.readFileSync(saved,'utf8').trim(),'7',
    'Shell observes actual nonzero CLI exit');
  check('failed_worker_done_exists',fs.existsSync(marker),true,
    'Presence of done alone is not sufficient for acceptance');
  fs.writeFileSync(saved,'0\n');
  check('forged_exit_can_fool_manager',(await manager.checkWorker(first.sessionName)).status,
    'completed','Same-UID worker could rewrite its exit file; security gap remains');
  check('external_oracle_rejects_false_success',fs.existsSync(
    path.join(outDir,'failure-1.json')),false,
    'Model-independent checker refuses completion with no validated result');
  fs.writeFileSync(saved,'7\n');
  // No force-reset is needed to launch a new unique task. Old dirty worktree
  // remains available for manual recovery while new worker proceeds.
  const recovered=await manager.startWorker({
    id:'recovered-2',description:'new unique job with validated fixture',
    status:'pending',attempts:0
  });
  assert(recovered.success,recovered.error);
  const recoveredState=await statusOf(manager,recovered.sessionName);
  check('new_unique_worker_completes',recoveredState,'completed',
    'Explicitly new task id can recover without resetting crashed worktree');
  const evidence=JSON.parse(fs.readFileSync(path.join(outDir,'recovered-2.json'),'utf8'));
  check('oracle_correct_result',JSON.stringify(evidence.labels),
    JSON.stringify([{id:'case-yes',decision:'SUPPORTED'},{id:'case-no',decision:'NOT_SUPPORTED'}]),
    'External fixture oracle verifies both outcomes');
  const repeated=await manager.startWorker({
    id:'recovered-2',description:'repeat accepted ID',status:'pending',attempts:1
  });
  check('accepted_id_duplicate_rejected',repeated.success,false,
    'A worktree that already exists prevents unverified duplicate processing');
  check('one_evidence_file_only',fs.readdirSync(outDir).length,1,
    'Only one result file is accepted after recovery');
  check('main_repo_head_unchanged',git(repo,'rev-parse','HEAD'),originalHead,
    'Main synthetic Git branch unchanged');
  check('failed_dirty_still_available_after_success',fs.existsSync(dirty),true,
    'Recovery cannot silently destroy prior worker progress');

  const record={
    date:'2026-11-07',
    study:'Claude Swarm bounded failure/recovery injection',
    source_pin:'31f19199bf3557cda4860231186a06b72c8edb94',
    cases_total:cases.length,matched_oracle:cases.filter(x=>x.matched).length,cases,
    independent_oracle:'synthetic mock exit codes, FS content SHA, Git refs, external fixed JSON',
    model_calls:0,real_project_changes:0,
    status:'BOUNDED_RECOVERY_REPRODUCED',
    limitations:[
      'One local Unix UID; worker can forge own exit/done marker',
      'Manual explicit releaseAll and new task ID; not automatic fault-tolerant scheduler',
      'No distributed crash recovery, power loss, retries, or concurrent file races',
      'No real model, credentials, production repository or private data',
      'Original dirty worktree is retained until separate owner-approved cleanup'
    ]
  };
  fs.mkdirSync(path.dirname(output),{recursive:true});
  fs.writeFileSync(output,JSON.stringify(record,null,2)+'\n');
  console.log('RECOVERY',JSON.stringify({cases:record.cases_total,matched:record.matched_oracle,status:record.status}));
}finally{
  try{execFileSync('tmux',['kill-server'],{stdio:'ignore'});}catch{}
  for(const [key,value] of Object.entries(original)){
    if(value===undefined)delete process.env[key];else process.env[key]=value;
  }
  fs.rmSync(root,{recursive:true,force:true});
}
