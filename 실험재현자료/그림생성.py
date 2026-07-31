#!/usr/bin/env python3
"""논문 그림 생성.

lab_app/data의 결과 JSON을 읽어 figures/ 아래에 그림을 만든다.
그림 6은 judge_reliability.json이 있을 때만 생성한다.

색상은 dataviz 팔레트 검증을 통과한 두 색만 사용한다.
조건A는 파랑 #2a78d6, 조건B는 주황 #eb6834이며, 전 그림에서 이 대응을 바꾸지 않는다.

    python3 그림생성.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch


def task_num(tid):
    """T10이 T7 앞에 오는 문자열 정렬을 막기 위해 숫자로 정렬한다."""
    return int(tid.lstrip("T"))

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


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def strip_axes(ax, keep=("left", "bottom")):
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)
    ax.tick_params(length=3, width=0.8)


def dot_handles():
    """조건 대응을 고정한 점 범례. 빈 데이터로 만든 핸들은 색이 유실되므로 직접 만든다."""
    return [
        Line2D([], [], marker="o", linestyle="none", markersize=6.5,
               markerfacecolor=SOLO, markeredgecolor=SOLO, label="조건A · 단일 LLM"),
        Line2D([], [], marker="o", linestyle="none", markersize=6.5,
               markerfacecolor=TEAM, markeredgecolor=TEAM, label="조건B · 비판루프 팀"),
    ]


def bar_handles():
    return [Patch(facecolor=SOLO, label="조건A · 단일 LLM"),
            Patch(facecolor=TEAM, label="조건B · 비판루프 팀")]


def fig1_design():
    """실험 설계 도식. 차트가 아니라 다이어그램이다."""
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 46)
    ax.axis("off")

    def box(x, y, w, h, text, edge, fill="none", fs=8.5, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                    linewidth=1.1, edgecolor=edge, facecolor=fill))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=INK, weight=weight, linespacing=1.5)

    def arrow(x1, y1, x2, y2, color=MUTED):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=9, linewidth=0.9, color=color))

    box(1, 20, 15, 10, "과제 20건\nk=1~5 각 4건", INK2, weight="bold")

    box(23, 33, 26, 10, "조건A · 단일 LLM\n1회 호출", SOLO)
    box(23, 9, 34, 10, "조건B · 비판루프 팀\n분리 에이전트 7회 호출", TEAM)
    ax.text(40, 5.2, "초안 → 비판 → 개선 → 비판 → 개선 → 비판 → PI 통합",
            ha="center", va="center", fontsize=7.2, color=MUTED)

    arrow(16, 27, 22, 36)
    arrow(16, 23, 22, 15)

    box(63, 20, 15, 10, "블라인드\n익명화", INK2)
    arrow(49, 37, 67, 31)
    arrow(57, 14, 67, 19)

    box(84, 30, 15, 9, "루브릭 4항목\n1차·2차 채점", INK2)
    box(84, 10, 15, 9, "문헌일치\nk=1~2 한정", INK2)
    arrow(78, 27, 87, 30)
    arrow(78, 23, 87, 19)

    fig.savefig(os.path.join(OUT, "figure1_design.png"))
    plt.close(fig)


def fig2_dumbbell():
    """과제별 조건A→조건B 점수 이동. 짝지어진 before/after이므로 덤벨로 그린다."""
    tasks = load("transcripts.json")
    order = sorted(tasks, key=lambda t: (t["task"]["k"], task_num(t["task"]["id"])))
    fig, ax = plt.subplots(figsize=(6.6, 6.6))
    ys = list(range(len(order)))[::-1]

    for y, t in zip(ys, order):
        a, b = t["judge"]["avgA"], t["judge"]["avgB"]
        ax.plot([a, b], [y, y], color=GRID, linewidth=2, solid_capstyle="round", zorder=1)
        if a == b:
            # 동점이면 두 점이 완전히 겹쳐 한쪽이 보이지 않으므로 위아래로 갈라 그린다.
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

    for k, boundary in ((1, 15.5), (2, 11.5), (3, 7.5), (4, 3.5)):
        ax.axhline(boundary, color=GRID, linewidth=0.8, linestyle=(0, (2, 2)))

    leg = ax.legend(handles=dot_handles(), loc="lower center", bbox_to_anchor=(0.5, -0.14),
                    ncol=2, frameon=False, fontsize=8.5)
    for text in leg.get_texts():
        text.set_color(INK2)

    fig.savefig(os.path.join(OUT, "figure2_scores.png"))
    plt.close(fig)


def fig3_dimensions():
    """루브릭 항목별 조건 간 평균 점수. 항목 정체성 비교이므로 짝지은 막대로 그린다."""
    sv = load("stats_verified.json")["dimension_breakdown"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    xs = range(len(DIMS))
    width = 0.36
    gap = 0.02

    for i, dim in enumerate(DIMS):
        a, b = sv[dim]["meanA"], sv[dim]["meanB"]
        ax.bar(i - width / 2 - gap, a, width, color=SOLO, zorder=2)
        ax.bar(i + width / 2 + gap, b, width, color=TEAM, zorder=2)
        ax.text(i - width / 2 - gap, a + 0.09, "%.2f" % a, ha="center", fontsize=7.8, color=INK2)
        ax.text(i + width / 2 + gap, b + 0.09, "%.2f" % b, ha="center", fontsize=7.8, color=INK2)
        ax.text(i, 5.55, "+%.2f" % sv[dim]["diff"], ha="center", fontsize=8.6,
                color=TEAM if dim == "safety" else INK2,
                weight="bold" if dim == "safety" else "normal")

    ax.set_xticks(list(xs))
    ax.set_xticklabels([DIM_KO[d] for d in DIMS], fontsize=8.5)
    ax.set_ylabel("평균 점수", labelpad=8)
    ax.set_ylim(0, 6.1)
    ax.set_yticks([0, 1, 2, 3, 4, 5])
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    strip_axes(ax, keep=("left",))
    ax.tick_params(axis="x", length=0)
    ax.text(-0.68, 5.55, "차이", fontsize=8, color=MUTED, ha="center")

    leg = ax.legend(handles=bar_handles(), loc="lower center", bbox_to_anchor=(0.5, -0.30),
                    ncol=2, frameon=False, fontsize=8.5)
    for text in leg.get_texts():
        text.set_color(INK2)

    fig.savefig(os.path.join(OUT, "figure3_dimensions.png"))
    plt.close(fig)


def fig4_two_metrics():
    """같은 8과제에서 두 지표가 서로 다른 방향을 가리키는 것을 보인다."""
    lm = load("lit_match.json")
    rows = sorted(lm["per_task"], key=lambda r: (r["k"], task_num(r["id"])))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
    ys = list(range(len(rows)))[::-1]
    labels = ["%s  k=%d" % (r["id"], r["k"]) for r in rows]

    for y, r in zip(ys, rows):
        g = r["rubric_gap_4dim"]
        ax1.barh(y, g, height=0.52, color=TEAM if g > 0 else SOLO, zorder=2)
        ax1.text(g + 0.08, y, "%+.2f" % g, va="center", fontsize=7.6, color=INK2)

        d = r["lit_gap"]
        color = MUTED if d == 0 else (TEAM if d > 0 else SOLO)
        ax2.barh(y, d, height=0.52, color=color, zorder=2)
        offset = 0.09 if d >= 0 else -0.09
        ax2.text(d + offset, y, "%+d" % d if d else "0", va="center",
                 ha="left" if d >= 0 else "right", fontsize=7.6, color=INK2)

    for ax, title, xlim in ((ax1, "LLM-judge 루브릭 Gap", (-0.3, 3.0)),
                            (ax2, "문헌일치 항목 수 차이", (-2.6, 1.6))):
        ax.axvline(0, color=INK2, linewidth=0.9)
        ax.set_title(title, fontsize=9.2, color=INK, pad=8)
        ax.set_xlim(*xlim)
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        strip_axes(ax, keep=("bottom",))
        ax.tick_params(axis="y", length=0)

    ax1.set_yticks(ys)
    ax1.set_yticklabels(labels, fontsize=8)
    # 방향 주석은 눈금 라벨과 겹치지 않도록 축 아래 별도 줄에 둔다.
    ax1.annotate("조건B 우위 →", xy=(0.5, -0.16), xycoords="axes fraction",
                 ha="center", fontsize=7.8, color=MUTED)
    ax2.annotate("← 조건A 우위          조건B 우위 →", xy=(0.5, -0.16),
                 xycoords="axes fraction", ha="center", fontsize=7.8, color=MUTED)

    fig.savefig(os.path.join(OUT, "figure6_two_metrics.png"))
    plt.close(fig)


def fig5_length():
    """응답 길이와 판정 점수의 관계. 단일 계열이므로 범례를 두지 않는다."""
    from scipy import stats as st
    tasks = load("transcripts.json")
    raw = load("length_analysis_raw.json")
    wa = [r["wa"] for r in raw]
    wb = [r["wb"] for r in raw]
    sa = [t["judge"]["avgA"] for t in tasks]
    sb = [t["judge"]["avgB"] for t in tasks]

    sf = load("surface_features.json")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.4, 3.6))

    # (a) 길이-점수. pooled 적합선은 군집 차이에 끌려가므로 조건 내부 상관을 함께 적는다.
    ax1.scatter(wa, sa, s=32, color=SOLO, alpha=0.85, edgecolor=SURFACE, linewidth=1.1, zorder=3)
    ax1.scatter(wb, sb, s=32, color=TEAM, alpha=0.85, edgecolor=SURFACE, linewidth=1.1, zorder=3)
    xs, ys = wa + wb, sa + sb
    fit = st.linregress(xs, ys)
    lo, hi = min(xs), max(xs)
    ax1.plot([lo, hi], [fit.intercept + fit.slope * lo, fit.intercept + fit.slope * hi],
             color=INK2, linewidth=1.3, linestyle=(0, (4, 2)), zorder=2)
    lg = sf["length"]
    ax1.text(0.97, 0.03,
             "합산 40건 r=%.3f (p=%.3f)\n조건A 내부 r=%.3f (p=%.2f)\n조건B 내부 r=%.3f (p=%.2f)"
             % (lg["pooled_r"], lg["pooled_p"], lg["within_A_r"], lg["within_A_p"],
                lg["within_B_r"], lg["within_B_p"]),
             transform=ax1.transAxes, fontsize=7.6, color=INK, ha="right", va="bottom",
             linespacing=1.5)
    ax1.set_xlabel("응답 길이 (단어 수)")
    ax1.set_ylabel("루브릭 4항목 평균 점수")
    ax1.set_title("(a) 길이와 점수", fontsize=9.2, color=INK, pad=8)
    ax1.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax1.set_axisbelow(True)
    strip_axes(ax1)

    # (b) 심의 잔여 표지. 과제별 짝지은 값이므로 덤벨로 그린다.
    rows = sorted(sf["per_task"], key=lambda r: task_num(r["id"]))
    ys2 = list(range(len(rows)))[::-1]
    for y, r in zip(ys2, rows):
        a, b = r["residue_A"], r["residue_B"]
        ax2.plot([a, b], [y, y], color=GRID, linewidth=1.8, solid_capstyle="round", zorder=1)
        ax2.scatter([a], [y], s=26, color=SOLO, zorder=3, edgecolor=SURFACE, linewidth=1.0)
        ax2.scatter([b], [y], s=26, color=TEAM, zorder=3, edgecolor=SURFACE, linewidth=1.0)
    dr = sf["deliberation_residue"]
    ax2.text(0.97, 0.03, "평균 %.2f 대 %.2f,  %d/20\nWilcoxon p=%.1e"
             % (dr["mean_A"], dr["mean_B"], dr["b_higher"], dr["p_exact_nonzero"]),
             transform=ax2.transAxes, fontsize=7.6, color=INK, ha="right", va="bottom",
             linespacing=1.5)
    ax2.set_yticks(ys2)
    ax2.set_yticklabels([r["id"] for r in rows], fontsize=7)
    ax2.set_xlabel("심의 잔여 표지 출현 횟수")
    ax2.set_title("(b) 심의 잔여 표지", fontsize=9.2, color=INK, pad=8)
    ax2.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax2.set_axisbelow(True)
    strip_axes(ax2, keep=("bottom",))
    ax2.tick_params(axis="y", length=0)

    leg = fig.legend(handles=dot_handles(), loc="lower center", bbox_to_anchor=(0.5, -0.06),
                     ncol=2, frameon=False, fontsize=8.2)
    for text in leg.get_texts():
        text.set_color(INK2)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figure5_surface.png"))
    plt.close(fig)


def fig6_reliability():
    """1차 채점과 재채점의 과제별 Gap 일치도."""
    path = os.path.join(DATA, "judge_reliability.json")
    if not os.path.exists(path):
        print("skip fig6 — judge_reliability.json 없음")
        return
    rel = load("judge_reliability.json")
    rows = rel["per_task"]
    g1 = [r["gap_round1"] for r in rows]
    g2 = [r["gap_round2"] for r in rows]

    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    lim = (min(g1 + g2) - 0.35, max(g1 + g2) + 0.35)
    ax.plot(lim, lim, color=GRID, linewidth=1.2, zorder=1)
    ax.axhline(0, color=GRID, linewidth=0.8, linestyle=(0, (2, 2)), zorder=1)
    ax.axvline(0, color=GRID, linewidth=0.8, linestyle=(0, (2, 2)), zorder=1)
    ax.scatter(g1, g2, s=40, color=TEAM, alpha=0.85, edgecolor=SURFACE, linewidth=1.1, zorder=3)

    ax.text(0.06, 0.94, "r = %.3f\nICC(2,1) = %.3f" % (rel["gap_pearson_r"], rel["gap_icc21"]),
            transform=ax.transAxes, fontsize=8.6, color=INK, va="top", linespacing=1.6)
    ax.set_xlabel("1차 채점 Gap")
    ax.set_ylabel("재채점 Gap")
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    strip_axes(ax)
    fig.savefig(os.path.join(OUT, "figure4_reliability.png"))
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    fig1_design()
    fig2_dumbbell()
    fig3_dimensions()
    fig4_two_metrics()
    fig5_length()
    fig6_reliability()
    print("figures written to", OUT)
    for name in sorted(os.listdir(OUT)):
        print(" ", name)
