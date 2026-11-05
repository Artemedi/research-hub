import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

export function validateEntities(root, m) {
  const fail = message => assert.fail('Entity model: ' + message);
  const require = (value, message) => { if (!value) fail(message); };
  const text = v => typeof v === 'string' && v.trim().length > 0;
  const local = p => text(p) && !p.includes('\\') && !p.startsWith('/') && !p.startsWith('../') && path.posix.normalize(p) === p && fs.existsSync(path.join(root, p));
  const url = s => { try { return new URL(s).protocol === 'https:'; } catch { return false; } };
  const date = s => /^\d{4}-\d{2}-\d{2}$/.test(s) && new Date(s).toISOString().slice(0, 10) === s;
  require(m.schema_version === 1 && m.coverage === 'PILOT', 'unsupported schema/coverage');
  require(Array.isArray(m.legacy_studies), 'explicit legacy study allowlist required');
  const maps = {};
  for (const name of ['studies', 'versions', 'reviews', 'experiments', 'projects', 'assessments', 'relations']) {
    require(Array.isArray(m[name]), name + ' must be an array');
    maps[name] = new Map();
    for (const row of m[name]) {
      require(/^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(row.id), name + ': invalid id');
      require(!maps[name].has(row.id), name + ': duplicate id'); maps[name].set(row.id, row);
    }
  }
  const ref = (kind, id) => { require(maps[kind].has(id), `unknown ${kind} id: ${id}`); return maps[kind].get(id); };
  const strings = (row, keys) => keys.forEach(k => require(text(row[k]), `${row.id}: missing ${k}`));
  const list = (value, label) => require(Array.isArray(value) && value.length > 0 && new Set(value).size === value.length, label + ': empty/duplicate list');
  for (const s of m.studies) {
    strings(s, ['title', 'kind', 'card', 'primary_url', 'current_review_id', 'fit_coverage']);
    require(['paper', 'engineering', 'video'].includes(s.kind) && ['MIGRATED', 'NOT_MIGRATED'].includes(s.fit_coverage), s.id + ': bad kind/coverage');
    require(local(s.card) && url(s.primary_url), s.id + ': missing card/primary URL');
    require(fs.readFileSync(path.join(root, s.card), 'utf8').includes(`../catalog/studies/${s.id}.md`), s.id + ': card lacks structured record link');
    require(ref('reviews', s.current_review_id).study_ids.includes(s.id), s.id + ': current review does not cover study');
  }
  require(new Set(m.studies.map(s => s.card)).size === m.studies.length, 'duplicate study card');
  const configured = JSON.parse(fs.readFileSync(path.join(root, 'catalog/structure.json'), 'utf8')).studies;
  const accounted = [...m.legacy_studies, ...m.studies.map(s => s.card)];
  require(new Set(accounted).size === accounted.length && accounted.length === configured.length && configured.every(p => accounted.includes(p)), 'study must be modeled or explicitly legacy');
  for (const s of m.studies) require(!m.reviews.some(r => r.supersedes === s.current_review_id), s.id + ': current review is superseded');
  for (const v of m.versions) {
    ref('studies', v.study_id); require(url(v.url), v.id + ': missing version URL');
    require(text(v.ref) || (v.ref === null && text(v.unknown_reason)), v.id + ': missing version/unknown reason');
  }
  for (const r of m.reviews) {
    list(r.study_ids, r.id); list(r.version_ids, r.id); strings(r, ['source_coverage', 'limitations']);
    require(['FULL_TEXT_REVIEWED', 'PARTIAL_SOURCE_REVIEW', 'FULL_TEXT_UNAVAILABLE', 'BOUNDED_CODE_REVIEW'].includes(r.source_coverage), r.id + ': unknown source coverage');
    require(date(r.date) && local(r.document), r.id + ': missing date/document');
    for (const id of r.study_ids) { ref('studies', id); require(r.version_ids.some(v => ref('versions', v).study_id === id), r.id + ': missing source version'); }
    for (const id of r.version_ids) require(r.study_ids.includes(ref('versions', id).study_id), r.id + ': version outside review');
    if (r.supersedes) {
      const old = ref('reviews', r.supersedes);
      require(old.date <= r.date && old.study_ids.every(id => r.study_ids.includes(id)), r.id + ': incompatible supersession');
    }
  }
  for (const e of m.experiments) {
    const r = ref('reviews', e.review_id); list(e.study_ids, e.id); list(e.artifacts, e.id); strings(e, ['scope', 'limitations']);
    require(['SYNTHETIC', 'ISOLATED_INTEGRATION'].includes(e.environment) && ['PASS', 'FAIL', 'BLOCKED', 'NOT_RUN'].includes(e.result), e.id + ': invalid environment/result');
    for (const id of e.study_ids) { ref('studies', id); require(r.study_ids.includes(id), e.id + ': study outside review'); }
    for (const p of e.artifacts) require(local(p), e.id + ': missing artifact');
  }
  for (const p of m.projects) {
    strings(p, ['title', 'registry_revision', 'registry_card_url']);
    require(/^[a-f0-9]{40}$/.test(p.registry_revision) && p.registry_card_url.startsWith(`https://github.com/Artemedi/project-registry/blob/${p.registry_revision}/projects/`) && p.registry_card_url.endsWith('/PROJECT.md'), p.id + ': registry provenance required');
  }
  const decisions = ['PROFILE_CANDIDATE_NOT_VALIDATED', 'CONDITIONAL_NEEDS_EVIDENCE', 'NO_CONFIRMED_FIT', 'RESEARCH_CANDIDATE_TARGET_NOT_MEASURED'];
  const imports = new Map();
  for (const a of m.assessments) {
    ref('studies', a.study_id); ref('projects', a.project_id);
    const r = ref('reviews', a.review_id);
    require(r.study_ids.includes(a.study_id) && date(a.date), a.id + ': review/date mismatch');
    strings(a, ['evidence', 'reason', 'limitations', 'project_revision', 'project_card_sha256']);
    require(decisions.includes(a.decision), a.id + ': unknown decision');
    require(text(a.next_test) || (a.next_test === null && text(a.next_test_reason)), a.id + ': missing next test/reason');
    require(local(a.source_matrix), a.id + ': missing original matrix');
    const source = JSON.parse(fs.readFileSync(path.join(root, a.source_matrix), 'utf8'));
    require(source.card_count === source.projects.length && new Set(source.projects.map(p => p.project_id)).size === source.projects.length, a.id + ': invalid original matrix count/IDs');
    const original = source.projects.find(p => p.project_id === a.project_id);
    const group = JSON.stringify([a.study_id, a.review_id, a.source_matrix]);
    if (!imports.has(group)) imports.set(group, { ids: [], expected: source.projects.map(p => p.project_id) });
    imports.get(group).ids.push(a.project_id);
    require(original && original.decision === a.decision && original.evidence === a.evidence && original.reason_ru === a.reason && original.card_sha256 === a.project_card_sha256 && source.registry_head === a.project_revision && source.report === r.document, a.id + ': assessment differs from original evidence');
    if (a.supersedes) { const old = ref('assessments', a.supersedes); require(old.study_id === a.study_id && old.project_id === a.project_id && old.date <= a.date, a.id + ': incompatible supersession'); }
  }
  for (const [group, { ids, expected }] of imports) require(ids.length === expected.length && new Set(ids).size === ids.length && expected.every(id => ids.includes(id)), group + ': incomplete/duplicate matrix import');
  for (const p of m.projects) {
    const provenance = m.assessments.find(a => a.project_id === p.id && a.project_revision === p.registry_revision);
    if (provenance) {
      const matrix = JSON.parse(fs.readFileSync(path.join(root, provenance.source_matrix), 'utf8'));
      const row = matrix.projects.find(r => r.project_id === p.id);
      require(p.registry_card_url === `https://github.com/Artemedi/project-registry/blob/${p.registry_revision}/${row.card_path}`, p.id + ': project card identity mismatch');
    }
  }
  for (const kind of ['reviews', 'assessments']) for (const row of m[kind]) {
    const visited = new Set([row.id]); let next = row.supersedes;
    while (next) { require(!visited.has(next), row.id + ': supersession cycle'); visited.add(next); next = ref(kind, next).supersedes; }
  }
  require(Array.isArray(m.current_assessments), 'current assessments missing');
  const current = new Set();
  for (const p of m.current_assessments) {
    const a = ref('assessments', p.assessment_id), key = p.study_id + '/' + p.project_id;
    require(!current.has(key) && a.study_id === p.study_id && a.project_id === p.project_id, 'invalid/duplicate current assessment');
    require(!m.assessments.some(x => x.supersedes === a.id), a.id + ': current points to superseded assessment'); current.add(key);
  }
  for (const s of m.studies) for (const a of m.assessments.filter(a => a.study_id === s.id)) require(current.has(s.id + '/' + a.project_id), a.id + ': current pointer missing');
  for (const s of m.studies) require((s.fit_coverage === 'MIGRATED') === m.assessments.some(a => a.study_id === s.id), s.id + ': inaccurate fit coverage');
  for (const r of m.relations) {
    ref('studies', r.from); ref('studies', r.to); ref('reviews', r.review_id); strings(r, ['reason']);
    require(r.from !== r.to && ['extends', 'compares', 'uses', 'related'].includes(r.type), r.id + ': invalid relation');
  }
  return m;
}

