#!/usr/bin/env -S tsx
/** Pin original Chartli TS renderer; generate public synthetic SVG fixtures. */
import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'
import {execFileSync} from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import {pathToFileURL} from 'node:url'

const source=path.resolve(process.env.CHARTLI_SOURCE??'')
const output=path.resolve(process.env.OUTPUT??'')
const svgDir=path.resolve(process.env.SVG_DIR??'')
const pin='3b39b97aeb564646437b2b7501b60541994d7575'
const sha=(v:Buffer|string)=>createHash('sha256').update(v).digest('hex')
const hashes={
 'src/utils/svg.ts':'81b05c1000e389b80e11a87f09e74e889a899462e14cd322e9f259acb431db7e',
 'src/utils/normalize.ts':'98adfcf1ebb0aa7793c194b1eb5e8e484004c52288fad0a692bee6c21503a438'
}
assert.equal(execFileSync('git',['-C',source,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),pin)
for(const [p,h] of Object.entries(hashes))assert.equal(sha(fs.readFileSync(path.join(source,p))),h)
const {normalizeData}=await import(pathToFileURL(path.join(source,'src/utils/normalize.ts')).href)
const {renderSvg}=await import(pathToFileURL(path.join(source,'src/utils/svg.ts')).href)
const a=[[0],[5],[10]],b=[[1,4],[3,9],[8,1]]
const cases=[
 {id:'single_circles',rows:a,options:{}},
 {id:'single_lines',rows:a,options:{mode:'lines'}},
 {id:'multi_circles_legend',rows:b,options:{seriesLabels:['A','B']}},
 {id:'multi_lines_legend',rows:b,options:{mode:'lines',seriesLabels:['A','B']}},
 {id:'escaped_x_y_labels',rows:a,options:{xAxisLabel:'x & < > \' "',yAxisLabel:'y & < > \' "',xLabels:['<script>&',"O'Reilly",'a"b'],showDataLabels:true}},
 {id:'escaped_legend',rows:b,options:{seriesLabels:['<script>alert(1)</script>','control & "tick"']}},
 {id:'empty',rows:[],options:{}},
 {id:'single_point',rows:[[3]],options:{}},
 {id:'flat_three',rows:[[4],[4],[4]],options:{}},
 {id:'negative_values',rows:[[-10],[-2],[0]],options:{}},
 {id:'ragged_rows',rows:[[1,2],[3],[4,5]],options:{}},
 {id:'nonfinite_nan',rows:[[0],[Number.NaN],[5]],options:{}},
 {id:'nonfinite_inf',rows:[[0],[Number.POSITIVE_INFINITY],[5]],options:{}},
 {id:'bad_control_series',rows:b,options:{seriesLabels:['BAD\u0001','B']}},
 {id:'bad_control_x',rows:a,options:{xAxisLabel:'A\u0002B'}},
 {id:'large_exponent',rows:[[1e308],[1e309],[3]],options:{}},
]
assert.equal(cases.length,16)
fs.mkdirSync(svgDir,{recursive:true})
const results=[]
for(const x of cases){
 const svg=renderSvg({normalized:normalizeData(x.rows),options:x.options})
 assert(svg.startsWith("<?xml version='1.0'?>"))
 fs.writeFileSync(path.join(svgDir,x.id+'.svg'),svg)
 results.push({id:x.id,file:x.id+'.svg',raw_svg_sha256:sha(svg),
  bytes:Buffer.byteLength(svg),
  literal_nan:/\bNaN\b/.test(svg),
  literal_infinity:/\bInfinity\b/.test(svg),
  xml_control:/[\u0001-\u0008\u000b\u000c\u000e-\u001f]/.test(svg)})
}
const result={date:'2026-11-07',study:'chartli',source_pin:pin,
 source_file_sha256:hashes,case_count:results.length,testcases:results,
 limitation:'Original TS renderer on synthetic inputs; no browser, Rust renderer or full CLI executed'}
fs.mkdirSync(path.dirname(output),{recursive:true})
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n')
console.log(JSON.stringify({total:results.length,
 literal_nan:results.filter(x=>x.literal_nan).length,
 with_control:results.filter(x=>x.xml_control).length}))
