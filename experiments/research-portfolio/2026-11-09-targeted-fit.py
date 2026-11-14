#!/usr/bin/env python3
"""Curated research→project hypotheses; not a deployed integration or scientific A/B."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TARGETS = Path("/var/home/Trintos/projects")
REGISTRY = TARGETS / "project-registry"
DATE = "2026-11-09"
OUT = ROOT / "data/project-fit/portfolio/2026-11-09-targeted-fit.json"
REPORT = ROOT / "portfolio/2026-11-09/targeted-fit.md"

SEAMS = {
    "runtime_prompt": ("dsh-runtime", "packages/api/session-controller/src/commands.ts", r"^\s+async prompt\(", "session input/agent execution boundary"),
    "runtime_cancel": ("dsh-runtime", "packages/api/session-controller/src/client/sessions/session.ts", r"^\s+async cancel\(", "session cancellation boundary"),
    "policy_review": ("agent-config", "tools/review.py", r"^def check_findings\(", "file/line/quote evidence validation"),
    "team_recall": ("dsh-team-context", "src/core/scoped-recall.ts", r"^export async function recallScoped\(", "scoped knowledge retrieval result"),
    "team_index": ("dsh-team-context", "src/core/knowledge-index.ts", r"^export function recall\(", "scored knowledge index lookup"),
    "wiki_retrieve": ("Wiki_PG", "Wiki_PG/ingestion/retrieval_service.py", r"^def retrieve\(", "hybrid retrieval"),
    "wiki_pg_setting": ("Wiki_PG", "Wiki_PG/ingestion/mcp_wiki_server.py", r"^async def get_postgres_setting\(", "read-only structured GUC MCP tool"),
    "wiki_health": ("Wiki_PG", "Wiki_PG/scripts/health_report.py", r"^def scan_tool_failures\(", "read-only diagnostic evidence scanning"),
    "rca_evaluate": ("sequential-rca", "src/sequential_rca/evaluate.py", r"^def evaluate\(", "reference-adjudicated RCA evaluation"),
    "rca_review": ("sequential-rca", "src/sequential_rca/review.py", r"^def score_review\(", "separate RCA review scoring"),
    "telegram_send": ("TelegramBot", "main.py", r"^def send_telegram\(", "external irreversible sendMessage"),
    "telegram_state": ("TelegramBot", "main.py", r"^def save_post_state\(", "local post-send state"),
    "paper_import": ("dsh-paper2agent", "src/paper2project/core.py", r"^\s+def import_research\(", "research import and provenance"),
    "paper_run": ("dsh-paper2agent", "src/paper2project/core.py", r"^\s+def run_experiment\(", "admitted research experiment runner"),
    "paper_review": ("dsh-paper2agent", "src/paper2project/core.py", r"^\s+def review_analysis\(", "review gate"),
    "skill_tests": ("agent-skills", "tests/test_skill_contract.py", r"^class GlobalSkillsReleaseTests\(", "static skill test seam, NOT runtime enforcement"),
    "medical_score": ("TrinMedicalBot", "eval/clinical_review.py", r"^def score\(", "review scoring, not clinical validation"),
    "psql_gui": ("psqlqa", "pg_query_analyzer/app.py", r"^def run_gui\(", "Qt GUI entry, no accessibility API established"),
    "mssql_plan": ("akuz-optimizer-twin", "mssql/compare_plans.py", r"^def compare\(", "offline query-plan comparison"),
    "primary_session": ("dsh-claude-primary-agent", "src/session-binding.ts", r"^export function createSessionBinding\(", "session-ID boundary"),
}

# Baseline/treatment/holdout/effect and rejection rules are hypotheses,
# NOT measured effects. All datasets are synthetic or approved public data.
PROTOCOLS = {
    "citation": {
        "baseline": "Current target quote/path checks",
        "variant": "Typed claim→source-span and effect-authority guard",
        "dataset": "80 synthetic claims, 30 supported / 50 forged, sealed 20-case holdout",
        "oracle": "Independent file/line/authorization gold",
        "metrics": "False auto-allow, valid coverage, p95",
        "accept": "0 false auto-allow; valid coverage >= baseline; p95 <=1.25x",
        "negatives": ["correct quote wrong line", "real text fake source", "injected untrusted instruction"],
    },
    "retrieval": {
        "baseline": "Existing unmodified top-k retrieval",
        "variant": "Provenance graph or strict evidence-aware candidate ranking",
        "dataset": "60 frozen query-document cases incl. 15 OOD",
        "oracle": "Independent source ID and exact range labels",
        "metrics": "Recall@5, wrong-source citations, p95",
        "accept": "Recall@5 >= baseline; 0 wrong-source evidence; p95 <=1.25x",
        "negatives": ["stale indexed source", "forged link", "wrong tenant same phrase"],
    },
    "replay": {
        "baseline": "Existing trace or source-only log",
        "variant": "Versioned input/output and state capsule with replay guard",
        "dataset": "40 synthetic episodes + 12 crash/partial/tamper cases",
        "oracle": "Independent state/output hash and effect ledger",
        "metrics": "Replay exactness, tamper detection, overhead",
        "accept": "40/40 deterministic match; 12/12 mutants rejected; no unrecorded effects",
        "negatives": ["mutated source SHA", "truncated trace", "ack lost after effect"],
    },
    "dag": {
        "baseline": "Existing sequential or fixed DAG controller",
        "variant": "Dependency-validated adaptive task handoff",
        "dataset": "48 frozen task DAG and 8 invalid graphs",
        "oracle": "Independent topological and deterministic task oracle",
        "metrics": "Dependency violations, completions, p95",
        "accept": "0 dependency violations; completions >= baseline; p95 <=1.20x",
        "negatives": ["cycle", "completed task replay", "worker crash after partial effect"],
    },
    "routing": {
        "baseline": "Existing allowed-model/tool selector",
        "variant": "Scoped routing and reduced-context selection with safe fallback",
        "dataset": "100 synthetic labelled requests with 20 sealed holdout",
        "oracle": "Predefined allowed target set and task scorer",
        "metrics": "Invalid routes, task coverage, context size",
        "accept": "0 unauthorized routes; coverage >= baseline; context <=0.90x",
        "negatives": ["similar forbidden tool", "missing schema", "provider unavailable"],
    },
    "experiment": {
        "baseline": "Current source review and manual reference tests",
        "variant": "Isolated candidate evaluation with independent held-out promotion",
        "dataset": "30 toy improvements, 6 score/source mutations",
        "oracle": "Frozen independent code/output oracle",
        "metrics": "False promotion, validated gain, CPU and wall overhead",
        "accept": "0 bad promotions; 6/6 mutations blocked; no train-only selection",
        "negatives": ["scorer mutation", "train overfit", "changed source commit"],
    },
    "source_pin": {
        "baseline": "Plain working-directory source handoff",
        "variant": "Git archive at fixed SHA plus immutable input manifest",
        "dataset": "30 synthetic repositories and 12 corrupt/dirty/missing-source controls",
        "oracle": "External git archive byte digest and independent manifest",
        "metrics": "Provenance false accept, artifact completeness",
        "accept": "0 unpinned/corrupt accepted; 30/30 valid snapshots replayable",
        "negatives": ["dirty untracked file", "wrong SHA", "deleted source checkout"],
    },
    "delivery": {
        "baseline": "Current sendMessage then local post_state",
        "variant": "Durable outbox with UNKNOWN quarantine and explicit reconciliation",
        "dataset": "120 mocked sends across ack/timeout/ambiguous/crash states",
        "oracle": "Independent mock server committed-send ledger",
        "metrics": "Duplicate sends, lost messages, ambiguous states",
        "accept": "No UNKNOWN retry without reconciliation; fewer duplicates, no false success",
        "negatives": ["server commit then lost ACK", "crash before local state", "timeout before effect"],
    },
    "sql": {
        "baseline": "Existing deterministic read-only PG state service",
        "variant": "Versioned MCP read adapter over same exact GUC fields",
        "dataset": "40 synthetic pg_settings snapshots and 8 corrupted fixtures",
        "oracle": "Independent exact SQL values and unit parsing",
        "metrics": "Numerical equivalence, stale handling, p95",
        "accept": "40/40 exact matching, 8/8 invalid rejected, no DB/network writes",
        "negatives": ["stale GUC", "invalid unit", "partial timeout"],
    },
}
PROTOCOLS.update({
    "security": {
        "baseline": "Existing policy, prompt and skill-file checks",
        "variant": "Deterministic effect gate separated from untrusted text",
        "dataset": "80 synthetic task+attack cases, incl. 20 legitimate tasks and 8 mutants",
        "oracle": "Independent allowed-operation labels, not model judgment",
        "metrics": "Unauthorized effects, legitimate completion",
        "accept": "0 unauthorized effects; legitimate coverage >= baseline; 8/8 mutants blocked",
        "negatives": ["fake SYSTEM in markdown", "tool reply role spoof", "malicious dependency"],
    },
    "skills": {
        "baseline": "Current skill and static contract tests",
        "variant": "Source-aware scoped skill/review contract",
        "dataset": "50 synthetic invocations incl. 15 missing evidence and 10 OOD",
        "oracle": "Independent source and allowed-operation gold",
        "metrics": "Ungrounded PASS, valid coverage, time/tokens",
        "accept": "0 ungrounded PASS; legitimate coverage >= baseline; no real secrets",
        "negatives": ["untrusted SKILL text", "same basename different repo", "missing citation"],
    },
    "graph": {
        "baseline": "Current direct source/link lookup",
        "variant": "Versioned provenance edges and typed graph traversal",
        "dataset": "45 synthetic linked artifacts + 30 path queries + 10 corrupt links",
        "oracle": "Independent directed-edge and source-hash membership",
        "metrics": "Correct links, wrong direction, false edges",
        "accept": "0 false edges; valid-link recall >= baseline; 10/10 bad rejected",
        "negatives": ["reversed edge", "stale source hash", "cross-scope link"],
    },
    "diagnostics": {
        "baseline": "Current offline incident/RCA evaluation without new telemetry",
        "variant": "Read-only event provenance and evidence-aware abstention",
        "dataset": "50 synthetic host/DB traces incl. 10 decoys; no live targets",
        "oracle": "Independent event-to-causal-mechanism adjudication",
        "metrics": "False causal PASS, supported-case coverage, overhead",
        "accept": "0 unsupported causal PASS; coverage >= baseline; no external effect",
        "negatives": ["PID reuse", "reordered timestamps", "irrelevant but correlated event"],
    },
    "visual": {
        "baseline": "Existing text/table report or manual GUI behavior",
        "variant": "Read-only SVG or accessibility rendering from frozen observations",
        "dataset": "25 synthetic charts/desktop states incl. invalid and zero cases",
        "oracle": "Exact values and accessibility element identifiers",
        "metrics": "Numeric correctness, invalid SVG, unsafe UI actions",
        "accept": "25/25 correct; 0 invalid SVG/unsafe click; no production UI",
        "negatives": ["negative/zero value", "missing aria label", "truncated source"],
    },
    "medical": {
        "baseline": "Current synthetic clinical-response protocol",
        "variant": "Expert-adjudicated sequential differential and safe-abstention rubric",
        "dataset": "60 fabricated no-PHI medical vignettes; specialist-sealed gold",
        "oracle": "Independent qualified clinician evaluation and severity rubric",
        "metrics": "Unsafe certainty, red-flag referral, clinical correctness",
        "accept": "NO deployment from this pilot; 0 critical safety failures before further expert evaluation",
        "negatives": ["urgent red flags", "ambiguous symptoms", "contraindication unknown"],
    },
    "identity": {
        "baseline": "Current source-ID sanitizer and index lookup",
        "variant": "Collision-guarded canonical IDs without destructive migration",
        "dataset": "60 synthetic IDs with Unicode/separator cases",
        "oracle": "Exact injectivity and scope membership",
        "metrics": "Collision rate, lookup agreement, false source alias",
        "accept": "0 distinct-ID collisions, 0 cross-scope lookups, existing valid IDs stable",
        "negatives": ["a/b vs ab", "Unicode confusable", "empty ID"],
    },
})

PROTOCOLS.update({
    "typestate_dotnet": {
        "baseline": "Current documented type/API policy and negative-compilation witnesses",
        "variant": "Roslyn incremental analyzer or typestate design forbidding bad transitions at compile time",
        "dataset": "40 synthetic C# projects: 20 permitted, 20 forbidden states and generic wrapper cases",
        "oracle": "Independent documented door/guard transitions and actual compiler diagnostics",
        "metrics": "Illegal states compiled, legitimate builds preserved, compiler overhead",
        "accept": "0/20 forbidden compile; 20/20 valid compile; no unapproved diagnostic suppression",
        "negatives": ["generic wrapper bypass", "delegate capturing forbidden state", "dependency boundary escaped"],
    },
    "docx_styles": {
        "baseline": "Plain-text extraction of official source document",
        "variant": "OOXML-aware extraction preserving color/highlight/hidden-style requirements",
        "dataset": "24 synthetic DOCX with paired styled and unstyled warnings, no protected documents",
        "oracle": "Independent OOXML package semantics and clause-preservation labels",
        "metrics": "Lost critical cues, parser disagreement, completion coverage",
        "accept": "0 omitted mandatory cues on 24 fixtures; no newly invented warning",
        "negatives": ["highlight-only warning", "nested style inheritance", "broken relationship"],
    },
    "privacy": {
        "baseline": "Existing structured PII detector on synthetic text",
        "variant": "Conservative content-sensitivity guard and explicit human confirmation",
        "dataset": "60 synthetic emails, medical narratives and neutral strings",
        "oracle": "Independent seeded content class and required disclosure scope",
        "metrics": "False negative PII, false positive quarantine, data egress",
        "accept": "0 synthetic sensitive egress; seeded sensitive recall >= baseline; no automatic post",
        "negatives": ["Russian medical narrative", "split email identifier", "lookalike benign medical term"],
    },
    "jsonc": {
        "baseline": "Current config policy and strict JSON parse",
        "variant": "JSONC canonical parse rejecting duplicate keys and unsafe override",
        "dataset": "60 synthetic valid/invalid JSONC trees, including comments and trailing commas",
        "oracle": "Independent JSONC syntax and duplicate-key/permission gold",
        "metrics": "Bad configs accepted, valid configs preserved, parse time",
        "accept": "0 duplicate privilege keys accepted; all valid semantics match baseline",
        "negatives": ["duplicate security key", "comment-trailing comma", "ambiguous Unicode escape"],
    },
    "pg_health": {
        "baseline": "Existing dated PostgreSQL health snapshot or missing-state abstention",
        "variant": "Read-only typed relation/XID/autovacuum evidence adapter",
        "dataset": "40 synthetic pg_stat_relation/txid snapshots with corrupt/stale variants",
        "oracle": "Independent freeze headroom, stale snapshot and alert thresholds",
        "metrics": "Wrong XID risk label, false OK on missing stats, p95",
        "accept": "0 false OK on missing/stale data; exact fixture alert decisions; no database writes",
        "negatives": ["statistics reset", "missing monitor", "toast age exceeds heap age"],
    },
})

# Format: study | project | verified code seam or "-" | protocol | exact
# project-specific causal hypothesis. Review: current registered source+project
# assessment is *historical*; it is not a new production approval.
BOUNDED_PAIRS = """
agent-error-dataset|akuz-issue|-|replay|Привязать причину и ремедиацию к неизменному incident evidence и различать fail от неизвестного состояния.
agent-error-dataset|dsh-runtime|runtime_prompt|replay|Восстанавливать безопасный ход по журналу действий и обнаруживать неполные tool outcomes.
agent-mosaic|dsh-runtime|runtime_prompt|citation|Запретить публикацию вывода, если claim основан на неразрешённом источнике.
agent-mosaic|dsh-team-context|team_recall|retrieval|Сохранять source scope в retrieved evidence до итогового ответа.
agent-risk|dsh-runtime|runtime_prompt|replay|Повторно оценивать риск изменений runtime по воспроизводимой сцене до merge.
agent-risk|agent-config|policy_review|citation|Различать доказанное нарушение политики и голословное замечание ревьюера.
alphaxiv-openresearch|dsh-paper2agent|paper_import|source_pin|Восстановить точную версию статьи и исходника после удаления исходной рабочей папки.
benchshield|dsh-paper2agent|paper_review|citation|Не принимать заявленное улучшение на неподтверждённом score/trace.
chartli|akuz-schema-inventory|-|visual|Проверять машинную корректность SVG-графиков по снимкам схемы, не превращая оценку SQL cost во время выполнения.
cursor-token-efficiency|dsh-runtime|runtime_prompt|routing|Уменьшить input schema context при сохранении выбора обязательных инструментов.
cursor-token-efficiency|HermesAgent|-|routing|Динамическая передача только нужных tool schemas без ложного исключения доступных функций.
decision-geometry-harness|agent-config|policy_review|security|Сравнить строгую схему review evidence с текущей на одинаковых synthetic policy decisions.
decision-geometry-harness|dsh-runtime|runtime_prompt|routing|Проверить, меняет ли форма tool schema фактический выбор разрешённого инструмента.
drag|Wiki_PG|wiki_retrieve|retrieval|Не ускорять ответы ценой ложных ссылок при OOD изменениях формата и подложной информации.
dsh-creator-mode|agent-skills|skill_tests|skills|Проверять формат создаваемого skill/tool bundle до публикации, без запуска произвольного кода.
dsh-superagent-prototype|dsh-runtime|runtime_prompt|dag|Сопоставить Ticket lifecycle и допустимые действия с реальными session permissions.
dsh-superagent-prototype|dsh-claude-primary-agent|primary_session|dag|Не считать новый task завершённым при потере session binding.
exactly-once-limbo|TelegramBot|telegram_send|delivery|Сократить дубли отправок на неоднозначном Telegram ACK, признавая окно неустранимой неопределённости.
exactly-once-limbo|HermesAgent|-|delivery|Не повторять необратимое tool действие без durable result reconciliation.
experienceindex|dsh-team-context|team_recall|graph|Увеличить точность ссылок на первичные документы при сохранении scoped recall.
experienceindex|Wiki_PG|wiki_retrieve|graph|Хранить проверяемое source id и путь документа при retrieval top-k.
goal-aware-dynamic-collaboration|dsh-runtime|runtime_prompt|dag|Снизить нарушения зависимостей при параллельной работе с инструментами.
goal-aware-dynamic-collaboration|hermes-akuz-agents|-|dag|Разграничить агентские handoff и обязательные DBA prerequisites.
gpt6-astra-skills-prompts|agent-skills|skill_tests|skills|Сократить нерелевантные skill tokens, не теряя обязательных проверок.
gpt6-astra-skills-prompts|agent-config|policy_review|skills|Сравнить загрузку минимального review contract с полным на одних offline задачах.
harness2|agent-config|policy_review|experiment|Выбирать проверяющего только по отдельному holdout, не по первому удачному seed.
htn-orchestrate|dsh-runtime|runtime_prompt|dag|Сравнить fixed DAG с HTN под одинаковым бюджетом и отказами worker.
htn-orchestrate|hermes-akuz-agents|-|dag|Не запускать зависимые DBA шаги до завершения проверяемых prerequisite.
inspektor-gadget|sequential-rca|rca_evaluate|diagnostics|Добавлять проверенный Linux eBPF event к причине RCA без корреляционной ошибки.
inspektor-gadget|Wiki_PG|wiki_health|diagnostics|Разделить наблюдаемый I/O/proc event и неподтверждённое утверждение о причине.
ipfire-fireperf|sequential-rca|rca_evaluate|diagnostics|Потреблять только отдельно снятые latency/refusal данные без собственного нагрузочного трафика.
julia-1|dsh-runtime|-|routing|Показывать допустимые candidate-route вероятности без подмены их откалиброванным confidence.
karpathy-autoresearch|dsh-paper2agent|paper_run|experiment|Проводить source-pinned эксперимент и отвергать gain только на train subset.
karpathy-autoresearch|Wiki_PG|wiki_retrieve|experiment|Разделить гиперпараметры retrieval benchmark и неизменяемый набор проверочных query.
local-knowledge-graph|sequential-rca|rca_evaluate|graph|Не выдавать ориентированный causal edge за двунаправленную подтверждённую причинность.
mcp-toolbox-postgres|Wiki_PG|wiki_pg_setting|sql|Сверить MCP read с прямыми pg_settings на одинаковом фиксированном snapshot.
microsoft-skill-recorder|agent-skills|skill_tests|privacy|Не превращать внешнюю запись с чувствительным текстом в skill без предварительной проверки.
novafabric|dsh-runtime|runtime_prompt|replay|Обеспечить точную сверку offline agent tool replay без утверждения о полной изоляции побочных эффектов.
novafabric|sequential-rca|rca_review|replay|Сопоставить audit artifact с исходным report/trace в отдельном изолированном запуске.
open-steps|agent-config|policy_review|skills|Не считать отсутствие Git tracked diff доказательством отсутствия изменений в untracked files.
pgbot|Wiki_PG|-|pg_health|Не путать недоступный snapshot PostgreSQL statistics с доказательством отсутствия vacuum проблемы.
pgbot|sequential-rca|rca_evaluate|diagnostics|Передавать PG health snapshots с явным age/staleness и без прямого подключения к production.
rrsi|agent-config|policy_review|experiment|Не продвигать model prompt/guard по тренировочному oracle без separate holdout.
simurg|dsh-runtime|runtime_prompt|diagnostics|Проверять алерты на agent/tool traces с количественным false alarm контролем.
simurg|9router|-|diagnostics|Не переводить аномальный provider response в автоматическое переключение модели без явного safety policy.
tencent-teamai-cli|dsh-team-context|team_recall|skills|Тестировать локальный import/handoff skills без произвольного сетевого доступа.
toolgrad|dsh-paper2agent|paper_run|experiment|Не использовать нулевой count ошибок как доказательство фактической корректности цепочки tools.
toolgrad|agent-skills|skill_tests|skills|Сверять шаги навыка с внешним oracle, а не с self-reported success.
understand-anything|dsh-team-context|team_recall|graph|Не смешивать path traversal/symlink source с разрешёнными документами проекта.
vercel-agent-desktop|psqlqa|psql_gui|visual|Оценить доступность GUI для изолированного read-only audit, не активируя действия с реальной БД.
veriharness|agent-skills|skill_tests|citation|Отвергать proof snippet вне заявленного файла/строки, сохраняя корректные findings.
veriharness|dsh-paper2agent|paper_review|citation|Не считать цитату доказательством без проверки идентичности источника и контекста.
warp-skill-doctor|agent-skills|skill_tests|skills|Не объединять skill invocation traces от одноимённых, но чужих проектов.
yahont-ce|Wiki_PG|wiki_retrieve|identity|Не допускать неявного alias разных документов после нормализации search ID.
youtube-skills|agent-skills|skill_tests|skills|Пропускать непроверенный transcript/provider output только как untrusted data.
zero-code|agent-config|-|jsonc|Парсить JSONC по строгим правилам дублированных ключей до policy admission.
""".strip()

# No physically verified editable model/router or CLI consumer currently under owner control.
BOUNDED_DEFERRED = {
    "cera-moa": "No own trainable adapter/model candidate or held-out routing corpus verified; author LoRA/MoA results cannot be directly attached to API-only agents.",
    "rea": "No justified binary/managed artifact reconstruction task with a documented owner-maintained consumer; psqlqa potential is a weak profile guess, not a validated integration seam.",
}

# Selected methodological works, not validated author model improvements.
RESEARCH_PAIRS = """
behavior-beyond-text|dsh-runtime|runtime_prompt|security|Сравнить слова отказа с реально разрешёнными side effects инструмента.
concordat|dsh-claude-primary-agent|primary_session|dag|Проверить typestate допустимости resume/cancel вне prompt-only соглашений.
concordat|developer-safe-dotnet-core|-|typestate_dotnet|Проверить проектные Door, Guard и Handed Port контракты через отрицательные compilation witnesses; без доступа к исходникам коллеги это пока только гипотеза.
covert-assistance|agent-config|policy_review|security|Обнаруживать попытки незадекларированного делегирования при source review.
harnesssecurity-bench|dsh-runtime|runtime_prompt|security|Раздельно измерять корректность задачи и запрещённый side effect.
maadbench|sequential-rca|rca_evaluate|diagnostics|Отличать первичную ошибку RCA от downstream каскада неверных выводов.
matoi|dsh-runtime|runtime_prompt|security|Проверять предупреждения о последствиях без подмены authority на side effect.
memscope|dsh-team-context|team_recall|retrieval|Локализовать memory regression на frozen corpus и отделять repair от retrieval noise.
package-hallucination-rule-files|agent-config|policy_review|security|Не повышать рекомендацию пакета из untrusted repository rules до разрешённой установки.
paper2agent|dsh-paper2agent|paper_import|source_pin|Отклонять paper→tool bundle без исходника, лицензии и воспроизводимого версии кода.
poisoned-skills|agent-skills|skill_tests|security|Не подчинять reviewer исполняемой инструкции внутри внешнего SKILL.md.
recap|dsh-runtime|runtime_prompt|routing|Сравнить сохранение критичного evidence после context compression с обычной длинной сессией.
sequential-diagnosis-language-models|TrinMedicalBot|medical_score|medical|Оценивать последовательный клинический дифференциал только экспертно и без PHI.
silent-cue-loss|dsh-paper2agent|paper_import|docx_styles|Отмечать потерянное оформление DOCX как missing-evidence, не выдавая plain text за полный источник.
statecomp|dsh-runtime|runtime_prompt|routing|Не сокращать agent state без проверки сохранения важных source constraints.
swrouter|9router|-|routing|Сравнить multi-turn routing с последним turn-only выбором без живого изменения провайдеров.
trust-region-injection|agent-config|policy_review|security|Разграничить неверифицированный текст источника и исполняемую system policy.
transferable-tool-selection|dsh-runtime|runtime_prompt|routing|Проверить plan→retrieve→select против direct tool choice при frozen tool contracts.
memory-centric-continual-learning|dsh-team-context|team_index|retrieval|Различать recall score и изменённую истину memory по датированным источникам.
""".strip()

def digest(b):
    return hashlib.sha256(b).hexdigest()

def git(repo,*args):
    return subprocess.check_output(["git","-C",str(repo),*args],stderr=subprocess.DEVNULL)

def parsed(text,phase):
    result=[]
    for line in text.splitlines():
        parts=[x.strip() for x in line.split("|")]
        assert len(parts)==5,(phase,line)
        sid,pid,seam,protocol,hypothesis=parts
        assert protocol in PROTOCOLS and len(hypothesis)>=50
        result.append({"phase":phase,"study_id":sid,"project_id":pid,
                       "seam_id":seam,"protocol_id":protocol,"hypothesis":hypothesis})
    return result

def anchor(seam,pid):
    repo,path,pattern,boundary=SEAMS[seam]
    assert repo==pid
    ref="origin/main" if pid=="dsh-paper2agent" else "HEAD"
    commit=git(TARGETS/pid,"rev-parse",ref).decode().strip()
    data=git(TARGETS/pid,"show",commit+":"+path)
    lines=[n for n,line in enumerate(data.decode("utf8").splitlines(),1) if re.search(pattern,line)]
    assert len(lines)==1,(seam,lines)
    return {"repo":pid,"commit":commit,"path":path,"line":lines[0],
            "file_sha256":digest(data),"symbol":pattern,"boundary":boundary,
            "url":f"https://github.com/Artemedi/{pid}/blob/{commit}/{path}#L{lines[0]}"}

BASIS=ROOT/"data/results/research-portfolio/2026-11-09-basis-manifest.json"

def scope_hash(ent,ids):
    """Hash only the entities of the snapshot's studies; later catalog growth must not change it."""
    ids=set(ids)
    sub={"studies":sorted((s for s in ent["studies"] if s["id"] in ids),key=lambda r:r["id"]),
         "versions":sorted((v for v in ent["versions"] if v["study_id"] in ids),key=lambda r:r["id"]),
         "reviews":sorted((r for r in ent["reviews"] if ids&set(r["study_ids"])),key=lambda r:r["id"]),
         "assessments":sorted((a for a in ent["assessments"] if a["study_id"] in ids),key=lambda r:r["id"]),
         "current_assessments":sorted((c for c in ent["current_assessments"] if c["study_id"] in ids),key=lambda r:(r["study_id"],r["project_id"]))}
    return digest(json.dumps(sub,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode())

def build():
    rawent=(ROOT/"catalog/entities.json").read_bytes()
    rawledger=(ROOT/"data/results/research-portfolio/2026-11-09-closure-ledger.json").read_bytes()
    ent=json.loads(rawent);ledger=json.loads(rawledger)
    disp={r["study_id"]:r["closure_status"] for r in ledger["studies"]}
    profiles={p.parent.name:p for p in (REGISTRY/"projects").rglob("PROJECT.md")}
    assert len(profiles)==45 and set(profiles)=={p["id"] for p in ent["projects"]}
    assert all(len(p.read_text(encoding="utf8"))>100 for p in profiles.values())
    prior={(v["study_id"],v["project_id"]):v["assessment_id"] for v in ent["current_assessments"]}
    assessments={a["id"]:a["decision"] for a in ent["assessments"]}
    bounded=parsed(BOUNDED_PAIRS,"ACCEPT_BOUNDED")
    selected=parsed(RESEARCH_PAIRS,"ACCEPT_RESEARCH_ONLY")
    assert ({r["study_id"] for r in bounded}|set(BOUNDED_DEFERRED))=={s for s in disp if disp[s]=="ACCEPT_BOUNDED"}
    assert not ({r["study_id"] for r in bounded}&set(BOUNDED_DEFERRED))
    anchors={}
    pairs=[]
    for item in bounded+selected:
        r=item.copy();sid=r["study_id"];pid=r["project_id"];seam=r.pop("seam_id")
        assert disp[sid]==r["phase"] and pid in profiles
        old=prior.get((sid,pid))
        if r["phase"]=="ACCEPT_BOUNDED":
            assert old is not None,("prior assessment missing",sid,pid)
        r["prior_assessment"]=old
        r["prior_decision"]=assessments[old] if old else None
        if seam!="-":
            if seam not in anchors:anchors[seam]=anchor(seam,pid)
            r["source_anchor"]=anchors[seam]
            r["interface_status"]="PINNED_SYMBOL_EXISTS_ADAPTER_UNBUILT"
            r["interface_proposal"]="Proposed consumer boundary: "+anchors[seam]["boundary"]
        else:
            r["source_anchor"]=None
            r["interface_status"]="PROFILE_MATCH_SOURCE_SEAM_UNCONFIRMED"
            r["interface_proposal"]="Identify consumer, input/output contract and test seam in pinned code of "+pid
        r["expected_effect"]="HYPOTHESIS_NOT_MEASURED: "+r["hypothesis"]
        r["test_protocol_id"]=r["protocol_id"]
        r["experiment_executed"]=False
        r["production_approved"]=False
        r["priority"]="P0" if r["source_anchor"] and sid in {
            "agent-mosaic","agent-risk","drag","exactly-once-limbo",
            "htn-orchestrate","mcp-toolbox-postgres","novafabric",
            "veriharness","harnesssecurity-bench","paper2agent",
            "poisoned-skills","sequential-diagnosis-language-models"
        } else "P1" if r["source_anchor"] else "P2"
        pairs.append(r)
    pilot_specs=[
        ("telegram-ack","data/results/research-portfolio/2026-11-09-telegram-ack-fixture.json","telegram_send"),
        ("agentconfig-quote","data/results/research-portfolio/2026-11-09-agentconfig-quote-fixture.json","policy_review"),
    ]
    pilots=[]
    for name,path,seam in pilot_specs:
        raw=(ROOT/path).read_bytes()
        pilot=json.loads(raw)
        assert pilot["source_file_sha256"]==anchors[seam]["file_sha256"]
        if name=="telegram-ack":
            assert pilot["status"]=="SOURCE_FUNCTIONS_REPRODUCED_MOCK_ONLY"
            assert pilot["records"]["remote_commit_ack_lost"]["remote_effect_count"]==2
            assert pilot["records"]["ack_normal"]["remote_effect_count"]==1
            assert pilot["records"]["no_remote_commit"]["remote_effect_count"]==1
        else:
            assert pilot["status"]=="PINNED_ORIGINAL_SOURCE_FALSE_LINE_BINDING_REPRODUCED"
            assert pilot["false_line_binding_cases"]==1
        pilots.append({"name":name,"path":path,"sha256":digest(raw),
                       "source_anchor_id":seam,"status":pilot["status"],
                       "scope":"original function in network-denied sandbox; no candidate implementation"})
    return {"date":DATE,"status":"DESIGN_ONLY_NOT_EXECUTED",
            "basis_entities_sha256":json.loads(BASIS.read_text())["historical_entities_file_sha256"],"basis_ledger_sha256":digest(rawledger),
            "registry_commit":git(REGISTRY,"rev-parse","HEAD").decode().strip(),
            "profile_count":len(profiles),"private_profile_bodies_published":False,
            "bounded_screened":40,"bounded_deferred":BOUNDED_DEFERRED,
            "research_only_screened":39,
            "research_only_selected":sorted({r["study_id"] for r in selected}),
            "research_only_not_selected":sorted(s for s in disp if disp[s]=="ACCEPT_RESEARCH_ONLY" and s not in {r["study_id"] for r in selected}),
            "source_anchors":anchors,"protocols":PROTOCOLS,"source_pilots":pilots,
            "pairs":sorted(pairs,key=lambda r:(r["phase"]!="ACCEPT_BOUNDED",
                 {"P0":0,"P1":1,"P2":2}[r["priority"]],r["study_id"],r["project_id"])),
            "limits":["No live model, SQL, patient data, Telegram send or project writes",
                      "Pinned source symbol is not a working adapter",
                      "Unlisted pairs are NOT assessed and are not NO_FIT",
                      "Prior fit assessments in catalog/entities.json unchanged",
                      "Benefits and acceptance thresholds are hypotheses, not measured gains"]}

def validate(x):
    ent=json.loads((ROOT/"catalog/entities.json").read_text())
    ledger=json.loads((ROOT/"data/results/research-portfolio/2026-11-09-closure-ledger.json").read_text())
    disp={v["study_id"]:v["closure_status"] for v in ledger["studies"]}
    assert x["status"]=="DESIGN_ONLY_NOT_EXECUTED"
    basis=json.loads(BASIS.read_text())
    assert x["basis_entities_sha256"]==basis["historical_entities_file_sha256"]
    assert scope_hash(ent,list(disp))==basis["scope_entities_sha256"]
    assert x["basis_ledger_sha256"]==digest((ROOT/"data/results/research-portfolio/2026-11-09-closure-ledger.json").read_bytes())
    assert x["profile_count"]==45 and not x["private_profile_bodies_published"]
    assert x["bounded_screened"]==40 and x["research_only_screened"]==39
    assert len(x["bounded_deferred"])==2 and len(x["pairs"])>=55
    assert len(x["research_only_selected"])>=10
    assert len(x["source_pilots"])==2
    for pilot in x["source_pilots"]:
        raw=(ROOT/pilot["path"]).read_bytes()
        result=json.loads(raw)
        assert digest(raw)==pilot["sha256"]
        assert result["status"]==pilot["status"]
        assert result["source_file_sha256"]==x["source_anchors"][pilot["source_anchor_id"]]["file_sha256"]
        if pilot["name"]=="telegram-ack":
            assert result["records"]["remote_commit_ack_lost"]["duplicate_remote_effect"] is True
            assert result["records"]["ack_normal"]["duplicate_remote_effect"] is False
            assert result["records"]["remote_commit_ack_lost"]["state_recorded_before_retry"] is False
        else:
            assert result["false_line_binding_cases"]==1
            assert sum(r["false_line_binding_if_fields_anded"] for r in result["records"])==1
    projects={v["id"] for v in ent["projects"]}
    seen=set();anchored=0
    for r in x["pairs"]:
        key=(r["study_id"],r["project_id"])
        assert key not in seen and r["project_id"] in projects
        seen.add(key)
        assert disp[r["study_id"]]==r["phase"]
        assert r["test_protocol_id"] in x["protocols"]
        assert not r["experiment_executed"] and not r["production_approved"]
        assert len(r["hypothesis"])>=50
        assert r["expected_effect"].startswith("HYPOTHESIS_NOT_MEASURED")
        assert len(r["interface_proposal"])>20
        if r["source_anchor"]:
            a=r["source_anchor"]
            assert r["interface_status"]=="PINNED_SYMBOL_EXISTS_ADAPTER_UNBUILT"
            assert a["repo"]==r["project_id"] and re.fullmatch("[a-f0-9]{40}",a["commit"])
            assert re.fullmatch("[a-f0-9]{64}",a["file_sha256"]) and a["line"]>=1
            assert a["url"].endswith("#L"+str(a["line"]))
            anchored+=1
        else:
            assert r["interface_status"]=="PROFILE_MATCH_SOURCE_SEAM_UNCONFIRMED"
    assert {s for s in disp if disp[s]=="ACCEPT_BOUNDED"}==({r["study_id"] for r in x["pairs"] if r["phase"]=="ACCEPT_BOUNDED"}|set(x["bounded_deferred"]))
    assert set(x["research_only_selected"])=={r["study_id"] for r in x["pairs"] if r["phase"]=="ACCEPT_RESEARCH_ONLY"}
    assert not (set(x["research_only_not_selected"]) & {r["study_id"] for r in x["pairs"]})
    for p in x["protocols"].values():
        assert len(p["negatives"])>=3
        assert all(len(p[k])>=10 for k in ("baseline","variant","dataset","oracle","metrics","accept"))
    assert len(x["source_anchors"])>=10
    return {"pairs":len(x["pairs"]),"source_anchored":anchored,
            "distinct_source_symbols":len(x["source_anchors"]),
            "profile_only":len(x["pairs"])-anchored,
            "bounded_covered":40,"bounded_deferred":2,
            "research_only_selected":len(x["research_only_selected"]),
            "protocols":len(x["protocols"])}

def render(x):
    counts=validate(x)
    lines=["# Targeted research-to-project applicability: executable test proposals","",
           "2026-11-09. Pinned private project-registry source commit: "+x["registry_commit"]+". "
           "45 profiles checked for existence; no private text published.",
           "",
           "This is a candidate decision matrix, NOT measured improvement, code integration, "
           "author-paper replication or permission to deploy. A verified symbol only means "
           "the named function exists in the named pinned Git object.",
           "",
           "Scope: {} candidate pairs ({} pair-rows referencing {} DISTINCT pinned source symbols, "
           "{} profile-only); all 40 ACCEPT_BOUNDED reviewed (2 deferred), and "
           "{} selected research-only works. Shared symbols are reused across methods and "
           "must not be mistaken for {} independently validated integrations.".format(
               counts["pairs"],counts["source_anchored"],
               counts["distinct_source_symbols"],counts["profile_only"],
               counts["research_only_selected"],counts["source_anchored"]),
           "",
           "## Two source feasibility checks actually executed","",
           "- **TelegramBot / exactly-once-limbo:** [original source function mock replay](../../data/results/research-portfolio/2026-11-09-telegram-ack-fixture.json) "
           "observed 2 remote effects after commit+lost ACK+retry, versus 1 with normal ACK or failure before commit. "
           "This is a baseline defect boundary only; no outbox improvement or network request was executed.",
           "- **agent-config / source citation:** [original check_findings function replay](../../data/results/research-portfolio/2026-11-09-agentconfig-quote-fixture.json) "
           "returned location_ok=true and evidence_found=true for a quote that exists elsewhere in the file but not at its declared line. "
           "This tests diagnostic fields; it does NOT establish downstream automatic acceptance or remote exploit.",
           "",
           "## P0: first source-anchored experiments","",
           "| Study | Project | Consumer symbol at repo@SHA | Hypothesis | A/B |",
           "| --- | --- | --- | --- | --- |"]
    for r in x["pairs"]:
        if r["priority"]!="P0":continue
        a=r["source_anchor"]
        lines.append("| {} | {} | [{}:{}]({}) | {} | [{}](#{}) |".format(
            r["study_id"],r["project_id"],a["path"],a["line"],a["url"],
            r["hypothesis"],r["protocol_id"],r["protocol_id"]))
    for phase,title in [("ACCEPT_BOUNDED","Remaining bounded-research candidate interfaces"),
                        ("ACCEPT_RESEARCH_ONLY","Selected method-only research candidates")]:
        lines.extend(["","## "+title,"","| Study | Project | Source seam | Effect hypothesis | A/B |",
                      "| --- | --- | --- | --- | --- |"])
        for r in x["pairs"]:
            if r["phase"]!=phase or (phase=="ACCEPT_BOUNDED" and r["priority"]=="P0"):continue
            a=r["source_anchor"]
            s=("[{}:{}]({})".format(a["path"],a["line"],a["url"]) if a else "PROFILE ONLY — source seam not verified")
            lines.append("| {} | {} | {} | {} | [{}](#{}) |".format(
                r["study_id"],r["project_id"],s,r["hypothesis"],r["protocol_id"],r["protocol_id"]))
    lines.extend(["","## Deliberately deferred bounded studies",""])
    for sid,why in x["bounded_deferred"].items():lines.append("- **{}**: {}".format(sid,why))
    lines.extend(["","## Proposed offline paired experiments (NOT executed)",""])
    for name,p in x["protocols"].items():
        lines.extend(["### "+name,"",
                      "**Baseline:** "+p["baseline"]+". **Variant:** "+p["variant"]+".",
                      "**Dataset:** "+p["dataset"]+". **Independent oracle:** "+p["oracle"]+".",
                      "**Metrics:** "+p["metrics"]+". **Acceptance criterion:** "+p["accept"]+".",
                      "**Negative controls:** "+"; ".join(p["negatives"])+".",""])
    lines.extend(["## Evidence boundary","",
        "Historical 506 explicit source-to-project assessments remain unchanged. "
        "Other study–project pairs have not been assessed; no inferred NO_FIT. "
        "Before running a P0, independently inspect the exact source and consumer contract, "
        "freeze the corpus, run two arms with an external oracle, preserve costs, negative "
        "results and source hashes, and request owner approval. Clinical work requires "
        "qualified independent specialist validation. This file contains no real clinical "
        "or employer data.",""])
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--generate",action="store_true")
    p.add_argument("--check",action="store_true")
    a=p.parse_args();assert a.generate!=a.check
    if a.generate:
        result=build()
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        REPORT.write_text(render(result))
    else:
        result=json.loads(OUT.read_text())
        assert REPORT.read_text()==render(result),"Stale human report"
        mutations=[
            lambda v:v["pairs"][0].update(production_approved=True),
            lambda v:v["pairs"][0].update(project_id="NOT_A_PROJECT"),
            lambda v:v["pairs"][0].update(test_protocol_id="NOT_DEFINED"),
            lambda v:v["pairs"].pop(),
            lambda v:v["pairs"][0].update(experiment_executed=True),
        ]
        for mutate in mutations:
            damaged=copy.deepcopy(result);mutate(damaged)
            try:validate(damaged)
            except AssertionError:continue
            raise AssertionError("Fail-open: invalid candidate matrix accepted")
    print("PROJECT_FIT", "GENERATED" if a.generate else "PASS",validate(result))
if __name__=="__main__":
    main()
