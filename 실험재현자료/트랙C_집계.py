#!/usr/bin/env python3
"""트랙 C 결과 집계.

입력은 트랙 C 워크플로 결과 JSON이다. 두 가지를 수행한다.

1. P1 — 전제가 성립하지 않던 과제 세 건(T14/T18/T20)을 교체본으로 갈아끼운
   정정 세트를 만들고, 원본 세트와 정정 세트의 통계를 나란히 계산한다.
2. P5 — 유지된 17과제의 3라운드 채점과 교체본 3과제의 3라운드 채점을 합쳐
   과제 수준 Gap의 3라운드 신뢰도(ICC(2,1))와 라운드 평균 Gap을 계산한다.

    python3 트랙C_집계.py <워크플로결과.json>
"""
import json
import os
import sys

from scipy import stats as st

DIMS = ["reagent", "condition", "mechanism", "safety"]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "lab_app", "data")
REPLACED = {"T14": "T14b", "T18": "T18b", "T20": "T20b"}


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def avg(scores, dims):
    return sum(scores[d] for d in dims) / len(dims)


def icc21(rows):
    """단일 측정 절대일치 ICC(2,1). rows는 대상별 측정값 리스트."""
    n = len(rows)
    k = len(rows[0])
    grand = sum(v for r in rows for v in r) / (n * k)
    ss_rows = k * sum((sum(r) / k - grand) ** 2 for r in rows)
    ss_cols = n * sum((sum(r[j] for r in rows) / n - grand) ** 2 for j in range(k))
    ss_tot = sum((v - grand) ** 2 for r in rows for v in r)
    ss_err = ss_tot - ss_rows - ss_cols
    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / (k - 1)
    ms_err = ss_err / ((n - 1) * (k - 1))
    denom = ms_rows + (k - 1) * ms_err + k * (ms_cols - ms_err) / n
    return (ms_rows - ms_err) / denom if denom else float("nan")


def unblind(rec, order):
    """제시 순서에 따라 채점 결과를 조건별로 되돌린다."""
    b_first = order == "B_first"
    b = rec["scores_first"] if b_first else rec["scores_second"]
    a = rec["scores_second"] if b_first else rec["scores_first"]
    guessed_b = (rec["more_deliberated"] == "제안1") if b_first else (rec["more_deliberated"] == "제안2")
    return a, b, guessed_b


def summarize(gaps, ks, label):
    nz = [g for g in gaps if g != 0]
    out = {
        "label": label, "n": len(gaps),
        "mean_gap": sum(gaps) / len(gaps),
        "b_wins": sum(1 for g in gaps if g > 0),
        "ties": sum(1 for g in gaps if g == 0),
        "a_wins": sum(1 for g in gaps if g < 0),
        "wilcoxon_p_approx": float(st.wilcoxon(gaps, method="approx").pvalue),
        "wilcoxon_p_exact_nonzero": float(st.wilcoxon(nz, method="exact").pvalue) if len(nz) > 1 else None,
        "cohen_dz": (sum(gaps) / len(gaps)) / (st.tstd(gaps)),
        "k_slope": float(st.linregress(ks, gaps).slope),
        "k_p": float(st.linregress(ks, gaps).pvalue),
        "k_spearman_rho": float(st.spearmanr(ks, gaps)[0]),
        "k_spearman_p": float(st.spearmanr(ks, gaps)[1]),
    }
    return out


