import { test } from 'node:test';
import { once } from 'node:events';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { preparePrivateTmux } from '../experiments/research-portfolio/private-tmux.mjs';

test('stop targets only the created private socket and repeated cleanup is safe', { skip: process.platform === 'win32' }, async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hub-tmux-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  t.mock.method(process, 'getuid', () => 1000);
  const keys = ['TMUX_TMPDIR', 'TMUX', 'TMUX_PANE', 'FAKE_TMUX_LOG'];
  const original = new Map(keys.map(key => [key, process.env[key]]));
  t.after(() => {
    for (const [key, value] of original) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  });

  const log = path.join(root, 'calls');
  const fake = path.join(root, 'tmux');
  fs.writeFileSync(fake, '#!/bin/sh\nprintf "%s\\n" "$@" >> "$FAKE_TMUX_LOG"\nrm -- "$2"\n', { mode: 0o700 });
  process.env.TMUX_TMPDIR = path.join(root, 'original');
  process.env.TMUX = '/user/server,123,0';
  process.env.TMUX_PANE = '%3';
  process.env.FAKE_TMUX_LOG = log;

  const directory = path.join(root, 'private');
  const tmux = preparePrivateTmux(directory);
  tmux.stop(fake);
  assert.equal(fs.existsSync(log), false);
  assert.equal(process.env.TMUX_TMPDIR, directory);
  assert.equal(process.env.TMUX, undefined);
  assert.equal(process.env.TMUX_PANE, undefined);

  const socketDir = path.join(directory, 'tmux-1000');
  fs.mkdirSync(socketDir);
  const socket = path.join(socketDir, 'default');
  fs.writeFileSync(socket, 'not a socket');
  tmux.stop(fake);
  assert.equal(fs.existsSync(log), false);
  fs.unlinkSync(socket);

  const server = net.createServer().listen(socket);
  try {
    await once(server, 'listening');
    tmux.stop(fake);
    tmux.stop(fake);
    assert.equal(fs.readFileSync(log, 'utf8'), ['-S', socket, 'kill-server', ''].join('\n'));
  } finally {
    await new Promise(resolve => server.close(resolve));
    tmux.restore();
  }
  assert.equal(process.env.TMUX_TMPDIR, path.join(root, 'original'));
  assert.equal(process.env.TMUX, '/user/server,123,0');
  assert.equal(process.env.TMUX_PANE, '%3');
});
