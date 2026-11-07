#!/usr/bin/env node
/**
 * Bounded synthetic transport replay of KVTether's ordered asynchronous export
 * contract (Section 7), not KVTether implementation or physical KV validation.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';

const output=path.resolve(process.env.OUTPUT||'');
const sha=s=>createHash('sha256').update(s).digest('hex');
const primitives=['append','fork','pin','one_off','spawn','replace','remove','unpin'];
const complete=[];
function eventHash(e) {
  return sha(JSON.stringify([e.context,e.seq,e.op,e.prev,e.version]));
}
function validate(stream,expectedContext){
  let prev='GENESIS',next=0;
  for(const e of stream){
    if(e.context!==expectedContext)return 'wrong_context';
    if(e.seq!==next)return 'out_of_order_or_missing';
    if(e.prev!==prev)return 'invalid_chain';
    if(e.digest!==eventHash(e))return 'payload_mutation';
    prev=e.digest;next++;
  }
  return next===primitives.length?'PASS':'incomplete';
}
const rejection={};
for(let seed=0;seed<25;seed++){
  const context='synthetic-context-'+seed;
  let prev='GENESIS';
  const original=[];
  for(let seq=0;seq<primitives.length;seq++){
    const e={context,seq,op:primitives[seq],prev,version:seed+1};
    e.digest=eventHash(e);
    original.push(e);
    prev=e.digest;
  }
  const delivered=[];
  await Promise.all(original.map(async e=>{
    // deterministic transport completion order intentionally reversed.
    await new Promise(resolve=>setTimeout(resolve,(primitives.length-1-e.seq)*2));
    delivered.push(e);
  }));
  const direct=validate(delivered,context);
  const reordered=[...delivered].sort((a,b)=>a.seq-b.seq);
  const recovered=validate(reordered,context);
  assert.notEqual(direct,'PASS');
  assert.equal(recovered,'PASS');
  complete.push({id:seed,context,events:original,transport_order:delivered.map(e=>e.seq),
    naive_validation:direct,ordered_validation:recovered});
}
const base=complete[0].events;
const cases=[
  ['duplicate',[...base.slice(0,2),base[1],...base.slice(2)]],
  ['missing',[...base.slice(0,4),...base.slice(5)]],
  ['wrong_prev',base.map((e,i)=>i===3?{...e,prev:'0'.repeat(64)}:e)],
  ['wrong_context',base.map((e,i)=>i===4?{...e,context:'foreign-context'}:e)],
  ['wrong_payload',base.map((e,i)=>i===2?{...e,op:'unpin'}:e)]
];
for(const [label,changed] of cases){
  const observed=validate(changed,complete[0].context);
  rejection[label]={observed,rejected:observed!=='PASS'};
}
assert.equal(complete.length,25);
assert(complete.every(x=>x.naive_validation!=='PASS'&&x.ordered_validation==='PASS'));
assert(Object.values(rejection).every(x=>x.rejected));
const result={
  date:'2026-11-07',study:'kvtether',
  full_source_url:'https://arxiv.org/html/2609.39819v1',
  full_source_html_sha256:'d0c211ef0bc8cf6583ba7acb1b92b9609e0f44537062e7402a750d5e8a270bfb',
  lab:'synthetic eight primitive event order with async arrival and ordered replay',
  synthetic_sequences:complete.length,
  events_per_sequence:primitives.length,
  unordered_sequences_rejected:complete.filter(x=>x.naive_validation!=='PASS').length,
  ordered_sequences_accepted:complete.filter(x=>x.ordered_validation==='PASS').length,
  negative_controls:rejection,
  negative_controls_passed:Object.values(rejection).filter(x=>x.rejected).length,
  oracle:'locally generated event seq and SHA chain; read-only executable replay; not independent runtime trace',
  sequences:complete,
  verdict:'PASS_SYNTHETIC_ORDER_CONTRACT_ONLY',
  limitations:[
    'No KVTether author implementation or inference serving engine exercised',
    'No physical KV ownership, prefix tokenization, cache hits, GPU/CPU transfer or policy correctness',
    'Event payload hash is same-UID forgeable and not a signature or transaction log',
    'A sorting replay may hide missing causal order if no sequence/chain is enforced',
    'No resource overhead or claimed latency/pricing savings measured',
    'No live user or production data'
  ]
};
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({sequences:result.synthetic_sequences,
  unordered_rejected:result.unordered_sequences_rejected,
  ordered_accepted:result.ordered_sequences_accepted,
  negatives:result.negative_controls_passed}));
