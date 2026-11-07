#!/usr/bin/env -S tsx
/** Reuse real pinned DSH serializeRequest; do not mutate DSH or expose tools. */
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { pathToFileURL } from 'node:url'

const root = path.resolve(process.env.DSH_RUNTIME_ROOT ?? '')
const fixturePath = path.resolve(process.env.FIXTURE ?? '')
const outputPath = path.resolve(process.env.OUTPUT ?? '')
const pin = '3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc'
const sourceHash = '36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162'
const sha = (value: Buffer|string) => createHash('sha256').update(value).digest('hex')
assert.equal(execFileSync('git',['-C',root,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),pin)
const sourcePath = path.join(root,'packages/llm/llm-deepseek/src/serialize.ts')
assert.equal(sha(fs.readFileSync(sourcePath)),sourceHash)
const {serializeRequest} = await import(pathToFileURL(sourcePath).href)
const fixtureBytes=fs.readFileSync(fixturePath)
const fixtures=JSON.parse(fixtureBytes.toString('utf8'))
assert.equal(fixtures.source_pin,pin)
assert.equal(fixtures.case_count,24)
const tools = [
  {name:'inspect_sql_plan',description:'Read the SQL execution plan for the specified database and query_id (read-only).',parameters:{type:'object',properties:{database:{type:'string',description:'Database name.'},query_id:{type:'string',description:'SQL query identifier.'}},required:['database','query_id'],additionalProperties:false}},
  {name:'inspect_pg_relation',description:'Read PostgreSQL relation statistics for a specific schema and relation (read-only).',parameters:{type:'object',properties:{schema:{type:'string',description:'PostgreSQL schema.'},relation:{type:'string',description:'PostgreSQL relation name.'}},required:['schema','relation'],additionalProperties:false}},
  {name:'get_job_status',description:'Read status for a job ID without changing the job.',parameters:{type:'object',properties:{job_id:{type:'string',description:'Exact job id.'}},required:['job_id'],additionalProperties:false}},
  {name:'list_experiment_artifacts',description:'List existing research artifacts by study and artifact kind.',parameters:{type:'object',properties:{study:{type:'string',description:'Research study id.'},kind:{type:'string',enum:['report','data','experiment'],description:'Artifact kind.'}},required:['study','kind'],additionalProperties:false}},
  {name:'read_file_range',description:'Read an inclusive line range from a permitted synthetic file path, without editing.',parameters:{type:'object',properties:{path:{type:'string',description:'Relative file path.'},start_line:{type:'integer',description:'First line inclusive.'},end_line:{type:'integer',description:'Last line inclusive.'}},required:['path','start_line','end_line'],additionalProperties:false}},
  {name:'find_runbook',description:'Find a runbook for a topic at an exact revision, without modifying it.',parameters:{type:'object',properties:{topic:{type:'string',description:'Runbook topic.'},revision:{type:'string',description:'Revision tag.'}},required:['topic','revision'],additionalProperties:false}},
  {name:'sum_numbers',description:'Select a calculator for an explicit array of integers.',parameters:{type:'object',properties:{numbers:{type:'array',items:{type:'integer'},description:'Integers to sum.'}},required:['numbers'],additionalProperties:false}},
]
const schemaB = [...tools].reverse().map(tool=>({
  ...tool,
  parameters:{...tool.parameters,properties:Object.fromEntries(
    Object.entries(tool.parameters.properties).reverse()
  )},
}))
const canon=(value:unknown):unknown=>Array.isArray(value)?value.map(canon):
  value!==null&&typeof value==='object'?
    Object.fromEntries(Object.entries(value).sort(([a],[b])=>a.localeCompare(b))
      .map(([k,v])=>[k,canon(v)])):value
const system='You are a read-only tool router. For each task, select exactly one named tool, or NONE if the instruction explicitly needs no tool. Do not execute anything. Do not invent arguments. Return one result per id.'
const wires=[]
for(let batch=0;batch<3;batch++){
  const tasks=fixtures.cases.slice(batch*8,batch*8+8)
    .map((x:{id:string;instruction:string})=>({id:x.id,instruction:x.instruction}))
  assert.equal(tasks.length,8)
  for(const variant of ['A','B'] as const){
    const request=serializeRequest({
      provider:'deepseek-official',model:'glm-5.3-flash',
      system,messages:[{role:'user',content:[{type:'text',
        text:JSON.stringify({tasks})}]}] as any,
      tools:variant==='A'?tools:schemaB,
      temperature:0, maxTokens:2500,
    })
    wires.push({batch,variant,task_ids:tasks.map((t:{id:string})=>t.id),
      wire_sha256:sha(JSON.stringify(request)),
      wire:request})
  }
  const a=wires.at(-2)!,b=wires.at(-1)!
  assert.equal(JSON.stringify(a.wire.messages),JSON.stringify(b.wire.messages))
  assert.equal(a.wire.model,b.wire.model)
  const compare=(req:any)=>[...req.tools].map(x=>x.function)
    .sort((x,y)=>x.name.localeCompare(y.name)).map(canon)
  assert.deepEqual(compare(a.wire),compare(b.wire))
  assert.notEqual(JSON.stringify(a.wire.tools),JSON.stringify(b.wire.tools))
}
const result={
 date:'2026-11-07',study:'decision-geometry-harness',
 dsh_runtime_pin:pin,serializer_source_sha256:sourceHash,
 fixture_sha256:sha(fixtureBytes),variants:['A','B'],batch_count:3,
 model_requested:'glm-5.3-flash',sampling_requested:{temperature:0,max_tokens:2500},
 intervention:'Reverse tool-definition order AND order of properties within every tool; model-facing instructions and semantics identical',
 oracle_check:'Real dsh-runtime serializeRequest + canonical equality of tool semantics and exact messages',
 wires,
 limitation:'The DeepSeek wire is passed as quoted data to a ZCode text-only model, not natively executed through the DSH provider or tool API'
}
fs.mkdirSync(path.dirname(outputPath),{recursive:true})
fs.writeFileSync(outputPath,JSON.stringify(result,null,2)+'\n')
console.log(JSON.stringify({batches:3,variants:2,sha256:sha(fs.readFileSync(outputPath)),
  wire_bytes:wires.map(w=>[w.batch,w.variant,JSON.stringify(w.wire).length])}))
