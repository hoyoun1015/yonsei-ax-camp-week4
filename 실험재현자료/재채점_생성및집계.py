#!/usr/bin/env python3
"""판정자 신뢰도 측정용 재채점 자료 생성 및 집계.

용도
----
`prepare` 모드는 transcripts.json에서 과제별 블라인드 채점 파일을 만든다.
조건 라벨을 제거하고 1차 채점과 동일한 제시 순서를 유지하므로, 재채점 결과를
1차 채점과 직접 비교할 수 있다.

`aggregate` 모드는 재채점 결과 JSON을 받아 1차 채점과의 일치도를 계산한다.
항목 수준 상관, 과제 수준 Gap 상관, 조건 판정 일치율, ICC(2,1)을 보고한다.

사용법
------
    python3 재채점_생성및집계.py prepare  <출력디렉토리>
    python3 재채점_생성및집계.py aggregate <재채점결과.json>
"""
import json
import os
import sys

DIMS = ["reagent", "condition", "mechanism", "safety"]
RUBRIC = (
    "각 항목을 1~5점으로 채점하시오: reagent(시약 적절성), "
    "condition(조건 현실성), mechanism(메커니즘 타당성), safety(안전성)."
)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TRANSCRIPTS = os.path.join(ROOT, "lab_app", "data", "transcripts.json")


def load_tasks():
    with open(TRANSCRIPTS, encoding="utf-8") as fh:
        return json.load(fh)


def prepare(outdir):
    """1차 채점과 동일한 순서로 조건 라벨을 지운 채점 파일을 만든다."""
    os.makedirs(outdir, exist_ok=True)
    for task in load_tasks():
        b_first = task["judge"]["order"] == "B_first"
        team = task["conditionB"]["finalResponse"]
        solo = task["conditionA"]
        first, second = (team, solo) if b_first else (solo, team)
        path = os.path.join(outdir, task["task"]["id"] + ".md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(
                "# 과제\n%s\n\n# 채점 기준\n%s\n\n# 제안1\n%s\n\n# 제안2\n%s\n"
                % (task["task"]["prompt"], RUBRIC, first, second)
            )
        print("wrote", path)


def icc21(pairs):
    """단일 측정 절대일치 ICC(2,1). pairs는 (측정1, 측정2) 목록이다."""
    n = len(pairs)
    grand = sum(a + b for a, b in pairs) / (2 * n)
    row_means = [(a + b) / 2 for a, b in pairs]
    col_means = [sum(p[0] for p in pairs) / n, sum(p[1] for p in pairs) / n]
    ss_rows = 2 * sum((m - grand) ** 2 for m in row_means)
    ss_cols = n * sum((m - grand) ** 2 for m in col_means)
    ss_total = sum((v - grand) ** 2 for p in pairs for v in p)
    ss_err = ss_total - ss_rows - ss_cols
    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / 1
    ms_err = ss_err / (n - 1)
    # ICC(2,1) = (MS_R - MS_E) / (MS_R + (k-1)MS_E + k(MS_C - MS_E)/n), k=2
    denom = ms_rows + ms_err + 2 * (ms_cols - ms_err) / n
    return (ms_rows - ms_err) / denom if denom else float("nan")


def aggregate(result_path):
    from scipy import stats as st

    with open(result_path, encoding="utf-8") as fh:
        rescores = {r["id"]: r for r in json.load(fh)}
    tasks = {t["task"]["id"]: t for t in load_tasks()}

    item_pairs, gap_pairs, winner_match, rows = [], [], 0, []
    for tid, task in tasks.items():
        if tid not in rescores:
            continue
        r = rescores[tid]
        b_first = task["judge"]["order"] == "B_first"
        new_b = r["scores_first"] if b_first else r["scores_second"]
        new_a = r["scores_second"] if b_first else r["scores_first"]
        old_a, old_b = task["judge"]["scoresA"], task["judge"]["scoresB"]
        for dim in DIMS:
            item_pairs.append((old_a[dim], new_a[dim]))
            item_pairs.append((old_b[dim], new_b[dim]))
        avg = lambda s: sum(s[d] for d in DIMS) / 4
        new_gap = avg(new_b) - avg(new_a)
        gap_pairs.append((task["judge"]["gap"], new_gap))
        guessed_b = (
            r["more_deliberated"] == "제안1" if b_first else r["more_deliberated"] == "제안2"
        )
        winner_match += int(guessed_b == task["judge"]["guessedB"])
        rows.append(
            {
                "id": tid,
                "k": task["task"]["k"],
                "gap_round1": task["judge"]["gap"],
                "gap_round2": new_gap,
                "guessedB_round1": task["judge"]["guessedB"],
                "guessedB_round2": guessed_b,
            }
        )

    n = len(rows)
    g1 = [p[0] for p in gap_pairs]
    g2 = [p[1] for p in gap_pairs]
    exact = sum(1 for a, b in item_pairs if a == b) / len(item_pairs)
    within1 = sum(1 for a, b in item_pairs if abs(a - b) <= 1) / len(item_pairs)
    out = {
        "note": "1차 채점과 독립 재채점의 일치도. 두 라운드는 동일한 블라인드 자료와 동일한 제시 순서를 사용했다.",
        "n_tasks": n,
        "item_exact_agreement": exact,
        "item_within_1_agreement": within1,
        "item_icc21": icc21(item_pairs),
        "gap_pearson_r": st.pearsonr(g1, g2)[0],
        "gap_pearson_p": st.pearsonr(g1, g2)[1],
        "gap_icc21": icc21(gap_pairs),
        "mean_gap_round1": sum(g1) / n,
        "mean_gap_round2": sum(g2) / n,
        "b_wins_round2": sum(1 for v in g2 if v > 0),
        "ties_round2": sum(1 for v in g2 if v == 0),
        "a_wins_round2": sum(1 for v in g2 if v < 0),
        "wilcoxon_p_round2": float(st.wilcoxon(g2, method="approx").pvalue),
        "blind_correct_round2": sum(1 for r in rows if r["guessedB_round2"]),
        "blind_agreement_between_rounds": winner_match / n,
        "per_task": rows,
    }
    dest = os.path.join(ROOT, "lab_app", "data", "judge_reliability.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    for key, value in out.items():
        if key not in ("per_task", "note"):
            print("%-34s %s" % (key, value))
    print("\nsaved", dest)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    mode, arg = sys.argv[1], sys.argv[2]
    if mode == "prepare":
        prepare(arg)
    elif mode == "aggregate":
        aggregate(arg)
    else:
        print(__doc__)
        sys.exit(1)
