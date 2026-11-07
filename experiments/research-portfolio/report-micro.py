#!/usr/bin/env python3
"""Produce source-grounded 31-study public screening archive from micro-swarm logs.
Never promote screening to scientific review, replication, project FIT or deployment.
"""
import argparse,collections,json,pathlib,re,hashlib

def clean(x,n=230):
    return re.sub(r"\s+"," ",str(x or "")).strip()[:n].replace("|","/").replace(chr(96),"'")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--work",type=pathlib.Path,required=True)
    ap.add_argument("--repo",type=pathlib.Path,required=True)
    args=ap.parse_args()
    W=args.work;H=args.repo
    packs={p.stem:json.loads(p.read_text()) for p in (W/"swarm-packs").glob("*.json")}
    assert len(packs)==31
    run_path=W/"micro-swarm-results.json"
    run=json.loads(run_path.read_text()) if run_path.is_file() else {}
    byid={r["id"]:r for r in run.get("studies",[])}
    study_map={r["id"]:r for r in json.loads((H/"catalog/entities.json").read_text())["studies"]}
    rows=[]
    for sid,pack in sorted(packs.items()):
        src=pack["source_evidence"]
        response=byid.get(sid,{})
        result=response.get("answer") or {}
        anchors=[{"path":x["path"],"kind":x["type"],"sha256":x.get("full_file_sha256")}
                 for x in src.get("files",[])]
        sections=[{"heading":x.get("heading"),"section":x["section"],
                   "excerpt_sha256":x.get("anchor_sha256")}
                  for x in src.get("sections",[])]
        rows.append({
          "study_id":sid,"kind":pack["kind"],"url":pack["source_url"],
          "canonical_card":study_map[sid]["card"],
          "source_access_gate":src["status"],
          "pinned_revision":src.get("revision"),
          "document_text_sha256":src.get("full_text_sha256"),
          "file_anchors":anchors,"section_anchors":sections,
          "prior_review_access":pack["current_review_claim"],
          "documented_previous_shortlist_not_new_fits":pack["previous_shortlist"],
          "model_role":response.get("role"),
          "model_result":response.get("model_status","NOT_ATTEMPTED"),
          "model_response":result if response.get("model_status")=="SCHEMA_PASS" else None,
          "errors":[x["status"] for x in response.get("attempts",[]) if x["status"]!="SCHEMA_PASS"],
          "independent_source_claim_reviewed":False,
          "new_project_fit_approved":False,
          "author_experiment_reproduced":False,
          "production_approved":False
        })
    n=collections.Counter(x["model_result"] for x in rows)
    gates=collections.Counter(x["source_access_gate"] for x in rows)
    out={
     "date":"2026-11-07",
     "scope":"31 high-priority public-source research gap dossiers and ZCode micro-role screening",
     "first_party_source_access_provenance":True,
     "source_review_completed":False,"project_fit_new_approvals":0,
     "independent_lab_replications":0,"production_approvals":0,
     "logical_roles_scheduled":31,"physical_model_concurrency":1,
     "model_family":"ZCode GLM-5.3-Flash; user Start Plan",
     "source_counts":dict(gates),"model_status_counts":dict(n),
     "model_calls":run.get("calls"),"reported_model_tokens":run.get("reported_tokens"),
     "balance_remaining_deltas":run.get("balance_delta"),
     "model_run_complete":run.get("finished",False),
     "limitations":["Model given short excerpts only; neither analyst nor external reviewer can claim to read full paper",
       "Pinned public repository files not built or executed, no source seam verified",
       "Project candidates from old assessments are not re-approved",
       "No output is automatically a scientific fact, independent reproduction or production readiness",
       "Public archive excludes raw source excerpts, private project registry and credentials"],
     "studies":rows
    }
    target=H/"data/results/research-portfolio/2026-11-07-mass-swarm.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    lines=[
     "# Массовый разбор роя — 31 доказательный пробел",
     "",
     "Дата: 07.11.2026. Входные данные: [83 первоисточника](review.md),",
     "[глобальная матрица 83×45](project-fit.md) и [архитектура оркестратора](../../docs/research-orchestrator.md).",
     "",
     "Здесь 31 исследование проходило новый source-based screening: 19 pinned-code",
     "excerpts, 10 извлечённых текстов научных/технических публикаций, 1 короткая",
     "landing-page и 1 source repository без достоверного implementation excerpt.",
     "**Полный обзор, независимое воспроизведение и новые привязки к проектам не утверждаются.**",
     "",
     "## Подсчитанные результаты",
     "",
     "- Пакетов с исходными доказательствами: **31/31**.",
     "- Итоговые статусы модельных заданий: "+", ".join(clean(k)+": "+str(v) for k,v in sorted(n.items()))+".",
     "- Модельных вызовов: "+str(run.get("calls","пока не завершено"))+".",
     "- Учтённых моделью входных и выходных токенов: "+str(run.get("reported_tokens","пока не завершено"))+".",
     "- Списания по балансам: "+clean(run.get("balance_delta","пока не завершено"),380)+".",
     "- Научный ACCEPT по новому прохождению: **0**; project-fit APPROVED: **0**.",
     "",
     "## Все исследовательские задачи",
     "",
     "| Исследование | Материал | Статус микроагента | Доказательный вывод / следующий тест |",
     "| --- | --- | --- | --- |"
    ]
    for row in rows:
        sid=row["study_id"]
        response=row["model_response"] or {}
        claim=response.get("claim")
        next_test=response.get("next_test")
        msg=(clean(claim,165)+" / "+clean(next_test,155)) if claim else "Требуется полный независимый review исходника и минимальный A/B по указанной теме"
        ref="../../"+row["canonical_card"]
        lines.append("| ["+clean(sid,80)+"]("+ref+") | "+clean(row["source_access_gate"],75)+" | "+clean(row["model_result"],72)+" | "+msg+" |")
    lines.extend([
     "",
     "## Три источника без текущего project-assessment: отдельный профильный screening",
     "",
     "Для каждого ниже недостаточно одной тематической ассоциации. Предварительный shortlist",
     "**не становится доказанным FIT**, пока не прочитан конкретный source seam проекта и не измерено влияние.",
     "",
     "- **cera-moa**: кандидат 9router или dsh-runtime лишь при доступе к hidden-state/обучению",
     "  LoRA-специалистов. Простой прокси удалённых моделей не реализует данный метод.",
     "- **kvtether**: кандидат dsh-runtime / Harness лишь если harness управляет собственным serving",
     "  KV cache и событиями жизненного цикла. Для ZCode и Wello через обычный API интерфейса KV нет.",
     "- **random-attention**: гипотеза для локального inference backend с поддержкой KV eviction.",
     "  Авторские ограничения относятся к decode-phase reasoning; нельзя переносить их на API-сессии",
     "  либо обычные SQL-операции без отдельного A/B.",
     "",
     "## Правила принятия",
     "",
     "1. HTTP 200, sha256 исходного материала, source path и LLM-ответ достаточны для",
     "   **прозрачного скрининга**, но недостаточны для source-level / scientific verification.",
     "2. Каждая роль получала исключительно публичные excerpts, без tools, токенов, SQL",
     "   и приватных PROJECT.md. Неуспешные/неполные ответы остаются BLOCKED.",
     "3. Внешняя экспертиза отдельно проверяет все фактические, численные и проектные claims",
     "   на исходниках; без подтверждённого независимого oracle никакой production APPROVAL.",
     "",
     "[Машинные данные и anchor hashes](../../data/results/research-portfolio/2026-11-07-mass-swarm.json)",
     "[Независимый offline-аудит происхождения фрагментов](../../data/results/research-portfolio/2026-11-07-mass-anchor-audit.json)",

     "разделяют источник, ранее установленный статус и текущий результат роя.",
     "",
     "**Вердикт этапа: SOURCE_PACKS_COMPLETE; MODEL_SCREENING_PARTIAL; SCIENTIFIC_REPRODUCTION_PENDING.**"
    ])
    document=H/"portfolio/2026-11-07/mass-swarm-review.md"
    document.parent.mkdir(parents=True,exist_ok=True)
    document.write_text("\n".join(lines)+"\n")
    assert len(rows)==31 and len({x["study_id"] for x in rows})==31
    assert document.read_text().count("| [")>=31
    print("REPORT_SUCCESS",len(rows),"studies",dict(n),"docs",document.stat().st_size,target.stat().st_size)
if __name__=="__main__":main()
