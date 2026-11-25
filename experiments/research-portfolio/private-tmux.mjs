import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

export function preparePrivateTmux(directory) {
  // Unqualified tmux commands in WorkerManager now resolve to this default socket.
  const socket = path.join(directory, `tmux-${process.getuid()}`, 'default');
  fs.mkdirSync(directory, { mode: 0o700 });
  const keys = ['TMUX_TMPDIR', 'TMUX', 'TMUX_PANE'];
  const previous = keys.map(key => [key, process.env[key]]);
  process.env.TMUX_TMPDIR = directory;
  delete process.env.TMUX;
  delete process.env.TMUX_PANE;

  return {
    stop(binary = 'tmux') {
      if (!fs.lstatSync(socket, { throwIfNoEntry: false })?.isSocket()) return;
      try {
        execFileSync(binary, ['-S', socket, 'kill-server'], { stdio: 'ignore' });
      } catch {
        // Cleanup is best-effort if the private server exits between stat and exec.
      }
    },
    restore() {
      for (const [key, value] of previous) {
        if (value === undefined) delete process.env[key];
        else process.env[key] = value;
      }
    },
  };
}
