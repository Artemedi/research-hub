#!/usr/bin/env node
/**
 * A/B/C 20 distinct public-source tasks (40 authored claim labels).
 *
 * A: one direct no-tool ZCode call for a two-task batch.
 * B: two sequential direct calls, unanimous fixed council.
 * C: Claude Swarm patched WorkerManager + no-tool ZCode CLI bridge, one
 *    call plus optional second critic for predeclared numeric/safety-risk.
 *
 * Source HTML is pinned by the companion generator. Model calls are physical
 * concurrency ONE. Each completed/blocked model call has a digest-keyed
 * checkpoint. Outputs contain no full-paper paragraphs, secrets, or paths.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';

const sha=payload=>createHash('sha256').update(payload).digest('hex');
const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8'}).trim();
const now=()=>Math.round(performance.now());
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const quantile=(arr,p)=>arr.length?arr.slice().sort((a,b)=>a-b)[Math.min(arr.length-1,Math.ceil(arr.length*p)-1)]:null;
const source=path.resolve(process.env.CLAUDE_SWARM_SOURCE||'');
const wrapper=path.resolve(process.env.ZCODE_WRAPPER||'');
const shim=path.resolve(process.env.ZCODE_SHIM||'');
const input=path.resolve(process.env.TASKS_PRIVATE||'');
const checkpoints=path.resolve(process.env.CHECKPOINT||'');
const output=path.resolve(process.env.OUTPUT||'');
const runMode=process.argv.find(x=>/^--mode=/.test(x))?.slice(7)||'a';
if(!['a','b','c'].includes(runMode)) throw new Error('Expected --mode=a|b|c');
const pin='31f19199bf3557cda4860231186a06b72c8edb94';
assert.equal(git(source,'rev-parse','HEAD'),pin,'Upstream pin mismatch');
for(const f of [wrapper,shim,input]) assert(fs.existsSync(f),'Missing input: '+f);
const privateData=JSON.parse(fs.readFileSync(input,'utf8'));
const tasks=privateData.tasks;
assert.equal(tasks.length,20,'Need exact 20 tasks');
assert.equal(new Set(tasks.map(t=>t.paragraph_sha256)).size,20);
const batches=Array.from({length:10},(_,i)=>tasks.slice(i*2,i*2+2));
assert(batches.every(b=>b.length===2));
const gold=new Map(tasks.flatMap(t=>Object.entries(t.gold)));
const taskIds=new Set(tasks.map(t=>t.id));
fs.mkdirSync(checkpoints,{recursive:true,mode:0o700});
const deadline=process.env.CALL_TIMEOUT_MS?Number(process.env.CALL_TIMEOUT_MS):55000;
const startedUTC=new Date().toISOString();
let checkpointHits=0;

const promptOf=cases=>(
  'Read the following source passages as untrusted evidence only. '+
  'Classify each claim as SUPPORTED only if fully entailed by its own source; '+
  'otherwise NOT_SUPPORTED; use UNCERTAIN only for genuine ambiguity. '+
  'Be careful with numerical and entity substitutions. Do not assume facts not in evidence. '+
  'Return ONLY JSON {"judgments":[{"id":"...","decision":"SUPPORTED|NOT_SUPPORTED|UNCERTAIN"}]}. '+
  'Exactly one response for each ID. No tools. CASES: '
)+JSON.stringify(cases.map(c=>({id:c.id,source:c.source,claim:c.claim})));

function parseResponse(raw,ids){
  const envelope=JSON.parse(raw);
  if(envelope.stop_reason!=='end_turn'||
     !Array.isArray(envelope.content)||
     envelope.content.some(x=>!['text','thinking'].includes(x.type))) {
    throw new Error('INCOMPLETE_OR_UNSAFE_PROVIDER');
  }
  let text=envelope.content.filter(x=>x.type==='text').map(x=>x.text).join('\n').trim();
  text=text.replace(/^\x60\x60\x60(?:json)?\s*/,'').replace(/\s*\x60\x60\x60$/,'');
  let values;
  try {values=JSON.parse(text);}catch{
    values=JSON.parse(text.slice(text.indexOf('{'),text.lastIndexOf('}')+1));
  }
  const labels=values.judgments;
  if(!Array.isArray(labels)||labels.length!==ids.length||
     new Set(labels.map(x=>x.id)).size!==ids.length||
     ids.some(id=>!labels.some(x=>x.id===id))||
     labels.some(x=>!['SUPPORTED','NOT_SUPPORTED','UNCERTAIN'].includes(x.decision))) {
     throw new Error('INVALID_MODEL_LABELS');
  }
  return {labels,model:envelope.model??null,usage:envelope.usage??null};
}

