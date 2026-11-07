#!/usr/bin/env node
/**
 * GAD-inspired coordination contract experiment: real pinned dsh-runtime task
 * graph validator + isolated fake receipts. NOT reproduction of GAD agent/model.
 * No source edits, model calls, network, production or private data.
 *
 * Run with node --experimental-transform-types <this-script>.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';

const source=path.resolve(process.env.DSH_RUNTIME_SOURCE||'');
const output=path.resolve(process.env.OUTPUT||'');
const pin='3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc';
const sha=value=>createHash('sha256').update(value).digest('hex');
const codePath=path.join(source,'packages/experimental/agent-team/src/task-graph.ts');
assert.equal(execFileSync('git',['-C',source,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),pin);
assert.equal(sha(fs.readFileSync(codePath)),'a726081289a2f7a848f69109a750db3ead0d95b88ab0adfdae0477f749b8f490');
const {assertTaskGraphCandidate,TeamTaskGraphError}=await import(pathToFileURL(codePath).href);

const classifications=['linear','diamond','duplicate','self','missing','deleted','cycle'];
const vectors=[];
for(let seed=0;seed<5;seed++){
  const a='a'+seed,b='b'+seed,c='c'+seed;
  const snapshots=(depsA=[],depsB=[a],statusB='pending')=>[
    {id:a,status:'pending',blockedBy:depsA},
    {id:b,status:statusB,blockedBy:depsB}
  ];
  for(const kind of classifications){
    let current,candidate,expected;
    if(kind==='linear'){
      current=snapshots();candidate={id:c,status:'pending',blockedBy:[b]};expected='PASS';
    }else if(kind==='diamond'){
      current=snapshots([],[]);candidate={id:c,status:'pending',blockedBy:[a,b]};expected='PASS';
    }else if(kind==='duplicate'){
      current=snapshots();candidate={id:c,status:'pending',blockedBy:[a,a]};expected='duplicate';
    }else if(kind==='self'){
      current=snapshots();candidate={id:c,status:'pending',blockedBy:[c]};expected='cycle';
    }else if(kind==='missing'){
      current=snapshots();candidate={id:c,status:'pending',blockedBy:['absent'+seed]};expected='missing';
    }else if(kind==='deleted'){
      current=snapshots([],[], 'deleted');candidate={id:c,status:'pending',blockedBy:[b]};expected='missing';
    }else{
      current=snapshots([c],[a]);candidate={id:c,status:'pending',blockedBy:[b]};expected='cycle';
    }
    let observed='PASS';
    try{assertTaskGraphCandidate(current,candidate);}
    catch(error){
      if(!(error instanceof TeamTaskGraphError))throw error;
      observed=error.violation;
    }
    vectors.push({id:kind+'-'+seed,expected,observed,matched:observed===expected});
  }
}
assert.equal(vectors.length,35);
assert(vectors.every(x=>x.matched));

function sourceResult(run,id,status='VERIFIED',scope='project'){
  const bytes='verified evidence for '+run+'::'+id;
  return {id,status,scope,bytes,
    expected_hash:sha(bytes)};
}
function dependencyContext(goal,acceptance,dependencyIds,allResults){
  const resultById=new Map(allResults.map(x=>[x.id,x]));
  const accepted=[],errors=[];
  for(const name of dependencyIds){
    const row=resultById.get(name);
    if(!row)errors.push('missing:'+name);
    else if(row.status!=='VERIFIED')errors.push('unverified:'+name);
    else if(sha(row.bytes)!==row.expected_hash)errors.push('stale:'+name);
    else if(row.scope!=='project')errors.push('scope:'+name);
    else accepted.push(name);
  }
  if(!goal || !acceptance)errors.push('missing_goal_or_acceptance');
  return {valid:errors.length===0,verified_deps:accepted,errors};
}

const kinds=['clean','unverified','stale','crossscope','rootfail','missing_dep','missing_acceptance'];
const trials=[];
let flatEvidenceTotal=0,scopedEvidenceTotal=0,naiveFalseAccept=0,guardedFalseAccept=0;
for(let seed=0;seed<5;seed++){
  for(const kind of kinds){
    const id=kind+'-'+seed;
    const results=[
      sourceResult(id,'collect'),sourceResult(id,'write'),
      sourceResult(id,'audit'),sourceResult(id,'unrelated-A'),
      sourceResult(id,'unrelated-B'),sourceResult(id,'unrelated-C')
    ];
    const deps=['write','audit'];
    let goal='Integrate verified artifacts into accepted result';
    let acceptance='Root checks expected output hash and complete contract';
    let rootCheck=true;
    if(kind==='unverified')results[1].status='DONE';
    if(kind==='stale')results[2].bytes='tampered artifact: '+id;
    if(kind==='crossscope')results[2].scope='foreign-project';
    if(kind==='rootfail')rootCheck=false;
    if(kind==='missing_dep')deps.push('missing-'+seed);
    if(kind==='missing_acceptance')acceptance='';
    const context=dependencyContext(goal,acceptance,deps,results);
    // Deliberately naive counterfactual: accepting reported child DONE without
    // independent root verification, and sharing all completed global results.
    const flat=results.filter(x=>x.status==='VERIFIED'||x.status==='DONE');
    const naiveAccepted=true; // synthetic baseline always self-reports done
    const guardedAccepted=context.valid&&rootCheck;
    const expected=kind==='clean';
    const irrelevant=flat.filter(x=>!deps.includes(x.id)).length;
    flatEvidenceTotal+=flat.length;
    scopedEvidenceTotal+=context.verified_deps.length;
    naiveFalseAccept+=Number(naiveAccepted&&!expected);
    guardedFalseAccept+=Number(guardedAccepted&&!expected);
    const row={id,kind,expected,naive_accepted:naiveAccepted,
      guarded_accepted:guardedAccepted,errors:context.errors,
      flat_context_items:flat.length,scoped_context_items:context.verified_deps.length,
      irrelevant_flat_items:irrelevant,root_verified:rootCheck};
    assert.equal(guardedAccepted,expected,id);
    if(kind!=='clean')assert(context.errors.length>0||!rootCheck);
    if(kind==='clean')assert.deepEqual(context.verified_deps,['write','audit']);
    trials.push(row);
  }
}
assert.equal(trials.length,35);
assert.equal(naiveFalseAccept,30);
assert.equal(guardedFalseAccept,0);
assert.equal(trials.filter(x=>x.guarded_accepted).length,5);
const result={
  date:'2026-11-07',study:'goal-aware-dynamic-collaboration',
  full_paper_url:'https://arxiv.org/html/2610.39193v1',
  full_paper_html_sha256:process.env.PAPER_SHA256||null,
  dsh_runtime_pin:pin,source_file:'packages/experimental/agent-team/src/task-graph.ts',
  source_sha256:sha(fs.readFileSync(codePath)),
  graph_vectors_total:vectors.length,graph_vectors_passed:vectors.filter(x=>x.matched).length,
  graph_negative_vectors:vectors.filter(x=>x.expected!=='PASS').length,
  workflow_cases:trials.length,workflow_expected_accept:5,
  workflow_guarded_accept:trials.filter(x=>x.guarded_accepted).length,
  naive_false_accept:naiveFalseAccept,guarded_false_accept:guardedFalseAccept,
  all_global_evidence_items:flatEvidenceTotal,
  scoped_verified_evidence_items:scopedEvidenceTotal,
  flat_unrelated_items:trials.reduce((n,x)=>n+x.irrelevant_flat_items,0),
  execution:'actual upstream TS graph validator via Node transform-types + deterministic external fake receipts',
  oracle:'fixed authored graph-error and root-acceptance labels; independent of model; not natural production workload',
  vectors,trials,
  status:'BOUNDED_GRAPH_AND_ROOT_GATE_VERIFIED',
  caveats:[
    'Real dsh-runtime graph validator tested but GAD controller/LLM not implemented or executed',
    'Naive accept-all self-report baseline is intentionally weak, not a measured MAS comparator',
    'Synthetic receipt hash and scopes are trusted in one process, not cryptographic worker isolation',
    'No autonomous model tool calls, large coding benchmarks or genuine long-horizon task accuracy',
    'No live tool I/O, production secrets or user data, and no edits to dsh-runtime',
    'Root acceptance and dependency filtering are local lab logic, not existing dsh-runtime behavior'
  ]
};
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log('GAD',JSON.stringify({graph:result.graph_vectors_passed,workflow:result.workflow_cases,
  guarded_accept:result.workflow_guarded_accept,naive_false_accept:naiveFalseAccept,
  guarded_false_accept:guardedFalseAccept,evidence_items:[flatEvidenceTotal,scopedEvidenceTotal]}));
