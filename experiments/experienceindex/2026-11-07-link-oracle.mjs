#!/usr/bin/env node
/**
 * Independent JS structural verifier of the pinned public Markdown navigation
 * oracle. Does not reuse the Python A/B source code or run any models.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const root = path.resolve(process.env.RESEARCH_HUB || '.');
const input = path.resolve(process.env.EVIDENCE || '');
const output = path.resolve(process.env.OUTPUT || '');
const recorded = JSON.parse(fs.readFileSync(input,'utf8'));
const rev = recorded.research_hub_pin;
assert.match(rev,/^[a-f0-9]{40}$/);
const sha = value=>createHash('sha256').update(value).digest('hex');
const gitText = name=>execFileSync('git',['-C',root,'show',rev+':'+name],{
  encoding:'utf8',maxBuffer:2_000_000
});
const cache=new Map();
const content=name=>{
  if(!cache.has(name))cache.set(name,gitText(name));
  return cache.get(name);
};
const linksOf=src=>{
  const body=content(src);
  const found=[];
  for(const match of body.matchAll(/\]\((\.\.\/reviews\/[^)#]+\.md)(?:#[^)]*)?\)/g)){
    const target=path.posix.normalize('studies/'+match[1]);
    if(!target.startsWith('reviews/'+src.slice(8,-3)+'/'))continue;
    try {content(target);found.push(target);}catch { /* broken source link */ }
  }
  return [...new Set(found)].sort();
};
function verify(row){
  const src=row.source, target=row.target;
  assert.match(src,/^studies\/[a-z0-9-]+\.md$/);
  assert.match(target,/^reviews\/[a-z0-9-]+\/[^/]+\.md$/);
  assert.equal(sha(content(src)),row.source_sha256);
  assert.equal(sha(content(target)),row.target_sha256);
  const links=linksOf(src);
  assert(links.length>0);
  assert.equal(target,links.at(-1));
  for(const key of ['baseline_top5','augmented_top5']){
    assert(Array.isArray(row[key]));
    assert(row[key].length>=1&&row[key].length<=5);
    for(const location of row[key])content(location);
  }
  assert.equal(row.baseline_review_at5,row.baseline_top5.includes(target));
  assert.equal(row.augmented_review_at5,row.augmented_top5.includes(target));
  return true;
}
let validated=0;
for(const row of recorded.cases_detail){
  verify(row);
  validated++;
}
assert.equal(validated,recorded.cases);
const mutated={...recorded.cases_detail[0],source_sha256:'0'.repeat(64)};
assert.throws(()=>verify(mutated),/Expected values to be strictly equal/);
const hitsBase=recorded.cases_detail.filter(x=>x.baseline_top5.includes(x.target)).length;
const hitsAfter=recorded.cases_detail.filter(x=>x.augmented_top5.includes(x.target)).length;
assert.equal(hitsBase,recorded.baseline_review_at5);
assert.equal(hitsAfter,recorded.augmented_review_at5);
assert.equal(hitsAfter,33);
assert.equal(hitsBase,32);
const result={
  date:'2026-11-07',
  study:'experienceindex',
  source_pin:rev,
  initial_experiment_sha256:sha(fs.readFileSync(input)),
  independent_js_oracle:'git show commit:path + literal Markdown link + exact SHA and latest explicit review',
  cases_validated:validated,
  unexpected_cases:0,
  injected_wrong_source_hash_rejected:true,
  navigation_hit_at5:{baseline:hitsBase,augmented:hitsAfter},
  limitation:'Checks href/path/hash and self-reported rank membership; it does not independently reproduce BM25 scoring or semantic relevance',
  status:'PASS_BOUNDED_NAVIGATION_PROVENANCE'
};
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