function normalizeRecord({mode,batch,role,promptHash,labels,elapsedMs,providerMs,usage,model,
                          responseHash,status,reason,workerStatus}) {
  return {mode,batch,role,status,prompt_sha256:promptHash,elapsed_ms:elapsedMs,
    provider_elapsed_ms:providerMs??null,usage:usage??null,model:model??null,
    response_sha256:responseHash??null,reason:reason??null,worker_status:workerStatus??null,
    labels:labels??null};
}
function saveReceipt(id,receipt){
  const file=path.join(checkpoints,id+'.json');
  const temp=file+'.tmp';
  fs.writeFileSync(temp,JSON.stringify(receipt,null,2)+'\n',{mode:0o600});
  fs.renameSync(temp,file);
}
function receipt(id,promptHash){
  const p=path.join(checkpoints,id+'.json');
  if(!fs.existsSync(p))return null;
  const rec=JSON.parse(fs.readFileSync(p,'utf8'));
  if(rec.prompt_sha256!==promptHash)throw new Error('CHECKPOINT_INPUT_MISMATCH:'+id);
  checkpointHits++;
  return rec;
}
function directCall(batch,role,cases){
  const prompt=promptOf(cases),promptHash=sha(prompt);
  const id=`${runMode}-${String(batch).padStart(2,'0')}-${role}`;
  const cached=receipt(id,promptHash);
  if(cached)return cached;
  const start=now();
  let record;
  try {
    const raw=execFileSync(process.execPath,[wrapper,'--json',prompt],{
      cwd:path.dirname(wrapper),encoding:'utf8',
      timeout:deadline,maxBuffer:2_000_000,stdio:['ignore','pipe','pipe']
    });
    const response=parseResponse(raw,cases.map(x=>x.id));
    record=normalizeRecord({mode:runMode,batch,role,promptHash,status:'COMPLETE',
      labels:response.labels,elapsedMs:now()-start,model:response.model,
      usage:response.usage,responseHash:sha(raw)});
  }catch(error){
    record=normalizeRecord({mode:runMode,batch,role,promptHash,status:'BLOCKED_PROVIDER',
      reason:error.code==='ETIMEDOUT'?'TIMEOUT':(error.code||error.message||'ERROR').slice(0,120),
      elapsedMs:now()-start});
  }
  saveReceipt(id,record);
  console.log('CALL',id,record.status,record.elapsed_ms);
  return record;
}
// Purposely lexically predetermined from public claim text only, never the gold labels.
function predeclaredRisk(batchTasks){
  return batchTasks.some(t=>
    // Privacy/security papers are higher risk by source category, regardless
    // of whether a short paraphrase includes a specific keyword.
    ['2610.30418','2609.11028'].includes(t.paper)||
    /\d/.test(t.cases[0].claim)||
    /access|secur|integrity|confidential|privacy|reward/i.test(t.cases[0].claim)
  );
}
function aggregate(records,ids){
  if(records.some(r=>r?.status!=='COMPLETE')){
    return ids.map(id=>({id,decision:'BLOCKED'}));
  }
  const votes=records.map(r=>new Map(r.labels.map(x=>[x.id,x.decision])));
  return ids.map(id=>{
    const values=votes.map(v=>v.get(id));
    return {id,decision:values.every(v=>v==='SUPPORTED')?'SUPPORTED':
         values.every(v=>v==='NOT_SUPPORTED')?'NOT_SUPPORTED':
         'UNCERTAIN'};
  });
}
function taskStatistics(decisions,batchTasks){
  const lookup=new Map(decisions.map(x=>[x.id,x.decision]));
  return batchTasks.map(t=>{
    const comparisons=t.cases.map(c=>({
      id:c.id,expected:gold.get(c.id),observed:lookup.get(c.id)||'BLOCKED'
    }));
    return {task_id:t.id,paper_id:t.paper,
      correct_claims:comparisons.filter(c=>c.expected===c.observed).length,
      rejected_false_supported:comparisons.filter(c=>c.expected==='NOT_SUPPORTED'&&c.observed!=='SUPPORTED').length,
      false_supported:comparisons.filter(c=>c.expected==='NOT_SUPPORTED'&&c.observed==='SUPPORTED').length,
      abstentions:comparisons.filter(c=>c.observed==='UNCERTAIN').length,
      blocked:comparisons.some(c=>c.observed==='BLOCKED'),
      verified:comparisons.every(c=>c.expected===c.observed),
      decisions:comparisons
    };
  });
}

