import assert from 'node:assert/strict';
import { generateKeyPairSync, sign, verify } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, realpathSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';

const sender = 'author@origin.test';
const recipient = 'reader@destination.test';
const keyId = 'fixture-key';
const signingBytes = (wire) => Buffer.from('ATP synthetic envelope v1\0' + wire, 'utf8');

function check(message, policy) {
  let envelope;
  try { envelope = JSON.parse(message.wire); }
  catch { return { status: 'invalid_message' }; }
  if (!envelope || envelope.sender !== sender || envelope.keyId !== keyId
      || typeof envelope.id !== 'string' || typeof envelope.body !== 'string'
      || !Number.isSafeInteger(envelope.createdAt) || !Number.isSafeInteger(envelope.expiresAt)
      || envelope.createdAt > policy.now || envelope.expiresAt <= envelope.createdAt) {
    return { status: 'invalid_message' };
  }
  if (!verify(null, signingBytes(message.wire), policy.publicKey,
              Buffer.from(message.signature, 'base64'))) {
    return { status: 'invalid_signature' };
  }
  if (envelope.recipient !== recipient) return { status: 'wrong_recipient' };
  if (policy.revoked) return { status: 'revoked' };
  if (envelope.expiresAt <= policy.now) return { status: 'expired' };
  return { status: 'valid', envelope };
}

function init(db) {
  db.exec(`
    PRAGMA journal_mode = DELETE;
    PRAGMA synchronous = FULL;
    CREATE TABLE IF NOT EXISTS outbox (
      id TEXT PRIMARY KEY, wire TEXT NOT NULL, signature TEXT NOT NULL,
      acknowledged INTEGER NOT NULL DEFAULT 0
    ) STRICT;
    CREATE TABLE IF NOT EXISTS inbox (
      sender TEXT NOT NULL, id TEXT NOT NULL, wire TEXT NOT NULL,
      signature TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
      PRIMARY KEY (sender, id)
    ) STRICT;
    CREATE TABLE IF NOT EXISTS delivered (
      sender TEXT NOT NULL, id TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY (sender, id)
    ) STRICT;
  `);
}

function transaction(db, fn) {
  db.exec('BEGIN IMMEDIATE');
  try {
    const result = fn();
    db.exec('COMMIT');
    return result;
  } catch (error) {
    db.exec('ROLLBACK');
    throw error;
  }
}

function worker(db, input) {
  const { op, message, policy, id } = input;
  switch (op) {
    case 'stage':
      db.prepare('INSERT INTO outbox (id, wire, signature) VALUES (?, ?, ?)')
        .run(id, message.wire, message.signature);
      return { status: 'staged' };
    case 'pending':
      return db.prepare('SELECT wire, signature FROM outbox WHERE id = ? AND acknowledged = 0')
        .get(id) ?? null;
    case 'acknowledge':
      db.prepare('UPDATE outbox SET acknowledged = 1 WHERE id = ?').run(id);
      return { status: 'acknowledged' };
    case 'receive': {
      const verified = check(message, policy);
      if (verified.status !== 'valid') return { status: verified.status };
      const envelope = verified.envelope;
      return transaction(db, () => {
        const previous = db.prepare('SELECT wire, signature FROM inbox WHERE sender = ? AND id = ?')
          .get(envelope.sender, envelope.id);
        if (previous) {
          const same = previous.wire === message.wire && previous.signature === message.signature;
          return { status: same ? 'duplicate' : 'id_conflict' };
        }
        db.prepare('INSERT INTO inbox (sender, id, wire, signature) VALUES (?, ?, ?, ?)')
          .run(envelope.sender, envelope.id, message.wire, message.signature);
        return { status: 'queued' };
      });
    }
    case 'consume':
      return transaction(db, () => {
        const row = db.prepare("SELECT * FROM inbox WHERE state = 'pending' ORDER BY rowid LIMIT 1")
          .get();
        if (!row) return { status: 'empty' };
        const verified = check(row, policy);
        const state = verified.status === 'valid' ? 'delivered' : 'quarantined';
        if (state === 'delivered') {
          assert.equal(verified.envelope.sender, row.sender);
          assert.equal(verified.envelope.id, row.id);
          db.prepare('INSERT INTO delivered VALUES (?, ?, ?)')
            .run(row.sender, row.id, verified.envelope.body);
        }
        db.prepare('UPDATE inbox SET state = ? WHERE sender = ? AND id = ?')
          .run(state, row.sender, row.id);
        return { status: state === 'delivered' ? state : verified.status, id: row.id };
      });
    case 'audit':
      return {
        deliveries: db.prepare('SELECT id, body FROM delivered ORDER BY id').all(),
        inbox_states: db.prepare('SELECT id, state FROM inbox ORDER BY id').all(),
        sqlite: db.prepare('SELECT sqlite_version() version').get().version,
      };
    default: throw new Error('Unknown worker operation');
  }
}