export function entityPages(m) {
  const pages = new Map(), escape = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');
  const review = id => m.reviews.find(r => r.id === id);
  const assessment = id => m.assessments.find(a => a.id === id);
  const current = m.current_assessments.map(p => assessment(p.assessment_id));
  const rows = items => items.map(a => `| [${escape(a.study_id)}](../catalog/studies/${a.study_id}.md) | ${escape(a.decision)} | ${escape(a.evidence)} | ${escape(a.reason)} | [Обзор](../${review(a.review_id).document}) |`).join('\n');
  for (const s of m.studies) {
    const reviews = m.reviews.filter(r => r.study_ids.includes(s.id));
    const fits = current.filter(a => a.study_id === s.id);
    pages.set(`catalog/studies/${s.id}.md`, `# ${escape(s.title)}\n\nПилот единой модели. [Карточка](../../${s.card}) · [Первоисточник](${s.primary_url})\n\n## Текущий обзор\n\n[${s.current_review_id}](../../${review(s.current_review_id).document}) — ${review(s.current_review_id).source_coverage}. ${escape(review(s.current_review_id).limitations)}\n\n## Версии и история обзоров\n\n${reviews.map(r => `- [${r.id}](../../${r.document}), ${r.date}; ${r.source_coverage}; заменяет: ${r.supersedes ?? 'нет'}. Версии: ${r.version_ids.map(id => {const v=m.versions.find(v=>v.id===id);return `[${v.ref ?? 'не установлена'}](${v.url})`;}).join(', ')}.`).join('\n')}\n\n## Применимость к проектам\n\n${s.fit_coverage === 'NOT_MIGRATED' ? 'Связи ещё не перенесены в единую модель. Это не NO_FIT и не отсутствие прежнего анализа; см. исходную карточку.' : 'Полная оценка перенесена из матриц. NO_CONFIRMED_FIT означает отсутствие подтверждённого соответствия, а не доказанную бесполезность.'}\n\n${fits.map(a => `- [${escape(a.project_id)}](../../projects/${a.project_id}.md): ${escape(a.decision)}; ${escape(a.evidence)}. ${escape(a.reason)} Ограничения: ${escape(a.limitations)} Следующий тест: ${escape(a.next_test ?? a.next_test_reason)} [Основание](../../${review(a.review_id).document}); предыдущая оценка: ${a.supersedes ?? 'нет'}.`).join('\n')}\n\n## Эксперименты\n\n${m.experiments.filter(e=>e.study_ids.includes(s.id)).map(e=>`- ${e.id}: ${e.environment} / ${e.result}. ${escape(e.scope)} ${escape(e.limitations)} ${e.artifacts.map(p=>`[Артефакт](../../${p})`).join(' · ')}`).join('\n') || 'Отдельные записи экспериментов в пилот ещё не перенесены; см. обзоры. Это не утверждение NOT_RUN.'}`);
  }
  for (const p of m.projects) {
    const fits = current.filter(a => a.project_id === p.id), candidates = fits.filter(a => a.decision !== 'NO_CONFIRMED_FIT'), other = fits.filter(a => a.decision === 'NO_CONFIRMED_FIT');
    pages.set(`projects/${p.id}.md`, `# ${escape(p.title)}\n\n[Каноническая карточка проекта](${p.registry_card_url}); ревизия ${p.registry_revision}. Публичная проекция без закрытого кода и текстов проекта.\n\n**Пилот:** показаны только перенесённые оценки, а не все подходящие исследования портфеля. Наличие кандидата не означает измеренную пользу или разрешение внедрения.\n\n## Исследовательские кандидаты\n\n| Источник | Решение | Доказательность | Основание | Проверка |\n| --- | --- | --- | --- | --- |\n${rows(candidates)}\n\n## Соответствие не подтверждено\n\n| Источник | Решение | Доказательность | Основание | Проверка |\n| --- | --- | --- | --- | --- |\n${rows(other)}\n\nОграничения, следующий тест и история оценки доступны в структурированной записи источника. Остальные связи ещё не мигрированы.`);
  }
  pages.set('projects/README.md', `# Проекты и исследования\n\nПилот обратного каталога: ${m.projects.length} проектов из зафиксированного реестра, но оценки перенесены только для REA. Это неполный список исследований для каждого проекта. Обе стороны связи генерируются из одних current_assessments.\n\n${m.projects.map(p=>`- [${escape(p.title)}](${p.id}.md)`).join('\n')}`);
  pages.set('catalog/studies/README.md', `# Структурированные исследования — пилот\n\n${m.studies.length} источников. [Полный файловый каталог](../../studies/INDEX.md) содержит и ещё не мигрированные записи. [Проекты](../../projects/README.md).\n\n${m.studies.map(s=>`- [${escape(s.title)}](${s.id}.md); project fit: ${s.fit_coverage}.`).join('\n')}`);
  for (const s of m.studies) {
    const related = m.relations.filter(r => r.from === s.id || r.to === s.id);
    if (!related.length) continue;
    const file = `catalog/studies/${s.id}.md`;
    pages.set(file, pages.get(file) + '\n\n## Связанные исследования\n\n' + related.map(r => {
      const other = r.from === s.id ? r.to : r.from;
      return `- [${escape(other)}](${other}.md): ${r.type} (${r.from} → ${r.to}). ${escape(r.reason)} [Основание](../../${review(r.review_id).document}).`;
    }).join('\n'));
  }
  return pages;
}
