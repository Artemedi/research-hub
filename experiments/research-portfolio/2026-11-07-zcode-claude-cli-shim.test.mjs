#!/usr/bin/env node
// Offline negative controls for the bounded ZCode CLI bridge; no provider calls.
import assert from 'node:assert/strict';
import {test} from 'node:test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const shim=path.resolve(import.meta.dirname,'2026-11-07-zcode-claude-cli-shim.mjs');
const cases=[
  {id:'case-a',url:'https://arxiv.org/html/2609.40111',
    source:'The sample has 30 examples.',claim:'The sample contains 30 examples.'},
  {id:'case-b',url:'https://arxiv.org/html/2609.11028',
    source:'The test failed and the reward was zero.',claim:'The test succeeded.'}
];
const withLab=fn=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'research-zcode-shim-test-'));
  try{
    const repo=path.join(root,'repo');
    const workerDir=path.join(repo,'.claude/orchestrator/workers');
    const resultDir=path.join(repo,'results');
    fs.mkdirSync(workerDir,{recursive:true});fs.mkdirSync(resultDir);
    const provider=path.join(root,'subagent.mjs');
    fs.writeFileSync(provider,[
      'const payload={stop_reason:"end_turn",model:"mock-only",usage:{},content:[{type:"text",',
      'text:JSON.stringify({judgments:[{id:"case-a",decision:"SUPPORTED"},{id:"case-b",decision:"NOT_SUPPORTED"}]})}]};',
      'process.stdout.write(JSON.stringify(payload));'
    ].join(''));
    const marker=path.join(workerDir,'swarm-test.done');
    const env={...process.env,RESEARCH_BRIDGE_COORDINATOR_DIR:repo,
      RESEARCH_BRIDGE_RESULT_DIR:resultDir,RESEARCH_BRIDGE_ZCODE_WRAPPER:provider};
    const data={id:'pilot',cases};
    const encoded=Buffer.from(JSON.stringify(data)).toString('base64');
    const prompt=(done=marker,payload=encoded)=>
      'RESEARCH_SWARM_JOB_BEGIN\n'+payload+'\nRESEARCH_SWARM_JOB_END\n'+
      '   - Create a file at: '+done+'\n';
    const run=(p)=>spawnSync(process.execPath,[shim,'--permission-mode','default','-p',p],
      {env,encoding:'utf8',timeout:15000});
    return fn({root,repo,workerDir,resultDir,provider,marker,env,data,prompt,run});
  }finally{fs.rmSync(root,{recursive:true,force:true});}
};

test('valid public-only job: model text JSON validated and trusted shim writes done',()=>{
  withLab(({marker,resultDir,prompt,run})=>{
    const out=run(prompt());
    assert.equal(out.status,0,out.stderr);
    assert.match(out.stdout,/BRIDGE_ACCEPTED_STRUCTURE:pilot/);
    assert.match(fs.readFileSync(marker,'utf8'),/^validated response/);
    const result=JSON.parse(fs.readFileSync(path.join(resultDir,'pilot.json')));
    assert.deepEqual(result.labels.map(x=>x.id),['case-a','case-b']);
    assert.equal(result.status,'STRUCTURE_VALID');
  });
});

test('invalid or missing bound job marker fails before any provider call',()=>{
  withLab(({run,resultDir})=>{
    const out=run('regular Claude prompt without an approved public evidence payload');
    assert.equal(out.status,17);
    assert.match(out.stderr,/BAD_JOB_MARKER/);
    assert.deepEqual(fs.readdirSync(resultDir),[]);
  });
});

test('non-https source URL is rejected and result is not accepted',()=>{
  withLab(({run,prompt,data,resultDir})=>{
    const poisoned={...data,cases:data.cases.map((x,i)=>i?x:{...x,url:'file:///private/tokens'})};
    const out=run(prompt(undefined,Buffer.from(JSON.stringify(poisoned)).toString('base64')));
    assert.equal(out.status,17);
    assert.match(out.stderr,/UNSAFE_JOB_ITEM/);
    assert.deepEqual(fs.readdirSync(resultDir),[]);
  });
});

test('outside completion path is rejected',()=>{
  withLab(({run,prompt,root,resultDir})=>{
    const out=run(prompt(path.join(root,'outside.done')));
    assert.equal(out.status,17);
    assert.match(out.stderr,/UNSAFE_DONE_PATH/);
    assert.deepEqual(fs.readdirSync(resultDir),[]);
  });
});

test('duplicate completion marker is rejected',()=>{
  withLab(({run,prompt,marker,resultDir})=>{
    const out=run(prompt()+'   - Create a file at: '+marker+'\n');
    assert.equal(out.status,17);
    assert.match(out.stderr,/BAD_DONE_MARKER/);
    assert.deepEqual(fs.readdirSync(resultDir),[]);
  });
});

test('provider thinking metadata may accompany valid text without tool execution',()=>{
  withLab(({provider,run,prompt,resultDir})=>{
    fs.writeFileSync(provider,
      'process.stdout.write(JSON.stringify({stop_reason:"end_turn",content:['+
      '{type:"thinking",thinking:"non-executable provider metadata"},'+
      '{type:"text",text:JSON.stringify({judgments:[{id:"case-a",decision:"SUPPORTED"},{id:"case-b",decision:"NOT_SUPPORTED"}]})}]}))');
    const out=run(prompt());
    assert.equal(out.status,0,out.stderr);
    assert.equal(JSON.parse(fs.readFileSync(path.join(resultDir,'pilot.json'))).status,'STRUCTURE_VALID');
  });
});

test('provider tool-use blocks are rejected even with valid text',()=>{
  withLab(({provider,run,prompt,resultDir})=>{
    fs.writeFileSync(provider,
      'process.stdout.write(JSON.stringify({stop_reason:"end_turn",content:['+
      '{type:"text",text:JSON.stringify({judgments:[{id:"case-a",decision:"SUPPORTED"},{id:"case-b",decision:"NOT_SUPPORTED"}]})},'+
      '{type:"tool_use",id:"toolu_test",name:"bash",input:{command:"echo test"}}]}))');
    const out=run(prompt());
    assert.equal(out.status,17);
    assert.match(out.stderr,/UNEXPECTED_TOOL_OR_NON_TEXT_BLOCK/);
    assert.deepEqual(fs.readdirSync(resultDir),[]);
  });
});
