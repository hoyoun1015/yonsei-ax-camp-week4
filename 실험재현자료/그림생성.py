#!/usr/bin/env python3
"""논문 그림 생성.

lab_app/data의 결과 JSON을 읽어 figures/ 아래에 그림 1~7을 만든다.
파일명은 본문 그림 번호와 일치시킨다.

색상은 dataviz 팔레트 검증을 통과한 두 색만 사용한다.
조건A는 파랑 #2a78d6, 조건B는 주황 #eb6834이며 전 그림에서 이 대응을 바꾸지 않는다.

    python3 그림생성.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "lab_app", "data")
OUT = os.path.join(ROOT, "figures")

SOLO = "#2a78d6"      # 조건A
TEAM = "#eb6834"      # 조건B
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8983"
GRID = "#e3e2de"
SURFACE = "#fcfcfb"
DIMS = ["reagent", "condition", "mechanism", "safety"]
DIM_KO = {"reagent": "시약 적절성", "condition": "조건 현실성",
          "mechanism": "메커니즘 타당성", "safety": "안전성"}

plt.rcParams.update({
    "font.family": "AppleGothic",
    "axes.unicode_minus": False,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK2,
    "text.color": INK,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "font.size": 9,
    "axes.titlesize": 10,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})


def task_num(tid):
    """T10이 T7 앞에 오는 문자열 정렬을 막기 위해 숫자로 정렬한다."""
    return int(tid.lstrip("T"))


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def strip_axes(ax, keep=("left", "bottom")):
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)
    ax.tick_params(length=3, width=0.8)


def dot_handles():
    """빈 데이터로 만든 핸들은 색이 유실되므로 직접 만든다."""
    return [
        Line2D([], [], marker="o", linestyle="none", markersize=6.5,
               markerfacecolor=SOLO, markeredgecolor=SOLO, label="조건A · 단일 LLM"),
        Line2D([], [], marker="o", linestyle="none", markersize=6.5,
               markerfacecolor=TEAM, markeredgecolor=TEAM, label="조건B · 비판 루프 팀"),
    ]


def bar_handles():
    return [Patch(facecolor=SOLO, label="조건A · 단일 LLM"),
            Patch(facecolor=TEAM, label="조건B · 비판 루프 팀")]


# ── 그림 1 ─────────────────────────────────────────────────────────────
def figure1():
    """설계 도식 2패널. (a)는 두 조건이 받는 정보량 비대칭을 화살표로 보인다."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.6),
                                   gridspec_kw={"width_ratios": [1.25, 1]})

    def box(ax, x, y, w, h, text, edge, fs=7.8, weight="normal", ls="solid"):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.4,rounding_size=1.0",
                                    linewidth=1.0, edgecolor=edge, facecolor="none",
                                    linestyle=ls))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=INK, weight=weight, linespacing=1.4)

    def arrow(ax, x1, y1, x2, y2, color=MUTED, lw=0.8, style="-|>"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                     mutation_scale=8, linewidth=lw, color=color,
                                     shrinkA=1, shrinkB=1))

    # (a) 호출 구조
    ax1.set_xlim(0, 100); ax1.set_ylim(0, 100); ax1.axis("off")
    ax1.set_title("(a) 두 조건의 호출 구조", fontsize=9.4, color=INK, pad=6)

    box(ax1, 1, 84, 32, 11, "과제 20건\nk=1~5 각 4건", INK2, fs=7.8, weight="bold")

    # 조건A
    box(ax1, 2, 60, 30, 9, "조건A · 단일 LLM", SOLO, weight="bold")
    arrow(ax1, 17, 84, 17, 69, SOLO)
    box(ax1, 2, 40, 30, 9, "응답", SOLO)
    arrow(ax1, 17, 60, 17, 49, SOLO)
    ax1.text(17, 33, "호출 20회\n(과제만 입력)", ha="center", va="center",
             fontsize=7.2, color=SOLO, linespacing=1.4)

    # 조건B 7단계
    steps = ["① 합성화학자 초안", "② Critic 1차 비판", "③ 메커니즘 전문가 개선",
             "④ Critic 2차 비판", "⑤ 공정안전 전문가 최종개선",
             "⑥ Critic 3차 비판", "⑦ PI 통합"]
    ys = [82, 71, 60, 49, 38, 27, 14]
    for i, (lab, y) in enumerate(zip(steps, ys)):
        h = 8.5 if i < 6 else 9.5
        box(ax1, 44, y, 54, h, lab, TEAM, fs=7.4,
            weight="bold" if i == 6 else "normal")
    arrow(ax1, 33, 90, 44, 86.5, TEAM)
    # 누적 입력 화살표
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]:
        arrow(ax1, 71, ys[a], 71, ys[b] + 8.5, TEAM)
    arrow(ax1, 71, ys[5], 71, ys[6] + 9.5, TEAM)
    # ③은 초안+1차비판, ⑤는 1차개선안+2차비판 → 건너뛰는 입력을 상자 왼쪽 바깥에 그린다
    for src, dst in [(0, 2), (2, 4)]:
        ax1.add_patch(FancyArrowPatch((42, ys[src] + 4), (42, ys[dst] + 5),
                                      connectionstyle="arc3,rad=-0.45",
                                      arrowstyle="-|>", mutation_scale=7,
                                      linewidth=0.7, color=TEAM, alpha=0.8))
    # ⑦ PI는 앞선 6건 전부 → 오른쪽 브래킷 하나로 표시
    ax1.plot([99.5, 99.5], [ys[6] + 6, ys[0] + 4], color=TEAM, linewidth=0.8, alpha=0.7)
    for src in range(6):
        ax1.plot([98, 99.5], [ys[src] + 4, ys[src] + 4], color=TEAM, linewidth=0.6, alpha=0.6)
    arrow(ax1, 99.5, ys[6] + 6, 98, ys[6] + 5, TEAM, lw=0.8)
    ax1.text(71, 7, "호출 140회 (⑦은 앞선 6건 전부를 입력으로 받음)",
             ha="center", va="center", fontsize=7.2, color=TEAM)

    # (b) 평가 경로
    ax2.set_xlim(0, 100); ax2.set_ylim(0, 100); ax2.axis("off")
    ax2.set_title("(b) 평가 경로", fontsize=9.4, color=INK, pad=6)

    box(ax2, 4, 84, 40, 9, "조건A 응답 20건", SOLO)
    box(ax2, 54, 84, 42, 9, "조건B 최종응답 20건", TEAM)
    box(ax2, 20, 62, 60, 12,
        "블라인드 익명화\n출처 라벨 제거 · 제시 순서 교대", INK2, weight="bold")
    arrow(ax2, 24, 84, 40, 74)
    arrow(ax2, 75, 84, 60, 74)

    box(ax2, 14, 42, 72, 11, "루브릭 채점  ·  1차 20회 + 재채점 20회", INK2, fs=7.6)
    box(ax2, 14, 27, 72, 11, "조건 식별 검사  ·  20회", INK2, fs=7.6)
    box(ax2, 14, 12, 72, 11, "문헌 표준조건 일치도  ·  8회 (k=1~2 한정)", INK2,
        fs=7.6, ls=(0, (3, 2)))
    arrow(ax2, 50, 62, 50, 53)
    arrow(ax2, 50, 42, 50, 38)
    arrow(ax2, 50, 27, 50, 23)
    ax2.text(50, 5, "평가 호출 68회", ha="center", fontsize=7.6, color=INK2)

    fig.savefig(os.path.join(OUT, "figure1_design.png"))
    plt.close(fig)


