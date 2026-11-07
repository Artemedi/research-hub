#!/usr/bin/env -S tsx
/** Real DSH wire serializer, invariant tool schemas, permuted observation keys. */
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { pathToFileURL } from 'node:url'

const root=path.resolve(process.env.DSH_RUNTIME_ROOT??'')
const fixturePath=path.resolve(process.env.FIXTURE??'')
const toolWirePath=path.resolve(process.env.TOOL_WIRES??'')
const outputPath=path.resolve(process.env.OUTPUT??'')
const pin='3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc'
const sourceHash='36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162'
const sha=(value:Buffer|string)=>createHash('sha256').update(value).digest('hex')
assert.equal(execFileSync('git',['-C',root,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),pin)
const sourcePath=path.join(root,'packages/llm/llm-deepseek/src/serialize.ts')
assert.equal(sha(fs.readFileSync(sourcePath)),sourceHash)
const {serializeRequest}=await import(pathToFileURL(sourcePath).href)
const fixtureBytes=fs.readFileSync(fixturePath)
const fixture=JSON.parse(fixtureBytes.toString('utf8'))
const toolWireBytes=fs.readFileSync(toolWirePath)
const toolsSource=JSON.parse(toolWireBytes.toString('utf8'))
assert.equal(fixture.case_count,16)
assert.equal(toolsSource.dsh_runtime_pin,pin)
const tools=toolsSource.wires[0].wire.tools.map((t:any)=>t.function)
const sort=(x:any):any=>Array.isArray(x)?x.map(sort):
  x!==null&&typeof x==='object'?Object.fromEntries(Object.entries(x)
    .sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,sort(v)])):x
const observation=(row:any,variant:string)=>{
  const base={
    id:row.id,
    current_request:row.current_request,
    previous_observation:row.previous_observation,
    context_metadata:row.context_metadata
  }
  if(variant==='A')return base
  return Object.fromEntries(Object.entries(base).reverse().map(([k,v])=>[
    k,v!==null&&typeof v==='object'&&!Array.isArray(v)?
      Object.fromEntries(Object.entries(v).reverse()):v
  ]))
}
const system='You are a read-only tool router receiving structured state observations. For EACH observation, select a tool for current_request ONLY, or NONE if current_request explicitly says no tool. Historical previous_observation is stale, not the current instruction. Ignore order of JSON keys. Do not execute tools. Return exactly one selection and arguments per id.'
const wires=[]
for(let batch=0;batch<2;batch++){
  const rows=fixture.cases.slice(batch*8,batch*8+8)
  assert.equal(rows.length,8)
  for(const variant of ['A','B']){
    const input={observations:rows.map((r:any)=>observation(r,variant))}
    const request=serializeRequest({
      provider:'deepseek-official',model:'glm-5.3-flash',
      system,
      messages:[{role:'user',content:[{type:'text',text:JSON.stringify(input)}]}] as any,
      tools,temperature:0,maxTokens:2500
    })
    wires.push({batch,variant,task_ids:rows.map((r:any)=>r.id),
      wire_sha256:sha(JSON.stringify(request)),wire:request})
  }
  const a=wires.at(-2)!,b=wires.at(-1)!
  assert.deepEqual(a.wire.tools,b.wire.tools)
  assert.notEqual(JSON.stringify(a.wire.messages),JSON.stringify(b.wire.messages))
  assert.deepEqual(
    sort(JSON.parse((a.wire.messages.at(-1) as any).content)),
    sort(JSON.parse((b.wire.messages.at(-1) as any).content))
  )
  for(const w of [a,b]){
    assert.equal((w.wire.messages[0] as any).content,system)
    assert.deepEqual((w.wire.tools as any[]).map(x=>x.function.name),
      tools.map((x:any)=>x.name))
  }
}
const result={
  date:'2026-11-07',study:'decision-geometry-harness',
  dsh_runtime_pin:pin,serializer_source_sha256:sourceHash,
  fixture_sha256:sha(fixtureBytes),
  tool_source_wires_sha256:sha(toolWireBytes),
  variants:['A','B'],batch_count:2,model_requested:'glm-5.3-flash',
  sampling_requested:{temperature:0,max_tokens:2500},
  intervention:'Only JSON key order in nested model-facing state observation; exact tools, messages semantics and user intent retained',
  oracle_check:'Actual dsh-runtime serializeRequest; deep sorted JSON equality of observation objects and exact tools schema equality',
  wires,
  limitation:'DSH wire is passed as inert JSON to ZCode, not executed by native DSH agent process'
}
fs.mkdirSync(path.dirname(outputPath),{recursive:true})
fs.writeFileSync(outputPath,JSON.stringify(result,null,2)+'\n')
console.log(JSON.stringify({wires:wires.length,bytes:wires.map(w=>JSON.stringify(w.wire).length),
  sha256:sha(fs.readFileSync(outputPath))}))