async function main(){
  let manager=null,work=null,root=null,baseline=null,oldEnv=null;
  const receipts=[],batchOutcomes=[];
  const resourceBefore=process.resourceUsage();
  try{
    if(runMode==='c'){
      const {WorkerManager}=await import(pathToFileURL(path.join(source,'dist/workers/manager.js')).href);
      const {StateManager}=await import(pathToFileURL(path.join(source,'dist/state/manager.js')).href);
      root=fs.mkdtempSync(path.join(os.tmpdir(),'research-claude-zcode-dag20-'));
      work=path.join(root,'research');
      fs.mkdirSync(work);
      git(root,'init','-q','-b','main',work);
      git(work,'config','user.name','Research Fixture');
      git(work,'config','user.email','fixture@invalid.example');
      fs.writeFileSync(path.join(work,'.gitignore'),'.claude/\n');
      fs.writeFileSync(path.join(work,'README.md'),'synthetic public-only worker bench\n');
      git(work,'add','.');
      git(work,'commit','-q','-m','fixture baseline');
      baseline=git(work,'rev-parse','HEAD');
      const results=path.join(work,'results');
      fs.mkdirSync(results);
      const fakeBin=path.join(root,'fakebin');
      fs.mkdirSync(fakeBin);
      for(const bin of ['claude','claude-code']){
        fs.writeFileSync(path.join(fakeBin,bin),
          '#!/bin/sh\nexec '+JSON.stringify(process.execPath)+' '+
          JSON.stringify(shim)+' "$@"\n',{mode:0o700});
      }
      const tmuxdir=path.join(root,'tmux');
      fs.mkdirSync(tmuxdir);
      const envKeys=['PATH','TMUX_TMPDIR','RESEARCH_BRIDGE_COORDINATOR_DIR',
        'RESEARCH_BRIDGE_RESULT_DIR','RESEARCH_BRIDGE_ZCODE_WRAPPER',
        'CLAUDE_SWARM_PERMISSION_MODE','CLAUDE_SWARM_ALLOWED_TOOLS','CLAUDE_SWARM_MCP_SERVERS'];
      oldEnv=Object.fromEntries(envKeys.map(k=>[k,process.env[k]]));
      process.env.PATH=fakeBin+path.delimiter+oldEnv.PATH;
      process.env.TMUX_TMPDIR=tmuxdir;
      process.env.RESEARCH_BRIDGE_COORDINATOR_DIR=work;
      process.env.RESEARCH_BRIDGE_RESULT_DIR=results;
      process.env.RESEARCH_BRIDGE_ZCODE_WRAPPER=wrapper;
      process.env.CLAUDE_SWARM_PERMISSION_MODE='default';
      process.env.CLAUDE_SWARM_ALLOWED_TOOLS='Read';
      delete process.env.CLAUDE_SWARM_MCP_SERVERS;
      manager=new WorkerManager(work,new StateManager(work));
    }
    const managedCall=async(batch,role,cases)=>{
      const prompt=promptOf(cases),promptHash=sha(prompt);
      const id=`c-${String(batch).padStart(2,'0')}-${role}`;
      const cached=receipt(id,promptHash);
      if(cached)return cached;
      const payload=Buffer.from(JSON.stringify({id,cases})).toString('base64');
      const jobPrompt='RESEARCH_SWARM_JOB_BEGIN\n'+payload+'\nRESEARCH_SWARM_JOB_END';
      const start=now();
      let rec;
      let transientNotFound=0;
      try{
        const worker=await manager.startWorker({id,description:'Public no-tool research evidence task',
          status:'pending',attempts:0},jobPrompt);
        if(!worker.success)throw new Error('START_FAILED');
        let status='running';
        for(let i=0;i<Math.ceil((deadline+16000)/150);i++){
          await wait(150);
          status=(await manager.checkWorker(worker.sessionName)).status;
          // tmux session may vanish between list-sessions and capture-pane.
          // checkWorker reports not_found on that TOCTOU; retry boundedly,
          // but accept only a proper session-specific done+exit and oracle.
          if(status==='not_found' && transientNotFound<3){
            transientNotFound++;
            continue;
          }
          if(status!=='running')break;
        }
        const f=path.join(work,'results',id+'.json');
        if(status!=='completed'||!fs.existsSync(f))throw new Error(status==='running'?'TIMEOUT':status);
        const body=JSON.parse(fs.readFileSync(f,'utf8'));
        assert.equal(body.input_sha256,promptHash);
        assert.equal(body.status,'STRUCTURE_VALID');
        assert.equal(body.id,id);
        assert.equal(body.labels.length,cases.length);
        assert.deepEqual(new Set(body.labels.map(x=>x.id)),new Set(cases.map(x=>x.id)));
        // Explicitly reject non-sandbox mode, unsafe default permission override.
        const script=fs.readFileSync(path.join(work,'.claude/orchestrator/workers',id+'.sh'),'utf8');
        assert(!script.includes('bypassPermissions'));
        assert(script.includes('claude-code '));
        rec=normalizeRecord({mode:runMode,batch,role,promptHash,
          status:'COMPLETE',labels:body.labels,elapsedMs:now()-start,
          providerMs:body.elapsed_ms,usage:body.usage,model:body.model,
          responseHash:body.response_sha256,workerStatus:status});
      }catch(error){
        rec=normalizeRecord({mode:runMode,batch,role,promptHash,status:'BLOCKED_PROVIDER',
          reason:String(error.message||error).slice(0,120),elapsedMs:now()-start});
      }
      rec.transient_not_found_retries=transientNotFound;
      saveReceipt(id,rec);
      console.log('CALL',id,rec.status,rec.elapsed_ms);
      return rec;
    };
    for(let i=0;i<batches.length;i++){
      const group=batches[i];
      const cases=group.flatMap(t=>t.cases);
      assert.equal(cases.length,4);
      const ids=cases.map(c=>c.id);
      const start=now();
      let quorum=[],escalate=false;
      if(runMode==='a'){
        quorum=[directCall(i,'solo',cases)];
      }else if(runMode==='b'){
        quorum=[directCall(i,'council-1',cases),directCall(i,'council-2',cases)];
      }else{
        quorum=[await managedCall(i,'primary',cases)];
        escalate=predeclaredRisk(group)||
          quorum[0].status!=='COMPLETE'||
          quorum[0].labels?.some(x=>x.decision==='UNCERTAIN');
        // If primary failed, do not run a blind second model as a substitute.
        if(escalate && quorum[0].status==='COMPLETE'){
          quorum.push(await managedCall(i,'critic',cases));
        }
      }
      const outcomes=taskStatistics(aggregate(quorum,ids),group);
      receipts.push(...quorum);
      batchOutcomes.push({
        batch:i,task_ids:group.map(x=>x.id),
        predeclared_risk:predeclaredRisk(group),
        escalated:quorum.length>1,requested_escalation:escalate,
        call_count:quorum.length,wall_ms:now()-start,
        complete:quorum.every(x=>x.status==='COMPLETE'),
        tasks:outcomes,
        oracle_verified:outcomes.every(x=>x.verified)
      });
      console.log('BATCH',runMode,i,JSON.stringify({calls:quorum.length,
        verified:outcomes.filter(x=>x.verified).length,blocked:outcomes.filter(x=>x.blocked).length}));
    }
    if(runMode==='c')assert.equal(git(work,'rev-parse','HEAD'),baseline);
    const usage=keys=>Object.fromEntries(keys.map(k=>[k,
      receipts.reduce((n,r)=>n+Number(r.usage?.[k]||0),0)]));
    const stats=process.resourceUsage();
    const tasksDone=batchOutcomes.flatMap(x=>x.tasks);
    const record={
      date:'2026-11-07',
      experiment:'Claude Swarm / ZCode twenty distinct evidence-task pilot',
      mode:runMode,
      mode_description:runMode==='a'?'A direct single ZCode':
        runMode==='b'?'B fixed independent-call unanimous council':
        'C risk-adaptive patched Claude Swarm + restricted ZCode bridge',
      source_pin:pin,
      task_manifest_sha256:sha(fs.readFileSync(input)),
      task_manifest_public_id:'2026-11-07-claude-zcode-tasks20-manifest.json',
      source_paper_pins:privateData.papers,
      batch_size_tasks:2,
      batch_count:batchOutcomes.length,
      task_count:tasksDone.length,
      claim_count:tasksDone.length*2,
      provider_calls:receipts.length,
      checkpoint_hits:checkpointHits,
      new_provider_calls_this_run:receipts.length-checkpointHits,
      completed_calls:receipts.filter(x=>x.status==='COMPLETE').length,
      blocked_calls:receipts.filter(x=>x.status!=='COMPLETE').length,
      verified_tasks:tasksDone.filter(x=>x.verified).length,
      blocked_tasks:tasksDone.filter(x=>x.blocked).length,
      false_supported:tasksDone.reduce((n,x)=>n+x.false_supported,0),
      all_claims_correct:tasksDone.reduce((n,x)=>n+x.correct_claims,0),
      abstentions:tasksDone.reduce((n,x)=>n+x.abstentions,0),
      total_claims:tasksDone.length*2,
      call_elapsed_ms_p50:quantile(receipts.map(x=>x.elapsed_ms),.5),
      call_elapsed_ms_p95:quantile(receipts.map(x=>x.elapsed_ms),.95),
      batch_wall_ms_p50:quantile(batchOutcomes.map(x=>x.wall_ms),.5),
      batch_wall_ms_p95:quantile(batchOutcomes.map(x=>x.wall_ms),.95),
      summed_call_wall_ms:receipts.reduce((n,x)=>n+x.elapsed_ms,0),
      reported_usage:usage(['input_tokens','output_tokens','cache_read_input_tokens']),
      local_runner_rusage_delta:{
        user_cpu_us:stats.userCPUTime-resourceBefore.userCPUTime,
        system_cpu_us:stats.systemCPUTime-resourceBefore.systemCPUTime,
        fs_read_ops:stats.fsRead-resourceBefore.fsRead,
        fs_write_ops:stats.fsWrite-resourceBefore.fsWrite,
        max_rss_kb:stats.maxRSS
      },
      first_started_at:startedUTC,
      physical_zcode_parallelism:1,
      oracle_kind:'author-written labels, not blinded independent expert adjudication',
      role_receipts:receipts,
      batches:batchOutcomes,
      caveats:[
        'The 20 tasks contain distinct paper paragraphs but share four source papers',
        'Two claim labels per task are author-generated in advance; model never receives labels',
        'Two-task batches mean per-task independent latency distributions cannot be inferred',
        'Role calls use the same model family and no independent human expert adjudication',
        'Budget differences A/B/C are intentional tradeoff rather than fixed-cost comparison',
        'Runner CPU and RSS exclude child ZCode and tmux process resources',
        'No arbitrary tools, production, private sources, clinical records, real Claude agent, or direct source edits',
        'No automatic production approval; faults and incomplete results remain BLOCKED'
      ]
    };
    fs.mkdirSync(path.dirname(output),{recursive:true});
    fs.writeFileSync(output,JSON.stringify(record,null,2)+'\n');
    console.log('FINAL',JSON.stringify({mode:runMode,tasks:record.task_count,
      verified:record.verified_tasks,blocked:record.blocked_tasks,
      calls:record.provider_calls,provider_blocked:record.blocked_calls,
      false_supported:record.false_supported,p50:record.call_elapsed_ms_p50,
      p95:record.call_elapsed_ms_p95}));
  }finally{
    if(runMode==='c'){
      try{execFileSync('tmux',['kill-server'],{stdio:'ignore'});}catch{}
      if(oldEnv)for(const [key,value] of Object.entries(oldEnv)){
        if(value===undefined)delete process.env[key];else process.env[key]=value;
      }
      if(root)fs.rmSync(root,{recursive:true,force:true});
    }
  }
}
await main();