# ── 그림 2 ─────────────────────────────────────────────────────────────
def figure2():
    """판정자가 조건을 지목할 때 든 단서의 범주. 단일 계열이므로 범례를 두지 않는다."""
    probe = load("identification_probe.json")
    cats = probe["cue_coding"]["categories"]
    order = sorted(cats.items(), key=lambda kv: (-kv[1], kv[0]))
    labels = [k for k, _ in order]
    vals = [v for _, v in order]

    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    ys = list(range(len(labels)))[::-1]
    ax.barh(ys, vals, height=0.58, color=TEAM, zorder=2)
    for y, v in zip(ys, vals):
        ax.text(v + 0.12, y, str(v), va="center", fontsize=8.4, color=INK2)

    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=8.4)
    ax.set_xlabel("과제 수 (n=20)")
    ax.set_xlim(0, max(vals) + 0.9)
    ax.set_xticks(range(0, max(vals) + 1))
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    strip_axes(ax, keep=("bottom",))
    ax.tick_params(axis="y", length=0)

    fig.savefig(os.path.join(OUT, "figure2_cues.png"))
    plt.close(fig)


# ── 그림 3 ─────────────────────────────────────────────────────────────
def figure3():
    """과제별 조건A→조건B 점수 이동. 짝지어진 자료이므로 덤벨로 그린다."""
    tasks = load("transcripts.json")
    order = sorted(tasks, key=lambda t: (t["task"]["k"], task_num(t["task"]["id"])))
    fig, ax = plt.subplots(figsize=(6.6, 6.6))
    ys = list(range(len(order)))[::-1]

    for y, t in zip(ys, order):
        a, b = t["judge"]["avgA"], t["judge"]["avgB"]
        ax.plot([a, b], [y, y], color=GRID, linewidth=2, solid_capstyle="round", zorder=1)
        if a == b:
            ax.scatter([a], [y + 0.19], s=42, color=SOLO, zorder=3,
                       edgecolor=SURFACE, linewidth=1.4)
            ax.scatter([b], [y - 0.19], s=42, color=TEAM, zorder=3,
                       edgecolor=SURFACE, linewidth=1.4)
            ax.text(a + 0.1, y, "동점", va="center", fontsize=7.2, color=MUTED)
        else:
            ax.scatter([a], [y], s=42, color=SOLO, zorder=3, edgecolor=SURFACE, linewidth=1.4)
            ax.scatter([b], [y], s=42, color=TEAM, zorder=3, edgecolor=SURFACE, linewidth=1.4)

    ax.set_yticks(ys)
    ax.set_yticklabels(["%s  k=%d" % (t["task"]["id"], t["task"]["k"]) for t in order], fontsize=8)
    ax.set_xlabel("루브릭 4항목 평균 점수")
    ax.set_xlim(2.2, 5.35)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    strip_axes(ax, keep=("bottom",))
    ax.tick_params(axis="y", length=0)
    for boundary in (15.5, 11.5, 7.5, 3.5):
        ax.axhline(boundary, color=GRID, linewidth=0.8, linestyle=(0, (2, 2)))

    leg = ax.legend(handles=dot_handles(), loc="lower center", bbox_to_anchor=(0.5, -0.14),
                    ncol=2, frameon=False, fontsize=8.5)
    for text in leg.get_texts():
        text.set_color(INK2)

    fig.savefig(os.path.join(OUT, "figure3_scores.png"))
    plt.close(fig)


