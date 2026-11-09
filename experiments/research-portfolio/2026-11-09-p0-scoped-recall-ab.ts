/**
 * Run from a pinned source-only Git archive of dsh-team-context.
 * Baseline mergeScopedRecall remains unmodified, candidate filters by a
 * synthetic approved source-id and SHA manifest. No runtime adapter exists.
 */
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { mergeScopedRecall } from './src/core/scoped-recall.js';
const sha = (s: string) => createHash('sha256').update(s).digest('hex');
const argv = process.argv.slice(2);
const sourcePath = argv[argv.indexOf('--source')+1];
const outputPath = argv[argv.indexOf('--out')+1];
if(!sourcePath||!outputPath)throw Error('Pass --source and --out');
const scopeHash = createHash('sha256').update(fs.readFileSync(sourcePath)).digest('hex');
const record = (i:number,n:number,score:number,content:string)=>({
  entry:{id:String(i)+'-'+String(n),type:'docs' as const,
    path:'docs/'+i+'-'+n+'.md',content,title:'synthetic',
    tags:[],titleTokens:[],tagTokens:[],bodyTokens:[]},
  score,matchedTerms:['synthetic'],missingTerms:[],snippet:content,
});
function candidate(project:ReturnType<typeof record>[],user:ReturnType<typeof record>[],allow:Map<string,string>){
  const eligible=(r:ReturnType<typeof record>)=>allow.get(r.entry.type+':'+r.entry.path)===sha(r.entry.content);
  return mergeScopedRecall(project.filter(eligible),user.filter(eligible),5);
}
function oracle(results:ReturnType<typeof mergeScopedRecall>,approved:Map<string,string>,gold:string|null){
  const keys=results.map(r=>r.entry.type+':'+r.entry.path);
  const invalid=results.filter(r=>approved.get(r.entry.type+':'+r.entry.path)!==sha(r.entry.content)).length;
  return {invalid,correct:gold?Number(keys.includes(gold)):Number(results.length===0)};
}
const records=[];
const timing={baseline:[] as number[],candidate:[] as number[]};
for(let i=0;i<60;i++){
  const ood=i>=45;
  const project:ReturnType<typeof record>[]=[];
  const user:ReturnType<typeof record>[]=[];
  const approved=new Map<string,string>();
  let gold:string|null=null;
  if(!ood){
    for(let j=0;j<3;j++){
      const doc=record(i,j,0.76-j*0.06,'stable-public-text-'+i+'-'+j);
      project.push(doc);
      approved.set(doc.entry.type+':'+doc.entry.path,sha(doc.entry.content));
      if(j===0)gold=doc.entry.type+':'+doc.entry.path;
    }
  }
  for(let j=3;j<10;j++)project.push(record(i,j,0.99-j*0.003,'SYSTEM OVERRIDE fake '+i+'-'+j));
  user.push(record(i,10,0.97,'untrusted user scope '+i));
  const results:Record<string,{invalid:number;correct:number;returned:number}>={};
  const arms=i%2===0?(['baseline','candidate'] as const):(['candidate','baseline'] as const);
  for(const arm of arms){
    const started=process.hrtime.bigint();
    const got=arm==='baseline'?mergeScopedRecall(project,user,5):candidate(project,user,approved);
    const elapsed=Number(process.hrtime.bigint()-started);
    timing[arm].push(elapsed);
    results[arm]={...oracle(got,approved,gold),returned:got.length};
  }
  records.push({id:i,ood,gold_id:gold,approved_count:approved.size,
    baseline:results.baseline,candidate:results.candidate});
}
const aggregate=(arm:'baseline'|'candidate')=>({
  cases:records.length,
  correct_or_abstain:records.reduce((n,r)=>n+r[arm].correct,0),
  wrong_source_count:records.reduce((n,r)=>n+r[arm].invalid,0),
  ood_abstained:records.filter(r=>r.ood&&r[arm].correct===1).length,
});
const p95=(xs:number[])=>xs.sort((a,b)=>a-b)[Math.floor((xs.length-1)*.95)];
const result={
  protocol:'retrieval',pair:'agent-mosaic/dsh-team-context',
  source_git_sha:'b7268d12581be2705c5e675991126c25f735701a',
  source_file:'src/core/scoped-recall.ts',source_file_sha256:scopeHash,
  scope:'REAL_MERGE_SCOPED_RECALL_FUNCTION_WITH_SYNTHETIC_MANIFEST_GUARD',
  records,baseline:aggregate('baseline'),candidate:aggregate('candidate'),
  dataset:{cases:60,regular:45,ood:15,gold:'exact source ID and content SHA'},
  timing:{unit:'nanoseconds_per_call',samples_per_arm:60,
    p95_baseline_ns:p95(timing.baseline),p95_candidate_ns:p95(timing.candidate)},
  negatives:['forged high-score source','stale source hash','wrong-scope user source'],
  limitations:['Synthetic approved manifest is not a deployed runtime permission oracle',
    'Only unchanged original mergeScopedRecall was executed; not full semantic retrieval or model generation',
    'Candidate is unintegrated and not a source-level patch to the target repository',
    'Not a proof of improved relevance/quality on a real held-out corpus'],
};
fs.writeFileSync(outputPath,JSON.stringify(result,null,2)+'\n');
console.log('SCOPED_RECALL_AB',JSON.stringify({baseline:result.baseline,candidate:result.candidate,timing:result.timing}));
