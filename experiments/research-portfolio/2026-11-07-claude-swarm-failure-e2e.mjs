#!/usr/bin/env node
/**
 * Isolated upstream Claude Swarm failure-injection, pinned artifact on synthetic git.
 * No real Claude CLI invocation. Fake command lives in temporary PATH; dedicated
 * TMUX_TMPDIR prevents touching the user's existing tmux server/sessions.
 */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';

const PIN = '31f19199bf3557cda4860231186a06b72c8edb94';
const source = path.resolve(process.env.CLAUDE_SWARM_SOURCE || '');
const out = path.resolve(process.env.OUTPUT || 'claude-swarm-failure-e2e.json');
const git = (cwd, ...args) => execFileSync('git', args, { cwd, encoding: 'utf8' }).trim();
const sh = (value) => createHash('sha256').update(value).digest('hex');
const cases = [];
const record = (id, actual, expected, interpretation) => {
  cases.push({ id, observed: actual, oracle: expected, oracle_met: actual === expected, interpretation });
};
const wait = ms => new Promise(r => setTimeout(r, ms));
assert.equal(git(source, 'rev-parse', 'HEAD'), PIN);
const managerPath = path.join(source, 'dist/workers/manager.js');
const worktreePath = path.join(source, 'dist/workers/worktree-manager.js');
const lockPath = path.join(source, 'dist/workers/lock-manager.js');
const statePath = path.join(source, 'dist/state/manager.js');
for (const f of [managerPath, worktreePath, lockPath, statePath]) assert(fs.existsSync(f), 'build required');
const { WorkerManager } = await import(pathToFileURL(managerPath).href);
const { WorktreeManager } = await import(pathToFileURL(worktreePath).href);
const { TaskLockManager } = await import(pathToFileURL(lockPath).href);
const { StateManager } = await import(pathToFileURL(statePath).href);
const upstreamFiles = {
  'src/workers/manager.ts': sh(fs.readFileSync(path.join(source, 'src/workers/manager.ts'))),
  'src/workers/worktree-manager.ts': sh(fs.readFileSync(path.join(source, 'src/workers/worktree-manager.ts'))),
  'src/workers/lock-manager.ts': sh(fs.readFileSync(path.join(source, 'src/workers/lock-manager.ts'))),
};
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'claude-swarm-fail-e2e-'));
const repo = path.join(root, 'synthetic');
const originalPath = process.env.PATH;
const oldTmuxDir = process.env.TMUX_TMPDIR;
try {
  fs.mkdirSync(repo, { recursive: true });
  git(root, 'init', '-q', '-b', 'main', repo);
  git(repo, 'config', 'user.email', 'fixture@invalid.example');
  git(repo, 'config', 'user.name', 'Fixture');
  fs.writeFileSync(path.join(repo, '.gitignore'), '.claude/\n');
  fs.writeFileSync(path.join(repo, 'README.md'), 'synthetic feature baseline\n');
  git(repo, 'add', '.gitignore', 'README.md');
  git(repo, 'commit', '-q', '-m', 'fixture baseline');
  const base = git(repo, 'rev-parse', 'HEAD');
  const wt = new WorktreeManager(repo);
  const locks = new TaskLockManager(repo);

  const a = await wt.createWorktree('alpha');
  const b = await wt.createWorktree('beta');
  record('parallel_worktrees_are_distinct', a.worktreePath !== b.worktreePath, true,
    'Parallel workers receive different Git worktree paths');
  fs.writeFileSync(path.join(a.worktreePath, 'alpha.txt'), 'alpha edit\n');
  fs.writeFileSync(path.join(b.worktreePath, 'beta.txt'), 'beta edit\n');
  record('uncommitted_files_isolated', !fs.existsSync(path.join(b.worktreePath, 'alpha.txt'))
    && !fs.existsSync(path.join(a.worktreePath, 'beta.txt')), true,
    'Each worker sees its own uncommitted files');
  const lockA = locks.claimFiles('alpha', ['src/shared.ts'], 'fixture-session-a');
  const lockB = locks.claimFiles('beta', ['src/shared.ts'], 'fixture-session-b');
  record('atomic_lock_conflict', lockA.claimed.length === 1
    && lockB.claimed.length === 0 && lockB.conflicts[0]?.heldBy === 'alpha', true,
    'A second feature cannot acquire a held file lock');
  const lockB2 = locks.claimFiles('beta', ['src/shared.ts'], 'fixture-session-b');
  record('orphan_lock_blocks_after_worker_loss', lockB2.conflicts.length === 1, true,
    'Without explicit recovery stale locks persist (not automatic lease expiry)');
  const released = locks.releaseAll('alpha');
  const lockRecovered = locks.claimFiles('beta', ['src/shared.ts'], 'fixture-session-b');
  record('manual_lock_recovery', released === 1 && lockRecovered.claimed.length === 1, true,
    'Explicit releaseAll permits progress; no automatic recovery proved');

  // Safely reproduce forced worktree recreation in a disposable synthetic repo.
  const beforePath = a.worktreePath;
  const priorEdit = path.join(beforePath, 'alpha.txt');
  assert(fs.existsSync(priorEdit));
  const aRetry = await wt.createWorktree('alpha');
  record('retry_resets_uncommitted_changes', !fs.existsSync(priorEdit)
    && aRetry.worktreePath === beforePath, true,
    'Uncommitted edits are discarded by removeWorktree(force) then recreation');
  record('retry_branch_reset_to_base', git(repo, 'rev-parse', 'swarm/work/alpha') === base, true,
    'The recreated branch points to original HEAD; no recovery checkpoint');

  // Only the synthetic "claude" shim is visible to tmux. Never call the real agent.
  const mockBin = path.join(root, 'mock-bin');
  fs.mkdirSync(mockBin);
  const mockCli = path.join(mockBin, 'claude');
  fs.writeFileSync(mockCli, `#!/bin/sh
set -eu
id=$(basename "$PWD")
case "$id" in
  probe-a)
    mkdir -p .claude/orchestrator/workers
    printf 'finished in isolated worktree\\n' > .claude/orchestrator/workers/probe-a.done
    echo MOCK_COMPLETED
    exit 0 ;;
  probe-b)
    printf 'created done marker before failing\\n' > "$MOCK_MAIN/.claude/orchestrator/workers/probe-b.done"
    echo MOCK_CRASHED_AFTER_DONE
    exit 7 ;;
  *) echo MOCK_UNKNOWN >&2; exit 8 ;;
esac
`, { mode: 0o700 });
  const tmuxDir = path.join(root, 'tmux');
  fs.mkdirSync(tmuxDir);
  process.env.TMUX_TMPDIR = tmuxDir;
  process.env.MOCK_MAIN = repo;
  process.env.PATH = mockBin + path.delimiter + originalPath;
  // Deliberately unset permission override to inspect the upstream default.
  delete process.env.CLAUDE_SWARM_PERMISSION_MODE;
  delete process.env.CLAUDE_SWARM_ALLOWED_TOOLS;
  delete process.env.CLAUDE_SWARM_MCP_SERVERS;
  const state = new StateManager(repo);
  const worker = new WorkerManager(repo, state);

  const startA = await worker.startWorker({
    id: 'probe-a', description: 'synthetic, local mock only',
    status: 'pending', attempts: 0,
  });
  assert(startA.success, startA.error);
  const scriptA = fs.readFileSync(path.join(repo, '.claude/orchestrator/workers/probe-a.sh'), 'utf8');
  record('default_permission_mode_bypass', scriptA.includes('--permission-mode')
    && scriptA.includes('bypassPermissions'), true,
    'Default generated wrapper requests bypassPermissions (source + runtime)');
  record('default_allowed_tools_include_bash', scriptA.includes('Bash,Read,Write,Edit,Glob,Grep'), true,
    'Default generated flags permit Bash and write-capable tools');
  let stateA = '';
  for (let i = 0; i < 60; i++) {
    await wait(150);
    const s = await worker.checkWorker(startA.sessionName);
    stateA = s.status;
    if (stateA !== 'running') break;
  }
  record('worktree_relative_done_exists', fs.existsSync(
    path.join(repo, '.claude/worktrees/probe-a/.claude/orchestrator/workers/probe-a.done')), true,
    'A cooperative mock worker followed the relative .done instruction');
  record('main_done_file_missing', !fs.existsSync(
    path.join(repo, '.claude/orchestrator/workers/probe-a.done')), true,
    'The manager looks for .done under the main project rather than the worktree');
  record('successful_worktree_worker_misclassified_crashed', stateA === 'crashed', true,
    'A successful mock with a .done in its worktree is reported crashed');

  const startB = await worker.startWorker({
    id: 'probe-b', description: 'synthetic, local mock only',
    status: 'pending', attempts: 0,
  });
  assert(startB.success, startB.error);
  let stateB = '';
  for (let i = 0; i < 60; i++) {
    await wait(150);
    const s = await worker.checkWorker(startB.sessionName);
    stateB = s.status;
    if (stateB !== 'running') break;
  }
  record('failed_worker_done_marker_false_completion', stateB === 'completed', true,
    'A fake worker exiting nonzero after writing main .done is marked completed');
  const logB = fs.readFileSync(path.join(repo, '.claude/orchestrator/workers/probe-b.log'), 'utf8');
  record('failed_cli_logged_exit_marker', logB.includes('MOCK_CRASHED_AFTER_DONE')
    && logB.includes('WORKER_EXITED'), true,
    'The shell wrapper reports WORKER_EXITED after a failed CLI pipeline');
  const ref = git(repo, 'rev-parse', 'HEAD');
  record('main_git_head_unchanged', ref === base, true,
    'No execution changed the synthetic main Git HEAD');

  // The temp-root tmux socket contains only synthetic sessions; kill only that server.
  try { execFileSync('tmux', ['kill-server'], { stdio: 'ignore' }); } catch {}
  await wt.cleanupAll();
  const result = {
    date: '2026-11-07',
    study: 'claude-swarm',
    upstream_pin: PIN,
    upstream_files_sha256: upstreamFiles,
    environment: { isolated_git_repository: true, isolated_tmux_socket: true,
      synthetic_claude_cli: true, real_claude_calls: 0,
      production_sources_modified: false, upstream_modified: false },
    tests: cases,
    tests_total: cases.length,
    matched_oracle: cases.filter(c => c.oracle_met).length,
    unexpected_results: cases.filter(c => !c.oracle_met).map(c => c.id),
    source_scope: 'Upstream production WorkerManager / WorktreeManager / TaskLockManager code',
    risks: [
      'Retry of same feature ID recreates worktree forcibly and loses uncommitted work',
      'Relative .done path under worktree does not match manager main-repo lookup',
      'A .done marker in main directory is trusted even after simulated CLI failure',
      'Generated CLI defaults bypassPermissions with Bash/Write/Edit enabled',
      'Locks remain after worker loss until explicit release'
    ],
    limitations: [
      'All workers use controlled fake claude CLI, no model execution or real credentials',
      'No actual DSH runtime worker integration or production worktree was exercised',
      'A single synthetic git repository, no concurrent race stress or crash at disk layer',
      'Tests verify observed failure modes, not full coverage of all real-world errors',
      'Source code is pinned; dependencies built locally via npm ci --ignore-scripts'
    ]
  };
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ total: result.tests_total, matched_oracle: result.matched_oracle,
    unexpected: result.unexpected_results, risks: result.risks.length }));
  assert.equal(result.matched_oracle, result.tests_total);
} finally {
  try { execFileSync('tmux', ['kill-server'], { stdio: 'ignore' }); } catch {}
  process.env.PATH = originalPath;
  if (oldTmuxDir === undefined) delete process.env.TMUX_TMPDIR;
  else process.env.TMUX_TMPDIR = oldTmuxDir;
  fs.rmSync(root, { recursive: true, force: true });
}
