# Individually indexed studies — previously reviewed in DSH

This index promotes **16 historically source-reviewed items** from the original DSH
research decisions into separate traceable records. Their original reviews and
full methodological qualifications are preserved via pinned SHA and archive links.
This is a document migration and extraction, **not a new independent replication**.

| Study | Area | Historical evidence status |
| --- | --- | --- |
| [Red-Teaming Auto Mode](red-teaming-auto-mode.md) | `SECURITY` | `PUBLIC_METHODS_REVIEW_RECORDED_APPENDICES_NOT_INSPECTED` |
| [REALM — Retrieval-Driven Memory Reconsolidation](realm.md) | `MEMORY` | `FULL_TEXT_REVIEW_RECORDED` |
| [DRAG — Dynamic Retriever and Generator Selection](drag.md) | `RETRIEVAL` | `FULL_TEXT_REVIEW_RECORDED` |
| [Paper2Agent — Research Papers as Reliable AI Agents](paper2agent.md) | `RESEARCH_WORKFLOW` | `FULL_TEXT_REVIEW_RECORDED` |
| [CERA-MoA — Adaptive Multi-Agent Routing](cera-moa.md) | `MODEL_ROUTING` | `FULL_TEXT_REVIEW_RECORDED` |
| [Where Does Exactly-Once Live? / LIMBO](exactly-once-limbo.md) | `RELIABILITY` | `FULL_TEXT_REVIEW_RECORDED` |
| [Cursor — Improved Token Efficiency](cursor-token-efficiency.md) | `INFERENCE_EFFICIENCY` | `FULL_ENGINEERING_ARTICLE_REVIEW_RECORDED` |
| [StateComp — State-Conditioned Context Compression](statecomp.md) | `CONTEXT_MANAGEMENT` | `FULL_TEXT_REVIEW_RECORDED` |
| [Self-Replicating Prompt Injections Exist](self-replicating-prompt-injections.md) | `SECURITY` | `FULL_PUBLIC_DISCLOSURE_REVIEW_RECORDED` |
| [KVSET — The KV Cache Working Set](kvset.md) | `KV_CACHE` | `FULL_TEXT_REVIEW_AND_LOCAL_TOOL_TEST_RECORDED` |
| [VeriHarness — Evidence-Grounded Agentic Verification](veriharness.md) | `VERIFICATION` | `FULL_TEXT_REVIEW_RECORDED` |
| [Agent Error Dataset — Trace-Grounded Diagnosis and Replay](agent-error-dataset.md) | `ERROR_RECOVERY` | `FULL_TEXT_REVIEW_RECORDED` |
| [Covert Assistance — Helpful LLM Agents Evade Oversight](covert-assistance.md) | `SECURITY` | `FULL_TEXT_REVIEW_RECORDED` |
| [MAADBench — Multi-Agent Anomaly and Fault Benchmarks](maadbench.md) | `EVALUATION` | `FULL_TEXT_REVIEW_RECORDED` |
| [ReCAP — Persistent Context Graphs for Memory Compaction](recap.md) | `MEMORY` | `FULL_TEXT_REVIEW_RECORDED` |
| [KVTether — KV Cache Lifecycle Management in ReAct Agents](kvtether.md) | `KV_CACHE` | `FULL_TEXT_REVIEW_RECORDED` |

## Scope and exclusions

- 2026-09-21: five source assessments. Auto Mode public method text was reviewed;
  the PDF appendices were not independently inspected.
- 2026-09-28: five full-source / first-party technical reviews; KVSET has an
  additional **bounded local test** on pinned original code, which is not a production benefit claim.
- 2026-10-05: six complete scientific-paper assessments, with methodology,
  caveats and accepted research-only dispositions.
- The 15 September early digest contains material including BenchShield, SWRouter,
  ToolGrad, REVA and NovaFabric. Its decision record explicitly identifies
  missing full-paper method verification for some candidates, so none was
  automatically promoted here.
- The 12 and 19 October digests are **reconstructed summaries**, not records of
  complete full-text scientific reviews. Their candidates remain in the immutable archive.
- The 26 October DSH watch preserves an author-supplied review, but explicitly
  says the import is not an independent full-text reread of each paper.
  Its candidates remain historical until source verification per item.
- The 7 October mathematical-models assessment remains available in the
  archive and is not conflated with these 16 paper-source research decisions.

**Evidence levels:** `FULL_TEXT_REVIEW_RECORDED` = an earlier review states
it inspected the complete work (not locally reproduced);
`FULL_ENGINEERING_ARTICLE_REVIEW_RECORDED` and
`FULL_PUBLIC_DISCLOSURE_REVIEW_RECORDED` are primary technical reports
rather than peer-reviewed papers; the other labels record their narrower
qualification. All scores and implementation proposals remain hypotheses
until repeated against a current target project and independent oracle.

**Future reviews:** check these titles, DOIs and URLs before adding a new report.
When reviewing a new source version or another project, create a dated
follow-up in `reports/` and link this prior evidence; do not overwrite history.