function run(fixtureDir) {
  const origin = join(fixtureDir, 'origin.sqlite');
  const destination = join(fixtureDir, 'destination.sqlite');
  const keypair = generateKeyPairSync('ed25519');
  const publicKey = keypair.publicKey.export({ type: 'spki', format: 'pem' });
  const policy = { now: 2, revoked: false, publicKey };

  function envelope(id, extra = {}) {
    const wire = JSON.stringify({
      sender, recipient, keyId, id, createdAt: 1, expiresAt: 10,
      body: 'Synthetic handoff', ...extra,
    });
    return { wire, signature: sign(null, signingBytes(wire), keypair.privateKey).toString('base64') };
  }

  function dispatch(path, op, input = {}) {
    const result = spawnSync(process.execPath, [fileURLToPath(import.meta.url), '--worker', path], {
      input: JSON.stringify({ op, policy, ...input }), encoding: 'utf8', timeout: 10000,
    });
    assert.equal(result.status, 0, result.error?.message ?? result.stderr);
    return JSON.parse(result.stdout);
  }
  const src = (op, input) => dispatch(origin, op, input);
  const dst = (op, input) => dispatch(destination, op, input);
  const receive = (message, nextPolicy) => dst('receive', { message, policy: nextPolicy ?? policy });
  const consume = (nextPolicy) => dst('consume', { policy: nextPolicy ?? policy });
  const outcomes = {};
  function observed(name, status, expected) {
    assert.equal(status, expected, name);
    outcomes[name] = status;
  }

  const queued = envelope('restart');
  // A direct callback has no queue and the receiver is intentionally absent here.
  const directSend = (receiver) => receiver ? receiver(queued) : { status: 'receiver_unavailable' };
  observed('direct_while_offline', directSend(null).status, 'receiver_unavailable');
  observed('sender_stage', src('stage', { id: 'restart', message: queued }).status, 'staged');
  const persisted = src('pending', { id: 'restart' });
  assert.deepEqual(persisted, queued);
  observed('receiver_offline_queue', receive(persisted).status, 'queued');

  // The first delivery acknowledgement has not reached the sender.
  assert.deepEqual(src('pending', { id: 'restart' }), queued);
  observed('resend_before_ack', receive(persisted).status, 'duplicate');
  observed('sender_acknowledged', src('acknowledge', { id: 'restart' }).status, 'acknowledged');
  assert.equal(src('pending', { id: 'restart' }), null);
  observed('consume_in_new_process', consume().status, 'delivered');
  observed('resend_after_delivery', receive(queued).status, 'duplicate');
  observed('different_signed_body_same_id', receive(envelope('restart', { body: 'Different' })).status,
    'id_conflict');

  const incoming = envelope('bad-wire');
  observed('modified_before_enqueue', receive({
    ...incoming, wire: incoming.wire.replace('Synthetic', 'Changed'),
  }).status, 'invalid_signature');
  observed('wrong_recipient', receive(envelope('wrong', { recipient: 'other@destination.test' })).status,
    'wrong_recipient');
  observed('expired_before_enqueue', receive(envelope('too-old', { expiresAt: 2 })).status, 'expired');

  assert.equal(receive(envelope('late', { expiresAt: 3 })).status, 'queued');
  observed('expired_at_read', consume({ ...policy, now: 3 }).status, 'expired');
  assert.equal(receive(envelope('revoked-at-read')).status, 'queued');
  observed('revoked_at_read', consume({ ...policy, revoked: true }).status, 'revoked');
  observed('revoked_before_enqueue', receive(envelope('revoked-in'), { ...policy, revoked: true }).status,
    'revoked');

  assert.equal(receive(envelope('changed-on-disk')).status, 'queued');
  const testDb = new DatabaseSync(destination);
  try {
    testDb.prepare('UPDATE inbox SET wire = replace(wire, ?, ?) WHERE id = ?')
      .run('Synthetic', 'Changed', 'changed-on-disk');
  } finally { testDb.close(); }
  observed('modified_after_enqueue', consume().status, 'invalid_signature');
  observed('no_second_delivery', consume().status, 'empty');

  const audit = dst('audit');
  assert.deepEqual(audit.deliveries, [{ id: 'restart', body: 'Synthetic handoff' }]);
  assert.deepEqual(audit.inbox_states, [
    { id: 'changed-on-disk', state: 'quarantined' },
    { id: 'late', state: 'quarantined' },
    { id: 'restart', state: 'delivered' },
    { id: 'revoked-at-read', state: 'quarantined' },
  ]);
  return { outcomes, ...audit };
}

if (process.argv[2] === '--worker') {
  const db = new DatabaseSync(process.argv[3]);
  try {
    init(db);
    console.log(JSON.stringify(worker(db, JSON.parse(readFileSync(0, 'utf8')))));
  } finally { db.close(); }
} else {
  const results = [];
  const scratch = realpathSync(tmpdir());
  for (let repeat = 0; repeat < 3; repeat++) {
    const fixture = mkdtempSync(join(scratch, 'atp-synthetic-'));
    assert.equal(dirname(fixture), scratch);
    try { results.push(run(fixture)); }
    finally { rmSync(fixture, { recursive: true, force: true }); }
  }
  assert.deepEqual(results[0], results[1]);
  assert.deepEqual(results[0], results[2]);
  console.log(JSON.stringify({
    node: process.version, platform: process.platform, repeats: results.length,
    cases_per_repeat: Object.keys(results[0].outcomes).length, ...results[0],
  }, null, 2));
}
