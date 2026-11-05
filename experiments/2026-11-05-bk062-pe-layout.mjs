// Original PE/CLI layout reader, independent authored byte fixture, no target execution.
// Node >=24: node --experimental-transform-types --permission --allow-fs-read=SOURCE --allow-fs-read=FIXTURE FIXTURE SOURCE
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { pathToFileURL } from 'node:url';
import { resolve,join } from 'node:path';
registerHooks({resolve(specifier,context,next){return next(specifier.startsWith('.')&&specifier.endsWith('.js')?specifier.slice(0,-3)+'.ts':specifier,context);}});
const source=resolve(process.argv[2]);
const {readManagedPeLayout}=await import(pathToFileURL(join(source,'src/dotnet/ManagedPeReader.ts')));
function authored(bits){
 const bytes=Buffer.alloc(4096), pe=128, coff=pe+4, opt=coff+20, size=bits===64?240:224, sec=opt+size, raw=1024, rva=8192;
 bytes.write('MZ');bytes.writeUInt32LE(pe,60);bytes.write('PE\0\0',pe,'latin1');bytes.writeUInt16LE(bits===64?0x8664:0x14c,coff);bytes.writeUInt16LE(1,coff+2);bytes.writeUInt16LE(size,coff+16);bytes.writeUInt16LE(0x2022,coff+18);
 bytes.writeUInt16LE(bits===64?0x20b:0x10b,opt);bytes.writeUInt32LE(4096,opt+32);bytes.writeUInt32LE(512,opt+36);bytes.writeUInt32LE(16384,opt+56);bytes.writeUInt32LE(1024,opt+60);
 const dir=opt+(bits===64?112:96);bytes.writeUInt32LE(16,dir-4);bytes.writeUInt32LE(rva,dir+14*8);bytes.writeUInt32LE(72,dir+14*8+4);
 bytes.write('.fixture',sec,'latin1');bytes.writeUInt32LE(768,sec+8);bytes.writeUInt32LE(rva,sec+12);bytes.writeUInt32LE(1024,sec+16);bytes.writeUInt32LE(raw,sec+20);
 bytes.writeUInt32LE(72,raw);bytes.writeUInt16LE(2,raw+4);bytes.writeUInt16LE(5,raw+6);bytes.writeUInt32LE(rva+128,raw+8);bytes.writeUInt32LE(64,raw+12);bytes.writeUInt32LE(1,raw+16);
 return {bytes,coff,opt,sec,dir,raw,rva,size};
}
const records=[];
function run(name,fn){fn();records.push(name);}
for(let repeat=0;repeat<3;repeat++)for(const bits of [32,64]){
 const prefix=`r${repeat}/PE${bits}/`;
 run(prefix+'known-coordinate-oracle',()=>{const f=authored(bits),l=readManagedPeLayout(f.bytes);assert.equal(l.optionalHeader,bits===64?'pe32-plus':'pe32');assert.equal(l.architecture,bits===64?'x86_64':'x86');assert.equal(l.cli.headerOffset,f.raw);assert.equal(l.cli.metadata.rva,f.rva+128);for(const delta of [0,17,72,128,700])assert.equal(l.rvaToOffset(f.rva+delta,1,'oracle'),f.raw+delta);});
 run(prefix+'bad-MZ-rejected',()=>{const f=authored(bits);f.bytes[0]=0;assert.throws(()=>readManagedPeLayout(f.bytes));});
 run(prefix+'truncated-section-table-rejected',()=>{const f=authored(bits);assert.throws(()=>readManagedPeLayout(f.bytes.subarray(0,f.sec+39)));});
 run(prefix+'zero-directory-count-is-absent',()=>{const f=authored(bits);f.bytes.writeUInt32LE(0,f.dir-4);const l=readManagedPeLayout(f.bytes);assert.equal(l.cliDirectoryState,'absent');assert.equal(l.cli,null);assert.equal(l.cliIssue,null);});
 run(prefix+'overlapping-sections-refused',()=>{const f=authored(bits);f.bytes.writeUInt16LE(2,f.coff+2);f.bytes.copy(f.bytes,f.sec+40,f.sec,f.sec+40);const l=readManagedPeLayout(f.bytes);assert.equal(l.cli,null);assert.match(l.cliIssue.detail,/ambiguous overlapping/);assert.throws(()=>l.rvaToOffset(f.rva,1,'oracle'));});
 run(prefix+'unbacked-virtual-RVA-refused',()=>{const f=authored(bits);f.bytes.writeUInt32LE(32,f.sec+16);const l=readManagedPeLayout(f.bytes);assert.equal(l.cli,null);assert.match(l.cliIssue.detail,/file-backed/);});
 run(prefix+'short-CLI-header-refused',()=>{const f=authored(bits);f.bytes.writeUInt32LE(16,f.raw);const l=readManagedPeLayout(f.bytes);assert.equal(l.cli,null);assert.equal(l.cliIssue.code,'invalid-cli-header');});
 run(prefix+'out-of-range-RVA-refused',()=>{const f=authored(bits),l=readManagedPeLayout(f.bytes);for(const v of [-1,4294967296,Number.MAX_SAFE_INTEGER])assert.throws(()=>l.rvaToOffset(v,1,'oracle'));});
}
console.log(JSON.stringify({expected_source_sha:'92f332652d352e60b550567adf2399d83d8ebe78',runtime:process.version,fixture:'independently authored in-memory PE32/PE32+ header bytes; not an executable or CLR-loadability proof',passed:records.length,repetitions:3,records,scope:'original ManagedPeReader and production dependencies only; no metadata/CIL pipeline, provider, CLI/MCP, external binary, native tool or project-effect test'},null,2));
