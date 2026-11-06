// BK-064 model-authored Client plugin probe. Run only in disposable rootless container.
'use strict';
const fs=require('node:fs'), vm=require('node:vm'), crypto=require('node:crypto'), assert=require('node:assert/strict');
const file=process.argv[2], manifestFile=process.argv[3];
assert.ok(file && manifestFile);
const source=fs.readFileSync(file,'utf8'), manifest=JSON.parse(fs.readFileSync(manifestFile,'utf8'));
const sha256=crypto.createHash('sha256').update(source).digest('hex');
assert.equal(manifest.exactWebsiteShaderAndFont,false);
assert.equal(manifest.scope,'offline client-only Cordis Run card');
assert.ok(!/\b(import|require|process|window|document|fetch)\b/.test(source),'forbidden token');

function probe(hasSlots) {
 let hook=0, registration=null;
 const states=[], cleanup=[], events=[];
 const React={
  createElement(type,props,...children){return {type,props:props||{},children};},
  useState(initial){const n=hook++;if(!(n in states))states[n]=initial;return [states[n],val=>{states[n]=typeof val==='function'?val(states[n]):val;}];}
 };
 const slots={
  inject(name,init){assert.equal(name,'tool.view.cordis');events.push('inject');const off=init();assert.equal(typeof off,'function');return ()=>off();},
  register(options,component){assert.equal(options.name,'tool.view.cordis');assert.equal(options.key,'self');assert.equal(typeof component,'function');assert.equal(registration,null);registration=component;events.push('register');return ()=>{registration=null;events.push('dispose');};}
 };
 const ctx={
  get(name){assert.equal(name,'slots');return hasSlots?slots:undefined;},
  effect(init){const off=init();if(off!==undefined){assert.equal(typeof off,'function');cleanup.push(off);}}
 };
 const environment=vm.createContext({React,ctx});
 const plugin=vm.runInContext('(function(){\n'+source+'\n})()',environment,{timeout:1500});
 assert.equal(typeof plugin?.apply,'function');
 environment.plugin=plugin;
 vm.runInContext('plugin.apply(ctx)',environment,{timeout:1500});
 if(!hasSlots){assert.equal(registration,null);assert.equal(events.length,0);return {missing_slot_safe:true};}
 assert.deepEqual(events,['inject','register']);
 function render(){hook=0;environment.renderComponent=registration;return vm.runInContext('renderComponent()',environment,{timeout:1500});}
 function walk(node){
  const nodes=[];
  function visit(n){
   if(n==null||typeof n==='boolean')return;
   if(Array.isArray(n)){n.forEach(visit);return;}
   if(typeof n!=='object')return;
   nodes.push(n);
   if(typeof n.type==='function')visit(n.type(n.props));
   (n.children||[]).forEach(visit);
  }
  visit(node);return nodes;
 }
 function select(node,type){return walk(node).filter(n=>n.type===type);}
 function field(tree,label){
  const l=select(tree,'label').find(n=>n.children.some(c=>c===label));
  assert.ok(l,'missing label '+label);
  const input=walk(l).find(n=>['input','textarea'].includes(n.type));
  assert.ok(input && typeof input.props.onChange==='function','missing control '+label);
  return input;
 }
 let tree=render();
 assert.equal(select(tree,'h1').length,1);
 assert.equal(select(tree,'h1')[0].children[0],'Everything is a plugin');
 assert.equal(select(tree,'h2').length+select(tree,'h3').length,0);
 assert.equal(select(tree,'label').length,4);
 const firstPreview=walk(tree).find(n=>n.props?.['aria-label']==='Poster preview');
 assert.ok(firstPreview?.props?.style?.backgroundImage.includes('#6554e8'));
 assert.ok(firstPreview?.props?.style?.backgroundImage.includes('#20c6b7'));
 field(tree,'Title').props.onChange({target:{value:'Verified poster'}});
 tree=render();
 assert.equal(select(tree,'h1')[0].children[0],'Verified poster');
 field(tree,'Text').props.onChange({target:{value:'Evidence-driven poster'}});
 tree=render();
 assert.equal(select(tree,'p')[0].children[0],'Evidence-driven poster');
 field(tree,'Color 1').props.onChange({target:{value:'#aabbcc'}});
 tree=render();
 field(tree,'Color 2').props.onChange({target:{value:'#002244'}});
 tree=render();
 const preview=walk(tree).find(n=>n.props?.['aria-label']==='Poster preview');
 assert.ok(preview.props.style.backgroundImage.includes('#aabbcc'));
 assert.ok(preview.props.style.backgroundImage.includes('#002244'));
 assert.equal(states.length,4);
 cleanup.forEach(fn=>fn());
 assert.equal(registration,null);
 assert.equal(events.at(-1),'dispose');
 return {default_title:true,title_edit:true,text_edit:true,shader_colors_independent:true,minimal_ui:true,slot_scoped:true,unload_cleanup:true};
}
const start=process.hrtime.bigint();
const result={...probe(true),...probe(false)};
assert.throws(()=>vm.runInNewContext('(function(){return {)',{}));
result.invalid_source_rejected=true;
const ms=Number(process.hrtime.bigint()-start)/1e6;
console.log(JSON.stringify({
  id:'BK-064-offline-cordis-model-generated-client',
  verdict:'PASS',sha256,source_bytes:Buffer.byteLength(source),
  checks:result,passes:Object.values(result).filter(Boolean).length,
  duration_ms:Number(ms.toFixed(3)),rss_kb:process.resourceUsage().maxRSS,
  guardrails:'podman read-only / network none / caps none / no creds',
  limits:['outside DeepSeek Harness Creator UI','synthetic slot and React, no real browser','website shader/font substituted','no live install','no original-model guarantee']
},null,2));
