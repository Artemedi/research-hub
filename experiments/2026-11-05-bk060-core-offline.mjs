// Bounded original-core test. No service, CLI, network, credentials or dependencies.
// node --experimental-transform-types --permission --allow-fs-read=<source>,<this-file> <this-file> <source>
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { resolve, join } from 'node:path';
const root = resolve(process.argv[2]);
const { Engine, MemoryRepositories, threadKey } = await import(pathToFileURL(join(root, 'src/core/index.ts')));
const checks = [];
function check(name, fn) { fn(); checks.push(name); }
function fixture() {
  const repo = new MemoryRepositories(), sent = new Map(), starts = [], stops = [], candidates = [];
  let clock = 0;
  const policy = { version: 'v1', paused: false, evalTimeoutMs: 1000,
    // Deliberately fake Policy: tests the core's use of the port, NOT settingsPolicy.
    gate: t => t.actor.id === 'owner' && t.human
      ? { admissible: true, strength: 'explicit', basis: { via: 'listed' } }
      : { admissible: false, reason: 'not_a_member' },
    revalidate: () => true, admitsInferred: () => false };
  const engine = new Engine({ repo, policy: () => policy,
    scope: { scope: t => t.meta.filtered ? { listened: false, reason: 'disabled' } : { listened: true, observed: true } },
    assessor: { request: c => candidates.push(c) },
    executor: { start: (t,a) => starts.push([t.id,a.id]), deliver: () => {}, stop: (t,a) => stops.push([t.id,a.id]) },
    outbox: { send: m => { if (!sent.has(m.id)) sent.set(m.id,m); }, status: id => sent.has(id) ? 'pending' : undefined, withdraw: id => sent.delete(id) },
    now: () => new Date(Date.UTC(2026,10,5,0,0,0,++clock)).toISOString() });
  const trigger = (id, extra = {}) => ({ id, source: 'fixture', threads: [{source:'fixture',id:'work'}], actor:{source:'fixture',id:'owner'},
    human:true, at:'2026-11-05T00:00:00Z', text:'synthetic request', channel:{source:'fixture',thread:'work',address:{}}, meta:{}, ...extra });
  function accept(id='origin') {
    engine.receive(trigger(id));
    const decision = engine.decide(id,{kind:'accept',title:'fixture',scope:'synthetic only',reason:'fixture'});
    const ticket = repo.tickets.get(decision.ticketId);
    engine.assignmentStarted(ticket.id,ticket.assignments[0].id);
    return ticket.id;
  }
  return {repo,engine,policy,starts,stops,sent,candidates,trigger,accept};
}
check('unlisted origin cannot be directly accepted', () => { const h=fixture(); h.engine.receive(h.trigger('x',{actor:{source:'fixture',id:'guest'}})); assert.throws(()=>h.engine.decide('x',{kind:'accept',title:'x',scope:'x',reason:'x'})); assert.equal(h.repo.tickets.list().length,0); });
check('filtered trigger never becomes candidate', () => { const h=fixture(); assert.equal(h.engine.receive(h.trigger('x',{meta:{filtered:true}})),'filtered'); h.engine.evaluateDue(); assert.equal(h.candidates.length,0); });
check('duplicate event creates no second ticket', () => { const h=fixture(); const id=h.accept(); assert.equal(h.engine.receive(h.trigger('origin')),'duplicate'); assert.equal(h.engine.decide('origin',{kind:'accept',title:'x',scope:'x',reason:'x'}).ticketId,id); assert.equal(h.repo.tickets.list().length,1); });
check('worker-owned follow-up cannot directly spawn work', () => { const h=fixture(); h.accept(); h.engine.receive(h.trigger('follow')); assert.throws(()=>h.engine.decide('follow',{kind:'accept',title:'x',scope:'x',reason:'x'})); assert.equal(h.repo.tickets.list().length,1); });
check('human stop prevents subsequent fanout and resume', () => { const h=fixture(); const id=h.accept(); h.engine.stopTicket(id); h.engine.receive(h.trigger('later')); assert.equal(h.repo.tickets.get(id).ended.outcome,'stopped'); assert.equal(h.repo.tickets.get(id).inputs.length,0); assert.equal(h.starts.length,1); assert.equal(h.stops.length,1); });
check('bot does not resume completed ticket', () => { const h=fixture(); const id=h.accept(); h.engine.report(id,{state:'ready',summary:'done'}); h.engine.receive(h.trigger('ci',{human:false})); assert.equal(h.repo.tickets.get(id).ended.outcome,'completed'); assert.equal(h.starts.length,1); });
check('human resumes completed ticket under same mandate', () => { const h=fixture(); const id=h.accept(); const mandate=h.repo.tickets.get(id).mandate; h.engine.report(id,{state:'ready',summary:'done'}); h.engine.receive(h.trigger('follow')); assert.equal(h.repo.tickets.get(id).ended,undefined); assert.deepEqual(h.repo.tickets.get(id).mandate,mandate); assert.equal(h.starts.length,2); });
check('revoked mandate cannot resume completed ticket', () => { const h=fixture(); const id=h.accept(); h.engine.report(id,{state:'ready',summary:'done'}); h.policy.revalidate=()=>false; h.engine.receive(h.trigger('follow')); assert.equal(h.repo.tickets.get(id).ended.outcome,'completed'); assert.equal(h.starts.length,1); });
check('pause defers resume and rechecks policy after unpause', () => { const h=fixture(); const id=h.accept(); h.engine.report(id,{state:'ready',summary:'done'}); h.policy.paused=true; h.engine.receive(h.trigger('follow')); assert.equal(h.starts.length,1); h.policy.revalidate=()=>false; h.policy.paused=false; h.engine.evaluateDue(); assert.equal(h.starts.length,1); assert.ok(h.repo.tickets.get(id).ended); });
check('context-only human message cannot resume ended ticket', () => { const h=fixture(); const id=h.accept(); h.engine.followForContext(id,{source:'fixture',id:'context'}); h.engine.report(id,{state:'ready',summary:'done'}); h.engine.receive(h.trigger('context',{threads:[{source:'fixture',id:'context'}]})); assert.equal(h.starts.length,1); assert.ok(h.repo.tickets.get(id).ended); });
check('context-only thread rejects acknowledgement', () => { const h=fixture(); const id=h.accept(); h.engine.followForContext(id,{source:'fixture',id:'context'}); h.engine.receive(h.trigger('context',{threads:[{source:'fixture',id:'context'}]})); assert.throws(()=>h.engine.reply({purpose:'acknowledgement',ticketId:id,triggerId:'context',text:'ack'})); assert.equal(h.sent.size,0); });
check('policy version mismatch refuses stale decision', () => { const h=fixture(); h.engine.receive(h.trigger('x')); h.engine.evaluateDue(); const c=h.candidates[0]; h.policy.version='v2'; const d=h.engine.decide('x',{kind:'accept',title:'x',scope:'x',reason:'x',evalId:c.evalId}); assert.equal(d.kind,'unavailable'); assert.equal(h.repo.tickets.list().length,0); });
check('ready ticket waits for its own PR close', () => { const h=fixture(); const id=h.accept(); const pr={source:'fixture',id:'pr'}; h.engine.bindThread(id,pr,true); h.engine.report(id,{state:'ready',summary:'done'}); assert.equal(h.repo.tickets.get(id).ended,undefined); h.engine.threadClosed(pr,'merged','2026-11-05T00:01:00Z'); assert.equal(h.repo.tickets.get(id).ended.outcome,'merged'); });
check('repository transaction rolls back failed mutations', () => { const h=fixture(); assert.throws(()=>h.repo.atomic(()=>{h.repo.triggers.save(h.trigger('x'));throw Error('rollback');})); assert.equal(h.repo.triggers.get('x'),undefined); });
check('repository reads are isolated clones', () => { const h=fixture(); const id=h.accept(); const t=h.repo.tickets.get(id); t.title='mutation'; assert.equal(h.repo.tickets.get(id).title,'fixture'); assert.equal(threadKey({source:'fixture',id:'work'}),'fixture:work'); });
console.log(JSON.stringify({source:'deepseek-ai/dsh-superagent-prototype',sha:'8c32a9dc5d72c033816c6a8110b37f40cf94fba4',runtime:process.version,passed:checks.length,checks,scope:'original in-memory core; fake Policy/Executor/Outbox; no live adapters, settingsPolicy, persistence, model, OS sandbox or production validation'},null,2));
