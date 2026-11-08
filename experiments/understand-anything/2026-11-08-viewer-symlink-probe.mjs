#!/usr/bin/env node
/**
 * Reproduce the token-gated viewer's graph-listed symlink boundary behavior.
 *
 * Usage:
 *   node 2026-11-08-viewer-symlink-probe.mjs /path/to/upstream/viewer/bin/viewer.mjs
 *
 * The exact upstream viewer source is copied to a temporary harness. A stub
 * supplies the unused staleness import and a minimal static index. The probe
 * uses only a synthetic project, a temporary outside sentinel and localhost.
 * It never reads user files or changes the supplied upstream source.
 */
import { createHash } from "node:crypto";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawn } from "node:child_process";

const EXPECTED_VIEWER_SHA256 =
  "b3f2aa1fa5c2fff5cc286932ae32d1d00a7c5da61c7481056014bc5a5d315883";
const SENTINEL = "SYNTHETIC_OUTSIDE_SENTINEL_9f41c2";
const TOKEN = "synthetic-token-not-a-secret";
const sourcePath = process.argv[2];

if (!sourcePath) {
  console.error("Usage: node 2026-11-08-viewer-symlink-probe.mjs <viewer.mjs>");
  process.exit(2);
}

const source = readFileSync(sourcePath);
const sourceSha256 = createHash("sha256").update(source).digest("hex");
if (sourceSha256 !== EXPECTED_VIEWER_SHA256) {
  console.error(JSON.stringify({
    result: "SOURCE_HASH_MISMATCH",
    expected: EXPECTED_VIEWER_SHA256,
    observed: sourceSha256,
  }, null, 2));
  process.exit(2);
}

const tempRoot = mkdtempSync(join(tmpdir(), "ua-viewer-symlink-probe-"));
let child;
try {
  const viewerRoot = join(tempRoot, "viewer");
  const bin = join(viewerRoot, "bin");
  const project = join(tempRoot, "project");
  const outsideFile = join(tempRoot, "outside-secret.txt");

  mkdirSync(join(bin, "dist"), { recursive: true });
  mkdirSync(join(viewerRoot, "dist"), { recursive: true });
  mkdirSync(join(project, ".ua"), { recursive: true });
  writeFileSync(join(bin, "viewer.mjs"), source);
  writeFileSync(
    join(bin, "dist", "staleness.js"),
    "export async function getGraphFreshnessBatch() { return {}; }\n",
  );
  writeFileSync(join(viewerRoot, "dist", "index.html"), "<!doctype html><title>synthetic</title>\n");
  writeFileSync(outsideFile, SENTINEL + "\n");
  symlinkSync(outsideFile, join(project, "escape.txt"));
  writeFileSync(
    join(project, ".ua", "knowledge-graph.json"),
    JSON.stringify({ nodes: [{ filePath: "escape.txt" }] }),
  );

  child = spawn(
    process.execPath,
    [join(bin, "viewer.mjs"), project, "--port", "0", "--no-open"],
    {
      env: { ...process.env, UNDERSTAND_ACCESS_TOKEN: TOKEN },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  let stdout = "";
  let stderr = "";
  child.stdout.setEncoding("utf8");
  child.stderr.setEncoding("utf8");
  child.stdout.on("data", chunk => { stdout += chunk; });
  child.stderr.on("data", chunk => { stderr += chunk; });

  const dashboardUrl = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error(
      "Viewer did not report a URL within 5 seconds: " + stderr,
    )), 5000);
    child.stdout.on("data", () => {
      const match = stdout.match(/Dashboard URL:\s*(http:\/\/127\.0\.0\.1:\d+\/\?token=[^\s]+)/);
      if (match) {
        clearTimeout(timeout);
        resolve(match[1]);
      }
    });
    child.once("error", error => {
      clearTimeout(timeout);
      reject(error);
    });
    child.once("exit", code => {
      if (!stdout.includes("Dashboard URL:")) {
        clearTimeout(timeout);
        reject(new Error("Viewer exited before startup (code " + code + "): " + stderr));
      }
    });
  });

  const endpoint = new URL("/file-content.json", new URL(dashboardUrl).origin);
  endpoint.searchParams.set("token", TOKEN);
  endpoint.searchParams.set("path", "escape.txt");
  const response = await fetch(endpoint);
  const body = await response.json();
  const outsideFileExposed =
    response.status === 200 && body.content?.includes(SENTINEL) === true;

  const result = {
    result: outsideFileExposed ? "OBSERVED_SYMLINK_ESCAPE" : "NOT_REPRODUCED",
    upstream_viewer_sha256: sourceSha256,
    expected_http_status: "deny external symlink target",
    observed_http_status: response.status,
    outside_file_exposed: outsideFileExposed,
    synthetic_sentinel: SENTINEL,
    bound_interface: new URL(dashboardUrl).hostname,
    endpoint: "/file-content.json",
    fixture: "temporary project graph lists escape.txt; escape.txt is a symlink to a temporary file outside the project",
    note: "The staleness import and static index are minimal stubs; the upstream viewer.mjs request handler is unchanged.",
  };
  console.log(JSON.stringify(result, null, 2));
  if (!outsideFileExposed) process.exitCode = 1;
} finally {
  child?.kill("SIGTERM");
  rmSync(tempRoot, { recursive: true, force: true });
}