# ── 그림 4 ─────────────────────────────────────────────────────────────
def figure4():
    """네 항목 점수 분포. 평균 막대는 표가 이미 담으므로 분포로 바꿨다."""
    tasks = load("transcripts.json")
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.6), sharex=True, sharey=True)
    xs = [2, 2.5, 3, 3.5, 4, 4.5, 5]
    width = 0.19

    for ax, dim in zip(axes.ravel(), DIMS):
        ca = {x: 0 for x in xs}
        cb = {x: 0 for x in xs}
        for t in tasks:
            ca[t["judge"]["scoresA"][dim]] = ca.get(t["judge"]["scoresA"][dim], 0) + 1
            cb[t["judge"]["scoresB"][dim]] = cb.get(t["judge"]["scoresB"][dim], 0) + 1
        pos = range(len(xs))
        ax.bar([p - width / 2 - 0.015 for p in pos], [ca[x] for x in xs], width,
               color=SOLO, zorder=2)
        ax.bar([p + width / 2 + 0.015 for p in pos], [cb[x] for x in xs], width,
               color=TEAM, zorder=2)
        ax.set_title(DIM_KO[dim], fontsize=9, color=INK, pad=5)
        ax.set_xticks(list(pos))
        ax.set_xticklabels([("%g" % x) for x in xs], fontsize=7.6)
        ax.set_ylim(0, 20)
        ax.set_yticks([0, 5, 10, 15, 20])
        ax.yaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        strip_axes(ax, keep=("left",))
        ax.tick_params(axis="x", length=0)

    for ax in axes[1]:
        ax.set_xlabel("항목 점수", fontsize=8.6)
    for ax in axes[:, 0]:
        ax.set_ylabel("과제 수", fontsize=8.6)

    leg = fig.legend(handles=bar_handles(), loc="lower center", bbox_to_anchor=(0.5, -0.04),
                     ncol=2, frameon=False, fontsize=8.5)
    for text in leg.get_texts():
        text.set_color(INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figure4_items.png"))
    plt.close(fig)


# ── 그림 5 ─────────────────────────────────────────────────────────────
def figure5():
    """1차 채점과 재채점의 과제별 Gap. 부호가 뒤집힌 과제를 라벨로 표시한다."""
    rel = load("judge_reliability.json")
    rows = rel["per_task"]
    g1 = [r["gap_round1"] for r in rows]
    g2 = [r["gap_round2"] for r in rows]

    fig, ax = plt.subplots(figsize=(4.8, 4.6))
    lim = (min(g1 + g2) - 0.35, max(g1 + g2) + 0.35)
    # 부호가 다른 두 사분면 음영
    ax.axhspan(lim[0], 0, xmin=(0 - lim[0]) / (lim[1] - lim[0]), xmax=1,
               color=GRID, alpha=0.45, zorder=0)
    ax.axhspan(0, lim[1], xmin=0, xmax=(0 - lim[0]) / (lim[1] - lim[0]),
               color=GRID, alpha=0.45, zorder=0)
    ax.plot(lim, lim, color=MUTED, linewidth=1.1, zorder=1)
    ax.axhline(0, color=GRID, linewidth=0.9, zorder=1)
    ax.axvline(0, color=GRID, linewidth=0.9, zorder=1)
    ax.scatter(g1, g2, s=40, color=TEAM, alpha=0.9, edgecolor=SURFACE,
               linewidth=1.1, zorder=3)

    for r in rows:
        if (r["gap_round1"] > 0) != (r["gap_round2"] > 0) and r["gap_round1"] != 0:
            ax.annotate(r["id"], (r["gap_round1"], r["gap_round2"]),
                        textcoords="offset points", xytext=(7, -3),
                        fontsize=7.8, color=INK)

    ax.text(0.04, 0.96, "r = %.3f\nICC(2,1) = %.3f" % (rel["gap_pearson_r"], rel["gap_icc21"]),
            transform=ax.transAxes, fontsize=8.4, color=INK, va="top", linespacing=1.6)
    ax.set_xlabel("1차 채점 Gap")
    ax.set_ylabel("재채점 Gap")
    ax.set_xlim(*lim); ax.set_ylim(*lim)
    ax.grid(True, color=GRID, linewidth=0.55)
    ax.set_axisbelow(True)
    strip_axes(ax)
    fig.savefig(os.path.join(OUT, "figure5_reliability.png"))
    plt.close(fig)


# ── 그림 6 ─────────────────────────────────────────────────────────────
def figure6():
    """응답의 표면적 특성. 지지된 기제(잔여 표지)를 (a)로 앞세운다."""
    from scipy import stats as st
    tasks = load("transcripts.json")
    sf = load("surface_features.json")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.4, 3.6))

    # (a) 심의 잔여 표지
    rows = sorted(sf["per_task"], key=lambda r: task_num(r["id"]))
    ys = list(range(len(rows)))[::-1]
    for y, r in zip(ys, rows):
        a, b = r["residue_A"], r["residue_B"]
        ax1.plot([a, b], [y, y], color=GRID, linewidth=1.8, solid_capstyle="round", zorder=1)
        ax1.scatter([a], [y], s=26, color=SOLO, zorder=3, edgecolor=SURFACE, linewidth=1.0)
        ax1.scatter([b], [y], s=26, color=TEAM, zorder=3, edgecolor=SURFACE, linewidth=1.0)
    dr = sf["deliberation_residue"]
    # 주석은 자료 점과 겹치지 않도록 축 위쪽 여백에 둔다.
    ax1.text(0.97, 0.97, "평균 %.2f 대 %.2f,  %d/20\n정확검정 p=%.1e"
             % (dr["mean_A"], dr["mean_B"], dr["b_higher"], dr["p_exact_nonzero"]),
             transform=ax1.transAxes, fontsize=7.6, color=INK, ha="right", va="top",
             linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.35", facecolor=SURFACE, edgecolor="none", alpha=0.92))
    ax1.set_yticks(ys)
    ax1.set_yticklabels([r["id"] for r in rows], fontsize=7)
    ax1.set_xlabel("심의 잔여 표지 출현 횟수")
    ax1.set_title("(a) 심의 잔여 표지", fontsize=9.2, color=INK, pad=8)
    ax1.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax1.set_axisbelow(True)
    strip_axes(ax1, keep=("bottom",))
    ax1.tick_params(axis="y", length=0)

    # (b) 길이-점수
    wa = [r["words_A"] for r in sf["per_task"]]
    wb = [r["words_B"] for r in sf["per_task"]]
    sa = [t["judge"]["avgA"] for t in tasks]
    sb = [t["judge"]["avgB"] for t in tasks]
    ax2.scatter(wa, sa, s=32, color=SOLO, alpha=0.85, edgecolor=SURFACE, linewidth=1.1, zorder=3)
    ax2.scatter(wb, sb, s=32, color=TEAM, alpha=0.85, edgecolor=SURFACE, linewidth=1.1, zorder=3)
    xs, ys2 = wa + wb, sa + sb
    fit = st.linregress(xs, ys2)
    lo, hi = min(xs), max(xs)
    ax2.plot([lo, hi], [fit.intercept + fit.slope * lo, fit.intercept + fit.slope * hi],
             color=INK2, linewidth=1.3, linestyle=(0, (4, 2)), zorder=2)
    lg = sf["length"]
    ax2.text(0.97, 0.03,
             "합산 40건 r=%.3f (p=%.3f)\n조건A 내부 r=%.3f (p=%.2f)\n조건B 내부 r=%.3f (p=%.2f)"
             % (lg["pooled_r"], lg["pooled_p"], lg["within_A_r"], lg["within_A_p"],
                lg["within_B_r"], lg["within_B_p"]),
             transform=ax2.transAxes, fontsize=7.6, color=INK, ha="right", va="bottom",
             linespacing=1.5)
    ax2.set_xlabel("응답 길이 (단어 수)")
    ax2.set_ylabel("루브릭 4항목 평균 점수")
    ax2.set_title("(b) 길이와 점수", fontsize=9.2, color=INK, pad=8)
    ax2.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax2.set_axisbelow(True)
    strip_axes(ax2)

    leg = fig.legend(handles=dot_handles(), loc="lower center", bbox_to_anchor=(0.5, -0.06),
                     ncol=2, frameon=False, fontsize=8.2)
    for text in leg.get_texts():
        text.set_color(INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figure6_surface.png"))
    plt.close(fig)


# ── 그림 7 ─────────────────────────────────────────────────────────────
def figure7():
    """같은 8과제에서 두 지표가 다른 방향을 가리키는 것을 보인다."""
    lm = load("lit_match.json")
    rows = sorted(lm["per_task"], key=lambda r: (r["k"], task_num(r["id"])))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
    ys = list(range(len(rows)))[::-1]

    for y, r in zip(ys, rows):
        g = r["rubric_gap_4dim"]
        ax1.barh(y, g, height=0.52, color=TEAM, zorder=2)
        ax1.text(g + 0.08, y, "%+.2f" % g, va="center", fontsize=7.6, color=INK2)
        d = r["lit_gap"]
        color = MUTED if d == 0 else (TEAM if d > 0 else SOLO)
        ax2.barh(y, d, height=0.52, color=color, zorder=2)
        ax2.text(d + (0.09 if d >= 0 else -0.09), y, "%+d" % d if d else "0",
                 va="center", ha="left" if d >= 0 else "right", fontsize=7.6, color=INK2)

    for ax, title, xlim, ticks in (
            (ax1, "(a) 루브릭 Gap (1–5점 척도)", (-0.3, 3.0), None),
            (ax2, "(b) 문헌일치 축 수 차이 (정수)", (-2.6, 1.6), [-2, -1, 0, 1])):
        ax.axvline(0, color=INK2, linewidth=0.9)
        ax.set_title(title, fontsize=9.0, color=INK, pad=8)
        ax.set_xlim(*xlim)
        if ticks:
            ax.set_xticks(ticks)
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        strip_axes(ax, keep=("bottom",))
        ax.tick_params(axis="y", length=0)

    ax1.set_yticks(ys)
    ax1.set_yticklabels(["%s  k=%d" % (r["id"], r["k"]) for r in rows], fontsize=8)
    ax1.annotate("조건B 우위 →", xy=(0.5, -0.17), xycoords="axes fraction",
                 ha="center", fontsize=7.8, color=MUTED)
    ax2.annotate("← 조건A 우위          조건B 우위 →", xy=(0.5, -0.17),
                 xycoords="axes fraction", ha="center", fontsize=7.8, color=MUTED)

    fig.savefig(os.path.join(OUT, "figure7_two_metrics.png"))
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".png"):
            os.remove(os.path.join(OUT, f))
    figure1(); figure2(); figure3(); figure4(); figure5(); figure6(); figure7()
    print("figures written to", OUT)
    for name in sorted(os.listdir(OUT)):
        print(" ", name)