def main(path):
    with open(path, encoding="utf-8") as fh:
        wf = json.load(fh)
    reps = {r["id"]: r for r in wf["replacements"]}
    r3 = {r["id"]: r for r in wf["round3_kept"]}
    tasks = {t["task"]["id"]: t for t in load("transcripts.json")}
    rel = {r["id"]: r for r in load("judge_reliability.json")["per_task"]}

    # ── 원본 세트 (교체 전) ─────────────────────────────────────────
    orig_ids = sorted(tasks, key=lambda i: int(i[1:]))
    orig_gaps = [tasks[i]["judge"]["gap"] for i in orig_ids]
    orig_ks = [tasks[i]["task"]["k"] for i in orig_ids]

    # ── 정정 세트 (교체 후) ─────────────────────────────────────────
    corr_ids, corr_gaps, corr_ks, per_task = [], [], [], []
    for i in orig_ids:
        if i in REPLACED:
            new = reps[REPLACED[i]]
            a, b, gb = unblind(new["judge_rounds"][0], new["order"])
            gap = avg(b, DIMS) - avg(a, DIMS)
            corr_ids.append(new["id"]); corr_gaps.append(gap); corr_ks.append(new["k"])
            per_task.append({"id": new["id"], "replaces": i, "k": new["k"],
                             "avgA": avg(a, DIMS), "avgB": avg(b, DIMS), "gap": gap,
                             "order": new["order"], "guessedB": gb,
                             "ident_correct": (new["ident"]["multi_agent"] == "제안2")
                             if new["order"] == "A_first" else
                             (new["ident"]["multi_agent"] == "제안1"),
                             "ident_cue": new["ident"]["cue"]})
        else:
            corr_ids.append(i); corr_gaps.append(tasks[i]["judge"]["gap"])
            corr_ks.append(tasks[i]["task"]["k"])
            per_task.append({"id": i, "k": tasks[i]["task"]["k"],
                             "avgA": tasks[i]["judge"]["avgA"], "avgB": tasks[i]["judge"]["avgB"],
                             "gap": tasks[i]["judge"]["gap"], "order": tasks[i]["judge"]["order"],
                             "guessedB": tasks[i]["judge"]["guessedB"]})

    # ── 항목별 분해 (정정 세트) ─────────────────────────────────────
    dim_diff = {}
    for d in DIMS:
        diffs = []
        for i in orig_ids:
            if i in REPLACED:
                new = reps[REPLACED[i]]
                a, b, _ = unblind(new["judge_rounds"][0], new["order"])
                diffs.append(b[d] - a[d])
            else:
                diffs.append(tasks[i]["judge"]["scoresB"][d] - tasks[i]["judge"]["scoresA"][d])
        dim_diff[d] = {"diff": sum(diffs) / len(diffs),
                       "wilcoxon_p_approx": float(st.wilcoxon(diffs, method="approx").pvalue)}
    tot = sum(v["diff"] for v in dim_diff.values())
    for d in DIMS:
        dim_diff[d]["share"] = dim_diff[d]["diff"] / tot

    # ── 3차원 강건성 (정정 세트) ────────────────────────────────────
    D3 = DIMS[:3]
    g3 = []
    for i in orig_ids:
        if i in REPLACED:
            new = reps[REPLACED[i]]
            a, b, _ = unblind(new["judge_rounds"][0], new["order"])
            g3.append(avg(b, D3) - avg(a, D3))
        else:
            g3.append(avg(tasks[i]["judge"]["scoresB"], D3) - avg(tasks[i]["judge"]["scoresA"], D3))

    # ── P5: 3라운드 신뢰도 ──────────────────────────────────────────
    triples, round_means = [], [[], [], []]
    for i in orig_ids:
        if i in REPLACED:
            new = reps[REPLACED[i]]
            gs = []
            for rec in new["judge_rounds"][:3]:
                a, b, _ = unblind(rec, new["order"])
                gs.append(avg(b, DIMS) - avg(a, DIMS))
        else:
            g1 = tasks[i]["judge"]["gap"]
            g2 = rel[i]["gap_round2"]
            a, b, _ = unblind(r3[i], tasks[i]["judge"]["order"])
            gs = [g1, g2, avg(b, DIMS) - avg(a, DIMS)]
        if len(gs) == 3:
            triples.append(gs)
            for j in range(3):
                round_means[j].append(gs[j])

    mean3 = [sum(t) / 3 for t in triples]
    out = {
        "note": "트랙 C 집계. P1은 전제 결함 과제 3건을 교체한 정정 세트를, P5는 3라운드 채점 신뢰도를 다룬다. 원본 세트 통계도 함께 남겨 교체의 영향을 비교할 수 있게 했다.",
        "replaced": REPLACED,
        "original_set": summarize(orig_gaps, orig_ks, "원본 20건"),
        "corrected_set": summarize(corr_gaps, corr_ks, "정정 20건"),
        "corrected_dim_breakdown": dim_diff,
        "corrected_3dim": summarize(g3, corr_ks, "정정 20건 · 안전성 제외"),
        "p5_three_round": {
            "n": len(triples),
            "icc21_three_rounds": icc21(triples),
            "round_mean_gaps": [sum(r) / len(r) for r in round_means],
            "mean_of_round_means": sum(mean3) / len(mean3),
            "sd_of_task_means": st.tstd(mean3),
            "dz_on_round_averaged_gap": (sum(mean3) / len(mean3)) / st.tstd(mean3),
            "wilcoxon_p_on_round_averaged": float(st.wilcoxon(mean3, method="approx").pvalue),
            "sign_stable_across_three_rounds": sum(
                1 for t in triples if all(v > 0 for v in t) or all(v < 0 for v in t)),
        },
        "replacement_detail": [p for p in per_task if "replaces" in p],
        "per_task_corrected": per_task,
    }
    dest = os.path.join(DATA, "track_c.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    print("=== P1 교체 영향 ===")
    for key in ("original_set", "corrected_set"):
        s = out[key]
        print("  %-14s 평균 Gap %.4f  B우위 %d/%d  근사 p=%.5g  dz=%.3f  k기울기 %.3f (p=%.4f)"
              % (s["label"], s["mean_gap"], s["b_wins"], s["n"], s["wilcoxon_p_approx"],
                 s["cohen_dz"], s["k_slope"], s["k_p"]))
    print("  정정 세트 안전성 제외: 평균 %.4f, p=%.5g, dz=%.3f"
          % (out["corrected_3dim"]["mean_gap"], out["corrected_3dim"]["wilcoxon_p_approx"],
             out["corrected_3dim"]["cohen_dz"]))
    print("  항목별 비중:", ", ".join("%s %.1f%%" % (d, dim_diff[d]["share"] * 100) for d in DIMS))
    print()
    print("=== P5 3라운드 신뢰도 ===")
    p5 = out["p5_three_round"]
    print("  n=%d  ICC(2,1) 3라운드 = %.3f  (2라운드 기준 0.359)" % (p5["n"], p5["icc21_three_rounds"]))
    print("  라운드별 평균 Gap:", ["%.3f" % v for v in p5["round_mean_gaps"]])
    print("  라운드 평균 Gap으로 계산한 dz = %.3f, p = %.5g"
          % (p5["dz_on_round_averaged_gap"], p5["wilcoxon_p_on_round_averaged"]))
    print("  3라운드 부호가 모두 같은 과제: %d/%d" % (p5["sign_stable_across_three_rounds"], p5["n"]))
    print()
    print("=== 교체본 상세 ===")
    for p in out["replacement_detail"]:
        print("  %s (구 %s, k=%d): A %.3f / B %.3f / Gap %+.3f / 식별 %s"
              % (p["id"], p["replaces"], p["k"], p["avgA"], p["avgB"], p["gap"],
                 "정답" if p["ident_correct"] else "오답"))
    print("\nsaved", dest)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
