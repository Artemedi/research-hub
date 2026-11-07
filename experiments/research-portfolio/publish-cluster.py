#!/usr/bin/env python3
"""Aggregate five cross-study critic council reviews into public provenance outputs."""
from pathlib import Path
import json,os
ROOT=Path(os.environ.get("SWARM_WORK","/var/tmp/research-portfolio-audit-20261107"))
H=Path(os.environ.get("RESEARCH_HUB_ROOT",str(ROOT/"research-hub")))
SRC=ROOT/"cluster-critics-20261107.json"
def safe(s,n=370):
    return str(s or "").replace("|","/").replace(chr(96),"'").replace("\n"," ").strip()[:n]
def main():
    original=json.loads(SRC.read_text())
    assert original.get("finished") and len(original["groups"])==5
    allgroups=[]
    counts={}
    for x in original["groups"]:
        name=x["group"];status=x["status"]
        counts[status]=counts.get(status,0)+1
        row={"group":name,"status":status,
             "elapsed_s":x.get("elapsed_s"),
             "input_tokens":x.get("input_tokens",0),
             "output_tokens":x.get("output_tokens",0),
             "scientific_review_confirmed":False}
        if status=="SCHEMA_PASS":
            j=x["verdict"]
            row.update({"questionable_ids":j.get("questionable_ids",[]),
                        "critical_gap":safe(j.get("critical_gap"),900),
                        "next_cross_study_test":safe(j.get("cross_study_test"),900),
                        "review_scope":"METADATA_ONLY"})
        allgroups.append(row)
    data={
      "date":"2026-11-07",
      "purpose":"Independent-shaped but same-model-family cross-study criticism of 31 short source screenings",
      "groups_planned":5,"groups_processed":len(allgroups),
      "status_counts":counts,
      "model_calls":original.get("calls"),
      "reported_tokens":original.get("reported_tokens"),
      "balance_remaining_deltas":original.get("balance_delta"),
      "evidence_independence":"NO: same GLM-5.3-Flash provider, new prompt and role but not a separate model family",
      "scientific_review_accepted":0,"project_fit_accepted":0,
      "limitations":[
        "Critics were shown only compressed claims and anchor IDs, not complete source texts",
        "This is secondary screening feedback, not evidence for experimental reproducibility",
        "A successful JSON answer does not establish independent scientific correctness",
        "No private registry content or source code sent in critic prompts",
        "No private credentials, raw server errors or protected paper text published"],
      "groups":allgroups}
    out=H/"data/results/research-portfolio/2026-11-07-cluster-critics.json"
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    lines=[
      "# Межисследовательская критика пяти групп роя",
      "",
      "Дата: 07.11.2026. Подробные исходные заключения: [31 исследование](mass-swarm-review.md);",
      "[машинные решения критиков](../../data/results/research-portfolio/2026-11-07-cluster-critics.json).",
      "",
      "Пять независимых **логических** ролей-критиков перечитывали краткие модельные выводы по направлениям.",
      "Это **не независимый научный oracle**: используется то же семейство GLM-5.3-Flash,",
      "без полного материала Methods/Results/Limitations. Недоказанные утверждения не повышают статус.",
      "",
      f"Всего групп {len(allgroups)}; результат: "+", ".join(f"{k}: {v}" for k,v in sorted(counts.items()))+".",
      "Production разрешений: **0**, новых доказанных project-fit: **0**.",
      "",
      "| Группа | Результат | Сомнительные source IDs | Основная проблема / следующий минимальный тест |",
      "| --- | --- | --- | --- |",
    ]
    for x in allgroups:
        uncertain=", ".join(safe(z,40) for z in x.get("questionable_ids",[])) or "—"
        idea=(safe(x.get("critical_gap"),180)+" / "+safe(x.get("next_cross_study_test"),190)) \
              if x["status"]=="SCHEMA_PASS" else "Нет проверенного заключения, требуется независимый источник/критик"
        lines.append("| "+safe(x["group"],90)+" | "+safe(x["status"],70)+" | "+uncertain+" | "+idea+" |")
    lines.extend([
      "",
      "## Итоговая приёмка",
      "",
      "Каждый сигнал критика требует конкретной сверки с pinned источником,",
      "точной версией или held-out A/B. Успешно завершённый формат вторичной модели",
      "не разрешает приписать подтверждение эффективности всем 31 исследованиям.",
      "",
      "Нерешённые и провайдером заблокированные исследования сохраняют статус",
      "§REWORK / BLOCKED_SOURCE / BLOCKED_PROVIDER§. Приватные PROJECT.md и исходники",
      "не опубликованы. Авторские цифры и claimed improvements не переименованы",
      "в измерения на локальных целевых проектах.",
    ])
    dest=H/"portfolio/2026-11-07/cluster-critics.md"
    dest.write_text("\n".join(lines).replace("§",chr(96))+"\n")
    st=H/"catalog/structure.json"
    catalog=json.loads(st.read_text())
    documents=[
      ("portfolio/2026-11-07/cluster-critics.md","Five logical critic council opinions over public source screening","review"),
      ("data/results/research-portfolio/2026-11-07-cluster-critics.json","Five grouped source-screening critic verdicts with withheld scientific approval","data"),
    ]
    known={x["to"] for x in catalog["documents"]}
    for p,title,kind in documents:
        if p not in known:
            catalog["documents"].append({"from":None,"to":p,"title":title,"kind":kind,"date":"2026-11-07"})
    st.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n")
    main_report=H/"portfolio/2026-11-07/mass-swarm-review.md"
    text=main_report.read_text()
    link="[Результаты пяти критических ролей](cluster-critics.md)"
    if link not in text:
        assert "## Правила принятия" in text
        text=text.replace("## Правила принятия",link+" — проверка достаточности вторичных выводов.\n\n## Правила принятия")
        main_report.write_text(text)
    print("CRITIC_PUBLICATION_PASS",len(allgroups),counts,out.stat().st_size,flush=True)
if __name__=="__main__":
    main()
