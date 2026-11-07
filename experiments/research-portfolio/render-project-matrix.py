#!/usr/bin/env python3
"""Render the explicitly documented existing 83x45 research-to-project coverage.

No inference of new project FIT or NO_FIT from absent assessments.
No access to private project descriptions. Deterministic read-only renderer
other than the explicitly requested output Markdown path.
"""
import argparse,json,pathlib,collections
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--coverage",type=pathlib.Path,required=True)
 ap.add_argument("--out",type=pathlib.Path,required=True)
 args=ap.parse_args()
 cover=json.loads(args.coverage.read_text())
 assert cover["counts"]["studies"]==83 and cover["counts"]["projects"]==45
 assert cover["counts"]["pairs"]==3735
 assert len(cover["studies"])==83
 assert cover["counts"]["documented_current_assessments"]==376
 assert cover["counts"]["no_documented_decision_pairs"]==3359
 entities=json.loads((pathlib.Path(__file__).resolve().parents[2]/"catalog/entities.json").read_text())
 cards={entry["id"]:entry["card"] for entry in entities["studies"]}
 rows=[
 "# Research-to-project — полный аудит документированных связей, 07.11.2026",
 "",
 "Снимки: §research-hub@3180d9c46914f2f54d2a21e642b7ec3efffa2b99§ и приватный §project-registry@838b86a28fcaa3440eeddbe147b6188e0d177963§.",
 "",
 "**Правило:** ниже только прежние явно зарегистрированные candidates/assessments, **не** новый научный project fit. Отсутствие решения (§NOT_EVALUATED§) не означает §NO_FIT§, и наличие кандидата не означает выполненный A/B или разрешение на внедрение.",
 "",
 "Контракт анализа — [исследовательская политика](../../RESEARCH_POLICY.md), полный обзор — [review](review.md), [глобальный оркестратор](../../docs/research-orchestrator.md). [Полная машинная матрица 3 735 записей](../../data/results/research-portfolio/2026-11-07-coverage.json) включает все 45 project ID для каждого источника и актуальный assessment_id при его наличии.",
 "",
 "## Фактическое покрытие",
 "",
 "| Показатель | Количество |",
 "| --- | ---: |",
 "| Канонических исследований | **83** |",
 "| Проектов в приватной глобальной карте | **45** |",
 "| Пар study×project | **3 735** |",
 "| Текущих явных оценок | **376** |",
 "| §NOT_EVALUATED§ | **3 359** |",
 "| Исследований без единой текущей project assessment | **3** |",
 "",
 "Три нулевых кейса: §cera-moa§, §kvtether§, §random-attention§. Их нельзя автоматически записывать как неподходящие ни к одному из 45 проектов; требуется source-specific broad triage.",
 "",
 "## Поимённый перечень всех источников",
 "",
 "| Источник | Текущая проверка источника | Существующий shortlist: до 3 project ID, **не approval** | Ограничения / минимальный следующий gate |",
 "| --- | --- | --- | --- |"
 ]
 def gate(study):
  kind=study["kind"];access=study["automated_source_access"];coverage=study["current_review_access_claim"]
  if study["documented_current_project_assessments"]==0:
   return "Нужна source-first оценка 45 profiles; нет документированного решения"
  if access in ("SOURCE_UNREACHABLE_OR_TOO_LARGE","SHORT_LANDING_NOT_FULL_TEXT_CONFIRMED","VIDEO_LANDING_ONLY_NO_TRANSCRIPT_VERIFIED"):
   return "Проверить полный легальный alternate/source или transcript; без него — BLOCKED"
  if access=="GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW":
   return "Проверить pinned source+tests, source seam и negative controls"
  if coverage in ("PARTIAL_SOURCE_REVIEW","BOUNDED_CODE_REVIEW","HISTORICAL_REVIEW_RECORDED"):
   return "Уточнить полный исходник/тест; независимый target A/B ещё не выполнен"
  if kind=="paper":return "Проверить методы/результаты/ограничения; target oracle/A-B отсутствует"
  return "Проектный эффект не измерен; удержать без автоматического внедрения"
 for study in sorted(cover["studies"],key=lambda x:x["study_id"]):
  sid=study["study_id"];present=study["documented_candidate_shortlist_not_new_fits"]
  # All existing recorded candidate shortlists, no semantic new matching.
  shortlist=", ".join("§"+item["project_id"]+"§" for item in present)
  if not shortlist:shortlist="**NO_DOCUMENTED_SHORTLIST**"
  rows.append(
   "| [§"+sid+"§](../../"+cards[sid]+") | "+
   "§"+study["automated_source_access"]+"§ / §"+str(study["current_review_access_claim"])+"§ | "+
   shortlist+" | "+gate(study)+" |"
  )
 rows.extend([
 "",
 "## Интерпретация",
 "",
 "- §NO_DOCUMENTED_SHORTLIST§ означает **нет сохранённого положительного shortlist**, а не отрицательное решение по всем 45 проектам.",
 "- Если источник частичный, статус code/head/source URL текущего audit не отменяет качественный предыдущий pinned review.",
 "- Для инженерных источников сначала читать актуальный source@SHA и tests; §GitHub HTTP 200§ подтверждает доступ, но не выполнение и безопасность.",
 "- Для клинического исследования §sequential-diagnosis-language-models§ доступна [полная легальная авторская PDF](https://erichorvitz.com/sequential_diagnosis_LM.pdf), несмотря на HTTP403 по DOI.",
 "- Внешний §developer-safe-dotnet-core§ документирован только author brief; без исходного кода любые утверждения об API и внедрении остаются §NEEDS_SOURCE_CODE§.",
 "- Публичная матрица не публикует содержимое частных PROJECT.md, токены или секреты. Исторические привязки не получают продвинутые статусы из этого скрининга.",
 "- Обновлять приватный registry backlink только при настоящем новом полном обзоре с доказанным profile match, не после автоматического HTTP-прохода.",
 "",
 "Итог: §EXPLICIT_ASSESSMENTS_PRESERVED / 83_SOURCES_SCREENED / 3359_PAIRS_NOT_EVALUATED / NO_NEW_PRODUCTION_APPROVAL§."
 ])
 output="\n".join(rows).replace("§",chr(96))+"\n"
 args.out.parent.mkdir(exist_ok=True,parents=True)
 args.out.write_text(output)
 assert output.count("| [")>=83
 print("MATRIX_RENDER_PASS",len(cover["studies"]),"studies",args.out,"lines",len(rows))
if __name__=="__main__":main()
