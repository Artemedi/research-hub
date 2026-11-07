#!/usr/bin/env node
/**
 * Execute exact source 0-CODE parseJsonc on Python-gold synthetic corpus.
 * No installation, commands, hooks, network, production or model execution.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';

const source = path.resolve(process.env.SOURCE_ROOT||'');
const fixtureFile = path.resolve(process.env.FIXTURE||'');
const output = path.resolve(process.env.OUTPUT||'');
const pinned = '47f6a81724e87ff5e916f0eb146516d801a8fb28';
const sourceSha = 'f61414badb9ec40589ebb26655a4b109466c86e20a6e5d8b96add15bf7deb954';
const hash = value=>createHash('sha256').update(value).digest('hex');
assert.equal(execFileSync('git',['-C',source,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),pinned);
const sourceFile = path.join(source,'lib/jsonc.mjs');
assert.equal(hash(fs.readFileSync(sourceFile)),sourceSha);
const {parseJsonc} = await import(pathToFileURL(sourceFile).href);
const fixtures = JSON.parse(fs.readFileSync(fixtureFile,'utf8'));
assert.equal(fixtures.valid_count,120);
assert.equal(fixtures.invalid_count,24);
const valid = [];
for(const row of fixtures.valid){
  assert.equal(hash(row.text),row.input_sha256);
  let actual=null,accepted=false,exception=null;
  try{
    actual = parseJsonc(row.text);
    accepted = true;
  }catch(error){
    exception = error?.name||'Error';
  }
  const matched = accepted && JSON.stringify(actual) === JSON.stringify(row.expected);
  valid.push({id:row.id, input_sha256:row.input_sha256,
    canonical_sha256:row.canonical_sha256,accepted,matched,actual,exception});
}
const invalid=[];
for(const row of fixtures.invalid){
  assert.equal(hash(row.text),row.input_sha256);
  let accepted=false,exception=null;
  try{
    parseJsonc(row.text);
    accepted=true;
  }catch(error){
    exception=error?.name||'Error';
  }
  invalid.push({id:row.id,input_sha256:row.input_sha256,accepted,
    rejected:!accepted,exception});
}
const ambiguous=fixtures.ambiguous_duplicate;
let duplicateValue=null,duplicateAccepted=false;
try{duplicateValue=parseJsonc(ambiguous.text);duplicateAccepted=true;}
catch{/* not a required standard, just an observation */}
// The native JSON editing path has a STRICT inspector, unlike parseJsonc.
const nativeSource=path.join(source,'lib/native-json.mjs');
const nativeSha='c22d121df69f0f4839827b933810c0b05cf6ce86e83cc1ce1c6980ac608e4d42';
assert.equal(hash(fs.readFileSync(nativeSource)),nativeSha);
const {readNativeJson}=await import(pathToFileURL(nativeSource).href);
let nativeDuplicateRejected=false,nativePositiveAccepted=false;
try{readNativeJson(Buffer.from(ambiguous.text));}
catch{nativeDuplicateRejected=true;}
try{nativePositiveAccepted=readNativeJson(Buffer.from('{"model":"safe"}')).model==='safe';}
catch{/* negative observed below */}
const result = {
  date:'2026-11-07',study:'zero-code',
  source_pin:pinned,
  source_path:'lib/jsonc.mjs',source_sha256:sourceSha,
  strict_native_source_path:'lib/native-json.mjs',strict_native_source_sha256:nativeSha,
  fixture_sha256:hash(fs.readFileSync(fixtureFile)),
  corpus:'Python-generated JSONC from known standard JSON values',
  valid_count:valid.length,invalid_count:invalid.length,
  valid_exact_matches:valid.filter(x=>x.matched).length,
  invalid_rejected:invalid.filter(x=>x.rejected).length,
  duplicate_key_observation:{
    input_sha256:ambiguous.input_sha256,accepted:duplicateAccepted,
    result:duplicateValue,
    strict_native_json_rejected_duplicate:nativeDuplicateRejected,
    strict_native_json_accepted_unique:nativePositiveAccepted,
    caution:'parseJsonc is last-key-wins; native-json inspect explicitly rejects ambiguous duplicate keys'
  },
  valid,invalid,
  status:'ORIGINAL_PARSER_BOUNDED_CONFORMANCE',
  limitations:[
    'Only lib/jsonc.mjs tested, not supervisor or hooks or native-json.mjs inspector',
    '20 base synthetic objects × six render styles, not 120 statistically independent real user configs',
    'Do not claim JSONC is a strict standardized unique-key format from this test',
    'No unusual Unicode BOM, future library versions or caller-side error handling verified',
    'No code or settings changed in either source repository or project target'
  ]
};
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({
 valid:result.valid_exact_matches,total_valid:result.valid_count,
 invalid_rejected:result.invalid_rejected,total_invalid:result.invalid_count,
 duplicate_key:result.duplicate_key_observation
}));
