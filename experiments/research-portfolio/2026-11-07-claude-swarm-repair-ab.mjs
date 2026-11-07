#!/usr/bin/env node
/**
 * Real WorkerManager/WorktreeManager repair A/B on disposable Git + isolated tmux.
 * Run against an isolated source checkout with research patch applied and built.
 * Uses only a fake Claude CLI, never genuine agent sessions or credentials.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';

const source=path.resolve(process.env.CLAUDE_SWARM_SOURCE || '');
const output=path.resolve(process.env.OUTPUT || 'claude-swarm-repair-ab.json');
const pin='31f19199bf3557cda4860231186a06b72c8edb94';
const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8'}).trim();
const sha=x=>createHash('sha256').update(x).digest('hex');
assert.equal(git(source,'rev-parse','HEAD'),pin);
const sourceFiles=['src/workers/manager.ts','src/workers/worktree-manager.ts'];
const fileHashes=Object.fromEntries(sourceFiles.map(x=>[x,sha(fs.readFileSync(path.join(source,x)))]));
const {WorkerManager}=await import(pathToFileURL(path.join(source,'dist/workers/manager.js')).href);
const {WorktreeManager}=await import(pathToFileURL(path.join(source,'dist/workers/worktree-manager.js')).href);
const {TaskLockManager}=await import(pathToFileURL(path.join(source,'dist/workers/lock-manager.js')).href);
const {StateManager}=await import(pathToFileURL(path.join(source,'dist/state/manager.js')).href);
const results=[];
function check(name,actual,expected,meaning) {
  results.push({name,actual,expected,passed:actual===expected,meaning});
  assert.equal(actual,expected,name);
}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const root=fs.mkdtempSync(path.join(os.tmpdir(),'research-swarm-repair-ab-'));
const repo=path.join(root,'synthetic');
const savedPath=process.env.PATH;
const savedTmux=process.env.TMUX_TMPDIR;
try {
  fs.mkdirSync(repo);
  git(root,'init','-q','-b','main',repo);
  git(repo,'config','user.email','fixture@invalid.example');
  git(repo,'config','user.name','Fixture');
  fs.writeFileSync(path.join(repo,'.gitignore'),'.claude/\n');
  fs.writeFileSync(path.join(repo,'README.md'),'clean baseline\n');
  git(repo,'add','.');
  git(repo,'commit','-q','-m','synthetic start');
  const head=git(repo,'rev-parse','HEAD');

  const worktrees=new WorktreeManager(repo);
  const locks=new TaskLockManager(repo);
  const alpha=await worktrees.createWorktree('alpha');
  const dirty=path.join(alpha.worktreePath,'uncommitted.txt');
  fs.writeFileSync(dirty,'preserve me on retry\n');
  let retryError='';
  try {await worktrees.createWorktree('alpha');}
  catch(e) {retryError=String(e.message);}
  check('retry_rejected',retryError.includes('explicit recovery required'),true,
    'Dirty worktree must fail closed, never force-delete');
  check('dirty_file_preserved',fs.readFileSync(dirty,'utf8'),'preserve me on retry\n',
    'Worker uncommitted content survives the attempted retry');
  check('original_worktree_unchanged',fs.existsSync(alpha.worktreePath),true,
    'Worktree directory survives');
  const worker=new WorkerManager(repo,new StateManager(repo));
  const blocked=await worker.startWorker({
    id:'alpha',description:'synthetic retry',status:'pending',attempts:0
  });
  check('manager_does_not_fallback_to_shared',blocked.success,false,
    'WorkerManager must propagate worktree creation error');
  check('failed_spawn_kept_dirty_worktree',fs.existsSync(dirty),true,
    'Failed worktree startup must not delete old worker state');

  const lock1=locks.claimFiles('alpha',['same/file.ts'],'one');
  const lock2=locks.claimFiles('beta',['same/file.ts'],'two');
  check('lock_conflict_still_enforced',lock1.claimed.length===1&&
    lock2.conflicts.length===1,true,'Keep atomic file ownership guarantee');

  const fake=path.join(root,'fake-cli');
  fs.mkdirSync(fake);
  const binary=path.join(fake,'claude');
  fs.writeFileSync(binary,`#!/bin/sh
set -eu
done_file=$(printf '%s\\n' "$*" | awk 'index($0, "- Create a file at: ") {sub(/^.*- Create a file at: /, "");print;exit}')
case "$done_file" in /*.done) : ;; *) echo INVALID_DONE_PATH >&2; exit 89 ;; esac
mkdir -p "$(dirname "$done_file")"
printf 'synthetic completion\\n' > "$done_file"
case "$(basename "$PWD")" in
  probe-ok) echo MOCK_SUCCESS; exit 0;;
  probe-fail) echo MOCK_FAILURE_AFTER_DONE; exit 7;;
  *) echo MOCK_UNKNOWN >&2; exit 99;;
esac
`,{mode:0o700});
  const tmuxdir=path.join(root,'tmux');
  fs.mkdirSync(tmuxdir);
  process.env.TMUX_TMPDIR=tmuxdir;
  process.env.PATH=fake+path.delimiter+savedPath;
  delete process.env.CLAUDE_SWARM_PERMISSION_MODE;
  delete process.env.CLAUDE_SWARM_ALLOWED_TOOLS;
  delete process.env.CLAUDE_SWARM_MCP_SERVERS;

  async function runWorker(id,expected) {
    const start=await worker.startWorker({
      id,description:'synthetic CLI recovery control',status:'pending',attempts:0
    });
    assert(start.success,start.error);
    const base=path.join(repo,'.claude/orchestrator/workers');
    const prompt=fs.readFileSync(path.join(base,id+'.prompt'),'utf8');
    const marker=path.join(base,start.sessionName+'.done');
    const exit=path.join(base,start.sessionName+'.exit');
    check(id+'_session_specific_prompt',prompt.includes(marker),true,
      'Prompt directs marker to absolute session-qualified path');
    let status='running';
    for(let i=0;i<100;i++) {
      await sleep(90);
      status=(await worker.checkWorker(start.sessionName)).status;
      if(status!=='running')break;
    }
    check(id+'_status',status,expected,
      'Classify actual CLI exit independently of .done marker');
    check(id+'_marker_exists',fs.existsSync(marker),true,
      'Fake CLI created a session-scoped marker');
    check(id+'_exit_code',fs.readFileSync(exit,'utf8').trim(),
      expected==='completed'?'0':'7','CLI exit code is persisted correctly');
    check(id+'_no_legacy_marker',fs.existsSync(path.join(base,id+'.done')),
      false,'Worker did not use a shared stale feature marker');
    if(expected==='crashed') {
      // This deliberately illustrates the remaining trust-boundary weakness:
      // a worker with the same OS identity can forge its own exit marker.
      fs.writeFileSync(exit,'0\n');
      check('untrusted_exit_marker_can_be_spoofed',
        (await worker.checkWorker(start.sessionName)).status,'completed',
        'Marker integrity is not a security guarantee against a malicious worker');
      fs.writeFileSync(exit,'7\n');
    }
  }
  await runWorker('probe-ok','completed');
  await runWorker('probe-fail','crashed');
  check('main_repo_head_unchanged',git(repo,'rev-parse','HEAD'),head,
    'No commits in main synthetic repository');
  check('original_dirty_content_remains',fs.readFileSync(dirty,'utf8'),
    'preserve me on retry\n','Independent runner did not disturb earlier worktree');

  try {execFileSync('tmux',['kill-server'],{stdio:'ignore'});}
  catch {}
  await worktrees.cleanupAll();
  const report={
    date:'2026-11-07',
    experiment:'pinned upstream Claude Swarm repair A/B',
    source_pin:pin,source_sha256:fileHashes,
    test_mode:'built real upstream managers + synthetic Git, private tmux, fake CLI',
    real_claude_calls:0,actual_target_project_modified:false,
    cases_total:results.length,cases_passed:results.filter(x=>x.passed).length,
    cases_failed:results.filter(x=>!x.passed).map(x=>x.name),
    cases:results,
    status:'BOUNDED_REPAIRED',
    remaining_risks:[
      'No actual Claude tool-use permission sandbox; bypassPermissions default unchanged',
      'Workers can write their own marker/exit file with Bash; markers are not a security attestation',
      'Concurrent retries, hard-kill during filesystem writes and process ownership race not stress tested',
      'Legacy non-worktree flows and plan/continuous mode not covered',
      'No model-backed worker or target DSH runtime tested',
      'Preserved dirty worktree requires explicit manual recovery; increases interruption overhead'
    ]
  };
  fs.mkdirSync(path.dirname(output),{recursive:true});
  fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({cases_total:report.cases_total,cases_passed:report.cases_passed,
    observed_fixed:results.filter(x=>x.name.includes('retry')||x.name.includes('status')).map(x=>x.name)}));
} finally {
  try{execFileSync('tmux',['kill-server'],{stdio:'ignore'});}catch{}
  process.env.PATH=savedPath;
  if(savedTmux===undefined)delete process.env.TMUX_TMPDIR;else process.env.TMUX_TMPDIR=savedTmux;
  fs.rmSync(root,{recursive:true,force:true});
}
