# IPFire fireperf

[Структурированная запись и связи](../catalog/studies/ipfire-fireperf.md)

**Telegram source:** BK-059 / 01.11.2026; [full engineering introduction](https://www.ipfire.org/fireperf) and [complete manual](https://man-pages.ipfire.org/fireperf/fireperf.html).
**Evidence type:** full original C source and official docs; **not** a peer-reviewed scientific paper.
**Source pin:** official [fireperf-0.3.0.tar.gz](https://source.ipfire.org/releases/fireperf/fireperf-0.3.0.tar.gz) (2026-10-26); BLAKE2b-512 `5f21302765f34a3043fc5df984b13f21355742ad787af84fb5c5d89707bbda079e1a84de465053e59a7f3ac2bb25d72fe45ba0084132d3a4067582bac9962a85`; compiled from source in disposable Fedora 44 toolbox.
**Full report:** [2026-11-04 bounded loopback network lab](../reviews/ipfire-fireperf/2026-11-04.md) · [reproducible script](../experiments/2026-11-04-bk059-fireperf-loopback-lab.py) · [results JSON](../data/results/ipfire-fireperf/2026-11-04.json).

**Original tool verification:** `make` succeeded, full upstream `make check` incomplete (23 pass/1 skip, remaining stalled; no full-suite success claim). Original binary executed in rootless Podman `--network=none`: 12/12 trials × 20 = 240/240 TCP connects; `--close` and `--exchange=64:256` counters exact, 0 loss/failed/skipped; negative refused port detected. `auto` backend selected **epoll**, not io_uring. This is not routed throughput, firewall, real AKUZ network, CPU/GiB A/B vs iperf3 or production improvement.

**Decision:** `LAB_VERIFIED_BOUNDED_LOOPBACK / NO_PRODUCTION_APPROVAL`. Potential network diagnostics for AKUZ/DBA on agreed **two-host nonprod** segment only. Aggressive connection rates could saturate conntrack, CPU or shared services. `sequential-rca` may ingest results as independent evidence if schema is validated, but should not generate traffic itself.
