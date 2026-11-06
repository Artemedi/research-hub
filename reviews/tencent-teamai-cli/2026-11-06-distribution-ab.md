# BK-002 — Tencent TeamAI CLI: A/B доставки Team Context против Git+symlink

**Дата:** 2026-11-06. **Вердикт:** `FUNCTIONAL_PASS / SCOPE_GATE_FAIL / NO_INTEGRATION_APPROVAL`. Это ограниченный инженерный эксперимент, не оценка качества LLM-агентов.

## Первоисточник и source pin

Первичный инженерный источник — [Tencent/teamai-cli](https://github.com/Tencent/teamai-cli) и [полный официальный механизм distribution](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/docs/guide/distribution.md). Upstream `7ed698998da8e446d8116c79ae58a9d5ff6ca016`, исходная версия 0.22.0. Предыдущая [проверка кода 2026-11-04](2026-11-04.md) сравнила публичный owner fork `Artemedi/teamai-cli@5a3c371f692675b6e080a6554af5a3da0752fe5c` с upstream, зафиксировала 13 ahead, 732 behind, 6 content conflicts.

**Реально исполняемый код:** локальный owner port `teamai-cli-port-upstream@e5a0bb5901f4b1c78d7b1e28a2ba43e1cbe86db4`, зафиксирован detached Git checkout в одноразовом `/var/tmp/bk002-teamai-lab-20261106/ported`. **Этот точный SHA не опубликован на GitHub Artemedi/teamai-cli** на дату теста (GitHub API HTTP 422, ветка не обнаружена), и его нельзя выдавать за официальный upstream или воспроизводимый публичный релиз. Действующие пользовательские worktrees не изменялись.

Test-only npm install: 307 URL-prefix substitutions в скопированном `package-lock.json` с `https://mirrors.tencent.com/npm/` на `https://registry.npmjs.org/` из-за неработающего прямого registry mapping. Original lock SHA-256 `57260332049299a4e816fb7014ca3e7b2c86c7c0b9b7bc7ab3f4008f7183e293`; altered test-only lock SHA-256 `169ee7079de8239ff2502f2a9e963f8101d5d51b5cfb7a773d10adc921ba50e4`. [Provenance JSON](../../data/results/tencent-teamai-cli/2026-11-06-dependency-lock-rewrite.json). После `npm ci --ignore-scripts --no-audit --no-fund` установлены 367 зависимостей с сохранённой npm integrity verification. **Только dependency installation имела доступ к npm internet**, тесты и A/B без сети.

## Реальные тесты TeamAI

Контейнер: cached `docker.io/library/node:22` через rootless Podman, `--network=none --read-only --cap-drop=all --security-opt=no-new-privileges`, только disposable `/work` и fake HOME; никакие рабочие agent settings, SSH credentials, hooks и MCP tokens не передавались.

| Контроль | Результат |
| --- | --- |
| `npm run build`, tsup | **PASS** |
| Unit: `team-context`, `post-pull`, `pkg-team-distribution` | **38/38 PASS** |
| Actual CLI E2E с локальными bare Git origins, `teamai pull --force` / `push --dry-run` | **7/7 PASS** |
| `npm run typecheck` | **PASS** |
| `npm run lint` (1 646 файлов, 176 правил), docs checks | **0 warnings, 0 errors; docs PASS** |

Actual E2E подтвердил initial skill/governance delivery; update; tombstone on deletion; authoritative governance overwrite after hand-edit; exclusion canonical skills from push; fail-closed invalid schemaVersion and unknown field, previous local materialization unchanged. Это не многомашинный live deployment.

## Независимый 5-seed A/B

[Исполняемый runner](../../experiments/2026-11-06-bk002-teamai-distribution-ab.py) запускает 5 независимых seeds `20261106..20261110` × 8 этапов `initial, update, delete, restore, invalid_schema, unknown_field, recover, idempotent` = **40 операций на каждую ветку**. Порядок A/B перемешан по seed внутри этапа, но последовательность этапов фиксирована. Эталон — SHA256 фактических `SKILL.md` и governance, независимо от CLI self-report.

- **A — простой скрипт Git pull + symlink**, одного dummy skill с удалением symlink при tombstone. **Этот baseline не имеет schema-version/field validation и governance projection по конструкции**; сравнительный p50 не претендует на feature parity с TeamAI или стоимость human review.
- **B — реальный скомпилированный TeamAI CLI** из локального pin с fake `HOME`, `teamContext.schemaVersion:1`, dummy origins; стартовый профиль содержит только `.claude/skills` и `.claude/rules`. Никаких реальных canonical providers.

Обе ветки дали **40/40 правильных результатов согласно своему контракту**. В B governance обновляется; invalid_schema и unknown_field не допускают внедрения подложенного skill, предыдущая материализация сохраняется. В A некорректный upstream skill следует за origin, поскольку в baseline нет проверки контракта; ручная проверка могла бы предотвратить такое поведение. Независимый отрицательный mutant с намеренно неверным ожидаемым SHA был обнаружен (oracle gate PASS).

**Основное отрицательное наблюдение:** при заранее зафиксированном минимальном Claude-only профиле B создал **35 различных путей вне разрешённых `.claude/` и `.teamai/`**, A — 0. В первом B pull появились 8 таких файлов; за все 40 этапов — 35. Примеры: `AGENTS.md`, `.bashrc`, `.profile`, `.codex/hooks.json`, `.openclaw/openclaw.json`, `.pi/agent/extensions/teamai-hooks.ts`, дополнительные skills/hooks в `.tcodex`, `.codex-internal`. **Только temporary HOME, не пользовательский**. TeamAI рассчитан на multi-tool deployment, поэтому это не доказательство уязвимости или непреднамеренного исполнения hooks. Но **проверяемое требование нулевых записей вне указанного scope не выполнено**. Scope gate FAIL, задним числом не ослаблен.

## Производительность / ресурсы

| 40 операций на ветку | A Git+symlink | B TeamAI CLI |
| --- | ---: | ---: |
| wall p50 | 16.050 ms | 753.773 ms |
| wall p95 nearest-rank | 17.936 ms | 824.895 ms |
| wall mean | 14.933 ms | 758.231 ms |
| child CPU p50 | 16.101 ms | 869.504 ms |
| child CPU p95 | 17.987 ms | 952.300 ms |
| wall min/max | 9.349 / 18.348 ms | 697.523 / 891.833 ms |
| minimal-home write scope | PASS | **FAIL** |

Разница median wall ~47× **только в этом feature-unequal тесте**. B включает node startup, provider logic, policy distribution, A — несколько дешёвых Git operations/symlink. Нельзя приписать разницу только адаптеру Team Context. Child block IO counters равны 0 по kernel accounting/tmpfs и **не являются доказательством отсутствия IO**. `ru_maxrss=144992 KiB` — кумулятивный максимум дочерних процессов в процессе измерения, **не сравнимый per-arm RSS**, p95 memory не измерен. GPU/VRAM N/A, model calls 0, tokens/cost N/A, сетевой трафик в A/B 0 (только local Git); нет production workload, human labor, inference, full feature parity, randomized inter-seed workload.

[Полный машинный JSON: 40×2 observations, seeds, timing, 35 путей](../../data/results/tencent-teamai-cli/2026-11-06-distribution-ab.json). Пароли/секреты/пользовательские файлы отсутствуют.

## Research → проекты и решение

| Источник | Target ID | Решение | Ограничение / следующий тест |
| --- | --- | --- | --- |
| BK-002 TeamAI | `dsh-team-context` | `BOUNDED_CLI_CONTRACT_PASS / SCOPE_GATE_FAIL` | Source and E2E confirm schema/governance; нужен явный allowlist / opt-in к клиентским путям и тест zero unauthorized writes на точном конфиге |
| BK-002 TeamAI | `agent-skills` | `DOCUMENTED_CANDIDATE / NO_MEASURED_ADVANTAGE` | Оценить 2-хостовый deployment, local-wins override, rollback, hook injection, операционную стоимость против существующего symlink+Git |
| BK-002 TeamAI | `teamai-cli` | `LOCAL_PORT_TESTED / PUBLIC_UPSTREAM_NOT_REBASED` | Опубликовать проверяемый SHA после peer review, отдельно разрешить merge conflicts и оценить совместимость версий без потери Team Context и без неожиданных writes |

**Исследовательское решение:** Telegram BK-002 остаётся `разобран`, отдельный offline эксперимент — `FUNCTIONAL_PASS_SCOPE_GATE_FAIL`. Никаких integration changes, LLM улучшений или security certification не утверждается. Перед повышением приоритета требуется согласование точного tool scope, allowlist на file writes, reproducible public pin и отдельная оценка реальной пользы. P0 исправления CVE-2026-82533 в `dsh-runtime` остаётся без изменений.
