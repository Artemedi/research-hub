import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

export function cardBodyHash(text) {
  const body = text.replace(/\r\n/g, '\n').replace(/^\[Структурированная запись и связи\]\([^\n]*\)\n\n?/gm, '').trim();
  return crypto.createHash('sha256').update(body).digest('hex');
}

export function isDocumentedTarget(lines, index, projectId) {
  if (!lines[index]?.trim().startsWith('|')) return null;
  const cells = line => line.trim().split(/(?<!\\)\|/).slice(1, -1).map(c => c.trim());
  let start = index;
  while (start > 0 && lines[start - 1].trim().startsWith('|')) start--;
  if (!lines[start + 1]?.includes('---')) return false;
  const header = cells(lines[start]), row = cells(lines[index]);
  const targetColumns = header.map((h, i) => /проек|целев|карточк|project|target|shortlist|кандидат/i.test(h) && !/причин|почему|обоснован|огранич|следующ|evidence|reason|limitation/i.test(h) ? i : -1).filter(i => i >= 0);
  const escaped = projectId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const mentions = new RegExp('(?:^|[^A-Za-z0-9_-])' + escaped + '(?:$|[^A-Za-z0-9_-])');
  return targetColumns.some(i => mentions.test(row[i] ?? ''));
}

export function validateEntities(root, m) {
  const fail = message => assert.fail('Entity model: ' + message);
  const require = (value, message) => { if (!value) fail(message); };
  const text = v => typeof v === 'string' && v.trim().length > 0;
  const local = p => text(p) && !p.includes('\\') && !p.startsWith('/') && !p.startsWith('../') && path.posix.normalize(p) === p && fs.existsSync(path.join(root, p));
  const url = s => { try { return new URL(s).protocol === 'https:'; } catch { return false; } };
  const date = s => /^\d{4}-\d{2}-\d{2}$/.test(s) && new Date(s).toISOString().slice(0, 10) === s;
  require([1, 2].includes(m.schema_version) && ['PILOT', 'NORMALIZED'].includes(m.coverage), 'unsupported schema/coverage');
  require(Array.isArray(m.legacy_studies), 'explicit legacy study allowlist required');
  if (m.coverage === 'NORMALIZED') require(m.legacy_studies.length === 0, 'normalized catalog cannot retain legacy studies');
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
    require(['paper', 'engineering', 'video', 'technical_disclosure'].includes(s.kind) && ['MIGRATED', 'PARTIAL', 'NOT_MIGRATED', 'NO_DOCUMENTED_ASSESSMENT'].includes(s.fit_coverage), s.id + ': bad kind/coverage');
    require(local(s.card) && url(s.primary_url), s.id + ': missing card/primary URL');
    require(fs.readFileSync(path.join(root, s.card), 'utf8').includes(`../catalog/studies/${s.id}.md`), s.id + ': card lacks structured record link');
    if (m.schema_version === 2 || s.card_body_sha256) require(s.card_body_sha256 === cardBodyHash(fs.readFileSync(path.join(root, s.card), 'utf8')), s.id + ': card body hash mismatch');
    if (s.fit_summary) {
      const summary = s.fit_summary;
      require(['NO_CURRENT_TARGET', 'UNKNOWN'].includes(summary.status) && local(summary.document), s.id + ': invalid fit summary');
      const lines = fs.readFileSync(path.join(root, summary.document), 'utf8').replace(/\r\n/g, '\n').split('\n');
      require(Number.isInteger(summary.line) && lines[summary.line - 1] === summary.excerpt && summary.excerpt.includes(summary.status), s.id + ': ungrounded fit summary');
    }
    if (m.schema_version === 2) {
      require(Array.isArray(s.linked_materials) && new Set(s.linked_materials).size === s.linked_materials.length, s.id + ': invalid linked materials');
      const source = fs.readFileSync(path.join(root, s.card), 'utf8');
      const links = [...source.matchAll(/\]\(([^\s)]+)\)/g)].map(x => x[1].split('#')[0]).filter(p => p && !/^https?:/.test(p)).map(p => path.posix.normalize(path.posix.join(path.posix.dirname(s.card), p)));
      for (const p of s.linked_materials) require(local(p) && links.includes(p), s.id + ': material not linked by source card');
    }
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
    require(['FULL_TEXT_REVIEWED', 'FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED', 'FULL_PRIMARY_TECHNICAL_DISCLOSURE_READ', 'HISTORICAL_REVIEW_RECORDED', 'PARTIAL_SOURCE_REVIEW', 'FULL_TEXT_UNAVAILABLE', 'BOUNDED_CODE_REVIEW', 'UNASSESSED'].includes(r.source_coverage), r.id + ': unknown source coverage');
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
    require(['SYNTHETIC', 'ISOLATED_INTEGRATION'].includes(e.environment) && ['PASS', 'FAIL', 'OBSERVED', 'BLOCKED', 'NOT_RUN'].includes(e.result), e.id + ': invalid environment/result');
    for (const id of e.study_ids) { ref('studies', id); require(r.study_ids.includes(id), e.id + ': study outside review'); }
    for (const p of e.artifacts) require(local(p), e.id + ': missing artifact');
  }
  for (const p of m.projects) {
    strings(p, ['title', 'registry_revision', 'registry_card_url']);
    require(/^[a-f0-9]{40}$/.test(p.registry_revision) && p.registry_card_url.startsWith(`https://github.com/Artemedi/project-registry/blob/${p.registry_revision}/projects/`) && p.registry_card_url.endsWith('/PROJECT.md'), p.id + ': registry provenance required');
  }
  const decisions = ['PROFILE_CANDIDATE_NOT_VALIDATED', 'CONDITIONAL_NEEDS_EVIDENCE', 'NO_CONFIRMED_FIT', 'RESEARCH_CANDIDATE_TARGET_NOT_MEASURED', 'ARCHITECTURAL_REFERENCE_CANDIDATE', 'DOCUMENTED_CANDIDATE', 'DOCUMENTED_NO_FIT', 'DEFERRED', 'NO_CURRENT_FIT', 'REFERENCE_NO_TARGET', 'SHORTLIST', 'CONTROL_PLANE_REFERENCE', 'NEEDS_EVIDENCE', 'CONDITIONAL_NEEDS_SOURCE_CODE'];
  const imports = new Map();
  for (const a of m.assessments) {
    ref('studies', a.study_id); ref('projects', a.project_id);
    const r = ref('reviews', a.review_id);
    require(r.study_ids.includes(a.study_id) && date(a.date), a.id + ': review/date mismatch');
    strings(a, ['evidence', 'reason', 'limitations']);
    require(decisions.includes(a.decision), a.id + ': unknown decision');
    require(text(a.next_test) || (a.next_test === null && text(a.next_test_reason)), a.id + ': missing next test/reason');
    if (a.source_document) {
      require(!a.source_matrix && local(a.source_document), a.id + ': invalid document provenance');
      require(a.project_revision === null && a.project_card_sha256 === null && text(a.unknown_reason), a.id + ': documentary assessment must not claim verified project source');
      require(['DOCUMENTED_CANDIDATE', 'DOCUMENTED_NO_FIT', 'DEFERRED'].includes(a.decision), a.id + ': invalid documentary decision');
      strings(a, ['source_excerpt', 'source_decision']);
      const lines = fs.readFileSync(path.join(root, a.source_document), 'utf8').replace(/\r\n/g, '\n').split('\n');
      require(Number.isInteger(a.source_line) && a.source_line > 0 && lines[a.source_line - 1] === a.source_excerpt, a.id + ': documentary quote/line mismatch');
      const escaped = a.project_id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const projectPattern = new RegExp('(?:^|[^A-Za-z0-9_-])' + escaped + '(?:$|[^A-Za-z0-9_-])');
      if (!projectPattern.test(a.source_excerpt)) {
        let heading = a.source_line - 2;
        while (heading >= 0 && !/^#{1,6} /.test(lines[heading])) heading--;
        require(heading >= 0 && a.source_context_line === heading + 1 && a.source_context === lines[heading] && projectPattern.test(a.source_context), a.id + ': source does not mention project');
      }
      require(isDocumentedTarget(lines, a.source_line - 1, a.project_id) !== false, a.id + ': project is not in the target column');
      require(a.source_excerpt.includes(a.source_decision) && a.source_excerpt.includes(a.evidence), a.id + ': documentary evidence not verbatim');
      const studyCard = ref('studies', a.study_id).card;
      const rowStudies = [...a.source_excerpt.matchAll(/studies\/([A-Za-z0-9_-]+\.md)/g)].map(x => x[1]);
      if (rowStudies.length) require(rowStudies.includes(path.posix.basename(studyCard)), a.id + ': documentary row belongs to another study');
      if (a.supersedes) { const old = ref('assessments', a.supersedes); require(old.study_id === a.study_id && old.project_id === a.project_id && old.date <= a.date, a.id + ': incompatible supersession'); }
      continue;
    }
    strings(a, ['project_revision', 'project_card_sha256']);
    require(local(a.source_matrix), a.id + ': missing original matrix');
    const source = JSON.parse(fs.readFileSync(path.join(root, a.source_matrix), 'utf8'));
    require(source.card_count === source.projects.length && new Set(source.projects.map(p => p.project_id)).size === source.projects.length, a.id + ': invalid original matrix count/IDs');
    const original = source.projects.find(p => p.project_id === a.project_id);
    const group = JSON.stringify([a.study_id, a.review_id, a.source_matrix]);
    if (!imports.has(group)) imports.set(group, { ids: [], expected: source.projects.map(p => p.project_id) });
    imports.get(group).ids.push(a.project_id);
    require(original && original.decision === a.decision && original.evidence === a.evidence && original.reason_ru === a.reason && original.card_sha256 === a.project_card_sha256 && (source.registry_head ?? source.registry_sha) === a.project_revision && source.report === r.document, a.id + ': assessment differs from original evidence');
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
  for (const s of m.studies) {
    const rows = m.assessments.filter(a => a.study_id === s.id);
    require((s.fit_coverage === 'MIGRATED' && rows.some(a => a.source_matrix)) || (s.fit_coverage === 'PARTIAL' && rows.length > 0) || (['NOT_MIGRATED', 'NO_DOCUMENTED_ASSESSMENT'].includes(s.fit_coverage) && rows.length === 0), s.id + ': inaccurate fit coverage');
  }
  for (const r of m.relations) {
    ref('studies', r.from); ref('studies', r.to); ref('reviews', r.review_id); strings(r, ['reason']);
    require(r.from !== r.to && ['extends', 'compares', 'uses', 'related'].includes(r.type), r.id + ': invalid relation');
  }
  return m;
}

export function entityPages(m) {
  const pages = new Map(), escape = s => String(s).replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/`/g, '').replace(/\*\*/g, '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');
  const review = id => m.reviews.find(r => r.id === id);
  const assessment = id => m.assessments.find(a => a.id === id);
  const current = m.current_assessments.map(p => assessment(p.assessment_id));
  const rows = items => items.map(a => `| [${escape(a.study_id)}](../catalog/studies/${a.study_id}.md) | ${escape(a.decision)} | ${escape(a.evidence)} | ${escape(a.reason)} | [Обзор](../${review(a.review_id).document}) · [Основание](../${a.source_document ?? a.source_matrix ?? review(a.review_id).document}) |`).join('\n');
  for (const s of m.studies) {
    const reviews = m.reviews.filter(r => r.study_ids.includes(s.id));
    const fits = current.filter(a => a.study_id === s.id);
    pages.set(`catalog/studies/${s.id}.md`, `# ${escape(s.title)}\n\nСтруктурированная запись источника. [Карточка](../../${s.card}) · [Первоисточник](${s.primary_url})\n\n## Текущий обзор\n\n[${s.current_review_id}](../../${review(s.current_review_id).document}) — ${review(s.current_review_id).source_coverage}. ${escape(review(s.current_review_id).limitations)}\n\n## Версии и история обзоров\n\n${reviews.map(r => `- [${r.id}](../../${r.document}), ${r.date}; ${r.source_coverage}; заменяет: ${r.supersedes ?? 'нет'}. Версии: ${r.version_ids.map(id => {const v=m.versions.find(v=>v.id===id);return `[${v.ref ?? 'не установлена'}](${v.url})`;}).join(', ')}.`).join('\n')}\n\n## Применимость к проектам\n\n${s.fit_coverage === 'MIGRATED' ? 'Полная исходная JSON-матрица перенесена с её историей и ограничениями.' : s.fit_coverage === 'PARTIAL' ? 'Перенесены явные документальные оценки. Это частичный охват проектов, не проверенный integration seam и не измеренная польза.' : 'При структурном переносе нет отдельной проектной оценки. Это не NO_FIT и не отсутствие прежнего анализа; см. исходную карточку.'}\n\n${fits.map(a => `- [${escape(a.project_id)}](../../projects/${a.project_id}.md): ${escape(a.decision)}; ${escape(a.evidence)}. ${escape(a.reason)} Ограничения: ${escape(a.limitations)} Следующий тест: ${escape(a.next_test ?? a.next_test_reason)} [Основание](../../${a.source_document ?? a.source_matrix ?? review(a.review_id).document}); предыдущая оценка: ${a.supersedes ?? 'нет'}.`).join('\n')}\n\n## Эксперименты\n\n${m.experiments.filter(e=>e.study_ids.includes(s.id)).map(e=>`- ${e.id}: ${e.environment} / ${e.result}. ${escape(e.scope)} ${escape(e.limitations)} ${e.artifacts.map(p=>`[Артефакт](../../${p})`).join(' · ')}`).join('\n') || 'В модели нет отдельной записи эксперимента. Фактический охват и ссылки сохранены в исходной карточке и обзорах; это не утверждение NOT_RUN.'}`);
  }
  for (const p of m.projects) {
    const fits = current.filter(a => a.project_id === p.id), deferred = ['NO_CONFIRMED_FIT', 'NO_CURRENT_FIT', 'REFERENCE_NO_TARGET', 'DOCUMENTED_NO_FIT', 'DEFERRED', 'NEEDS_EVIDENCE'], candidates = fits.filter(a => !deferred.includes(a.decision)), other = fits.filter(a => deferred.includes(a.decision));
    pages.set(`projects/${p.id}.md`, `# ${escape(p.title)}\n\n[Каноническая карточка проекта](${p.registry_card_url}); ревизия ${p.registry_revision}. Публичная проекция без закрытого кода и текстов проекта.\n\n**Охват:** показаны только перенесённые оценки, а не все подходящие исследования портфеля. Наличие кандидата не означает измеренную пользу или разрешение внедрения.\n\n## Исследовательские кандидаты\n\n| Источник | Решение | Доказательность | Основание | Проверка |\n| --- | --- | --- | --- | --- |\n${rows(candidates)}\n\n## Соответствие не подтверждено или применение отложено\n\n| Источник | Решение | Доказательность | Основание | Проверка |\n| --- | --- | --- | --- | --- |\n${rows(other)}\n\nОграничения, следующий тест и история оценки доступны в структурированной записи источника. Отсутствие связи не означает отрицательную оценку; полный портфель заново не оценивался.`);
  }
  pages.set('projects/README.md', `# Проекты и исследования\n\nОбратный каталог: ${m.projects.length} проектов из зафиксированного реестра, оценки перенесены для ${new Set(m.current_assessments.map(a => a.study_id)).size} источников. Это неполный список исследований для каждого проекта. Обе стороны связи генерируются из одних current_assessments.\n\n${m.projects.map(p=>`- [${escape(p.title)}](${p.id}.md)`).join('\n')}`);
  pages.set('catalog/studies/README.md', `# Структурированные исследования\n\n${m.studies.length} источников. [Полный файловый каталог](../../studies/INDEX.md) содержит исходные аналитические карточки. [Проекты](../../projects/README.md).\n\n${m.studies.map(s=>`- [${escape(s.title)}](${s.id}.md); project fit: ${s.fit_coverage}.`).join('\n')}`);
  for (const s of m.studies) {
    const related = m.relations.filter(r => r.from === s.id || r.to === s.id);
    if (!related.length) continue;
    const file = `catalog/studies/${s.id}.md`;
    pages.set(file, pages.get(file) + '\n\n## Связанные исследования\n\n' + related.map(r => {
      const other = r.from === s.id ? r.to : r.from;
      return `- [${escape(other)}](${other}.md): ${r.type} (${r.from} → ${r.to}). ${escape(r.reason)} [Основание](../../${review(r.review_id).document}).`;
    }).join('\n'));
  }
  for (const s of m.studies) {
    const file = 'catalog/studies/' + s.id + '.md';
    const note = s.fit_summary ? '\n\n## Оговорка исходного источника\n\n' + escape(s.fit_summary.status) + ': ' + escape(s.fit_summary.excerpt) + ' [Источник](../../' + s.fit_summary.document + ').' : '';
    const links = (s.linked_materials ?? []).map(p => '- [' + p + '](../../' + p + ')').join('\n');
    pages.set(file, pages.get(file) + note + '\n\n## Ссылки из исходной карточки\n\nЭто ссылки на материалы, а не автоматическое подтверждение связи методов или собственного эксперимента.\n\n' + links);
  }
  return pages;
}
