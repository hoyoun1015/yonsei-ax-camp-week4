const SPEAKER_LABELS = {
  synthetic_chemist: "합성화학자",
  mechanistic_chemist: "메커니즘전문가",
  safety_specialist: "안전전문가",
  critic: "Scientific Critic",
  pi: "PI",
};

let currentTask = null;
let allTasksSummary = [];
let campaignLoaded = false;
let roundIndex = -1; // -1 = nothing shown yet
let playTimer = null;
let typeTimer = null;
let scene = "team"; // "team" | "solo" | "campaign"
let wanderRunning = false;

const TEAM_ROLES = ["pi", "synthetic_chemist", "mechanistic_chemist", "safety_specialist", "critic"];
const WANDER_RANGE = { dx: 70, dy: 18 };
const APPROACH = {
  pi: { dx: 0, dy: 55, face: 1 },
  synthetic_chemist: { dx: 85, dy: 15, face: 1 },
  mechanistic_chemist: { dx: -85, dy: 15, face: -1 },
  safety_specialist: { dx: 55, dy: -35, face: 1 },
  critic: { dx: -55, dy: -35, face: -1 },
};
const wanderState = {}; // role -> { lastDx, lastDy, timer }
const baseRects = {}; // role -> un-transformed sprite-anchor position within .room-tiles

function rand(min, max) {
  return min + Math.random() * (max - min);
}
function getMountByRole(role) {
  return document.querySelector(`.sprite-mount[data-speaker="${role}"]`);
}
const PX = 4; // world grid unit — matches the sprite's own pixel size

function quantize(v) {
  return Math.round(v / PX) * PX;
}

// .room-floor clips overflow, and mount-sc/mount-mc sit close to its side
// walls — a naive +-70px wander on top of that base position walked the
// (now visually bigger, 96px) sprite straight past the wall and got most of
// it clipped, leaving just a sliver poking out. Record each role's real,
// un-transformed position once at startup so wander can be clamped to what
// the room actually has room for, instead of a fixed range that assumes
// every mount has the same clearance.
function captureBaseRects() {
  const room = document.querySelector("#scene-team .room-tiles");
  if (!room) return;
  const roomRect = room.getBoundingClientRect();
  TEAM_ROLES.forEach((role) => {
    const mount = getMountByRole(role);
    if (!mount) return;
    const anchor = mount.querySelector(".sprite-anchor");
    const r = anchor.getBoundingClientRect();
    baseRects[role] = {
      left: r.left - roomRect.left,
      top: r.top - roomRect.top,
      width: r.width,
      height: r.height,
      roomWidth: roomRect.width,
      roomHeight: roomRect.height,
    };
  });
}

function wanderBounds(role) {
  const base = baseRects[role];
  const margin = 6;
  if (!base) {
    return { minDx: -WANDER_RANGE.dx, maxDx: WANDER_RANGE.dx, minDy: -WANDER_RANGE.dy, maxDy: WANDER_RANGE.dy };
  }
  return {
    minDx: Math.max(-WANDER_RANGE.dx, margin - base.left),
    maxDx: Math.min(WANDER_RANGE.dx, base.roomWidth - margin - base.width - base.left),
    minDy: Math.max(-WANDER_RANGE.dy, margin - base.top),
    maxDy: Math.min(WANDER_RANGE.dy, base.roomHeight - margin - base.height - base.top),
  };
}

function moveTo(mount, dx, dy, face, duration) {
  const anchor = mount.querySelector(".sprite-anchor");
  const canvas = mount.querySelector(".sprite-canvas");
  const nameTag = mount.querySelector(".name-tag");
  // AI Town / generative-agents style sims (PixiJS) move characters at a
  // constant walking speed every frame — smooth, not eased, not stepped.
  // steps() made it look like a stop-motion glitch; the "chunky" part of
  // that look is supposed to live in the sprite art, not the motion.
  anchor.style.transition = `transform ${duration}s linear`;
  anchor.style.transform = `translate(${dx}px, ${dy}px) scaleX(${face})`;
  // The name-tag is a flex sibling of sprite-anchor, not a child, so it
  // never inherited the anchor's transform — it used to stay put while the
  // character wandered off, visually detaching from its own label.
  if (nameTag) {
    nameTag.style.transition = `transform ${duration}s linear`;
    nameTag.style.transform = `translate(${dx}px, ${dy}px)`;
  }
  // Scale the leg-swap/hop period to this move's actual speed (1.2s duration
  // = the reference rate the CSS keyframe periods were tuned for), so a slow
  // long glide doesn't strut its legs at the same fixed rate as a quick
  // short hop — that mismatch was the main "it's a flat image sliding, not a
  // figure walking" tell.
  canvas.style.setProperty("--walk-rate", String(duration / 1.2));
  canvas.classList.add("walking");
  clearTimeout(canvas._walkStopTimer);
  canvas._walkStopTimer = setTimeout(() => canvas.classList.remove("walking"), duration * 1000);
}
function scheduleWander(role) {
  const mount = getMountByRole(role);
  if (!mount || scene !== "team" || !wanderRunning) return;
  if (mount.classList.contains("active")) return; // this one is at the table right now
  const state = wanderState[role] || (wanderState[role] = { lastDx: 0, lastDy: 0, timer: null });
  const { minDx, maxDx, minDy, maxDy } = wanderBounds(role);
  const dx = quantize(rand(minDx, maxDx));
  const dy = quantize(rand(minDy, maxDy));
  const face = dx < state.lastDx ? -1 : 1;
  const dist = Math.hypot(dx - state.lastDx, dy - (state.lastDy || 0));
  // A near-constant walking speed (~60px/s), only clamped at the extremes —
  // the old [0.7, 2.4] clamp squeezed every distance the wander range can
  // actually produce (0-~100px) into a narrow band, so a 10px shuffle and a
  // 100px crossing took almost the same time. That inconsistent pace is
  // part of what read as "gliding" instead of "walking."
  const duration = Math.min(2.2, Math.max(0.35, dist / 60));
  moveTo(mount, dx, dy, face, duration);
  state.lastDx = dx;
  state.lastDy = dy;
  state.timer = setTimeout(() => scheduleWander(role), duration * 1000 + rand(400, 2000));
}
function stopWander(role) {
  const state = wanderState[role];
  if (state && state.timer) {
    clearTimeout(state.timer);
    state.timer = null;
  }
}
function startAllWander() {
  if (wanderRunning) return;
  wanderRunning = true;
  TEAM_ROLES.forEach((role, i) => {
    setTimeout(() => scheduleWander(role), i * 350 + rand(0, 400));
  });
}
function stopAllWander() {
  wanderRunning = false;
  TEAM_ROLES.forEach(stopWander);
}
function approachTable(role) {
  stopWander(role);
  const mount = getMountByRole(role);
  const a = APPROACH[role];
  if (mount && a) moveTo(mount, a.dx, a.dy, a.face, 0.5);
}
function resumeWander(role) {
  if (wanderRunning) scheduleWander(role);
}

const els = {
  select: document.getElementById("task-select"),
  kBadge: document.getElementById("task-k-badge"),
  prompt: document.getElementById("task-prompt"),
  bubbleSpeaker: document.getElementById("bubble-speaker"),
  bubbleRound: document.getElementById("bubble-round"),
  bubbleText: document.getElementById("bubble-text"),
  prevBtn: document.getElementById("prev-btn"),
  playBtn: document.getElementById("play-btn"),
  nextBtn: document.getElementById("next-btn"),
  progressDots: document.getElementById("progress-dots"),
  roundIndicator: document.getElementById("round-indicator"),
  gapChip: document.getElementById("gap-chip"),
  scoreBars: document.getElementById("score-bars"),
  blindGuess: document.getElementById("blind-guess"),
  sceneTeam: document.getElementById("scene-team"),
  sceneSolo: document.getElementById("scene-solo"),
  sceneCampaign: document.getElementById("scene-campaign"),
  controlPlate: document.getElementById("control-plate"),
  dialogueBox: document.getElementById("dialogue-box"),
  resultsScreen: document.getElementById("results-screen"),
  transport: document.querySelector(".transport"),
  cartridges: document.querySelectorAll(".cartridge"),
  campaignGrid: document.getElementById("campaign-grid"),
  kBars: document.getElementById("k-bars"),
};

async function init() {
  mountAllSprites();
  captureBaseRects();

  const res = await fetch("/api/tasks");
  allTasksSummary = await res.json();
  els.select.innerHTML = allTasksSummary
    .map((t) => `<option value="${t.id}">${t.id} · ${t.title} (k=${t.k})</option>`)
    .join("");
  els.select.addEventListener("change", () => loadTask(els.select.value));
  els.prevBtn.addEventListener("click", () => step(-1));
  els.nextBtn.addEventListener("click", () => step(1));
  els.playBtn.addEventListener("click", togglePlay);
  els.cartridges.forEach((btn) => btn.addEventListener("click", () => switchScene(btn.dataset.scene)));

  if (allTasksSummary.length) loadTask(allTasksSummary[0].id);
  startAllWander();
}

function switchScene(next) {
  scene = next;
  els.cartridges.forEach((btn) => btn.classList.toggle("active", btn.dataset.scene === next));
  els.sceneTeam.hidden = next !== "team";
  els.sceneSolo.hidden = next !== "solo";
  els.sceneCampaign.hidden = next !== "campaign";

  const isCampaign = next === "campaign";
  els.controlPlate.style.display = isCampaign ? "none" : "block";
  els.dialogueBox.style.display = isCampaign ? "none" : "block";
  els.resultsScreen.style.display = isCampaign ? "none" : "block";
  els.transport.style.display = next === "team" ? "flex" : "none";

  if (next === "team") {
    startAllWander();
  } else {
    stopAllWander();
  }

  if (isCampaign) {
    stopPlay();
    if (!campaignLoaded) loadCampaign();
    return;
  }
  if (!currentTask) return;
  if (next === "solo") {
    stopPlay();
    els.bubbleSpeaker.textContent = "SINGLE_AGENT";
    els.bubbleRound.textContent = "1회 호출";
    typeText(currentTask.conditionA);
  } else {
    showRound(roundIndex);
  }
}

async function loadTask(taskId) {
  stopPlay();
  const res = await fetch(`/api/tasks/${taskId}`);
  currentTask = await res.json();
  roundIndex = -1;

  els.kBadge.textContent = `k=${currentTask.task.k}`;
  els.prompt.textContent = currentTask.task.prompt;

  renderDots();
  clearActiveSprites();
  updateRoundIndicator();
  renderJudge();

  if (scene === "solo") {
    els.bubbleSpeaker.textContent = "SINGLE_AGENT";
    els.bubbleRound.textContent = "1회 호출";
    typeText(currentTask.conditionA);
  } else {
    els.bubbleSpeaker.textContent = "대기 중";
    els.bubbleRound.textContent = "라운드 -";
    typeText("재생을 누르면 팀 논의가 순서대로 출력됩니다.");
  }
}

function clearActiveSprites() {
  document.querySelectorAll(".sprite-mount.active").forEach((s) => {
    s.classList.remove("active");
    if (s.dataset.speaker) resumeWander(s.dataset.speaker);
  });
}

function typeText(text) {
  if (typeTimer) clearInterval(typeTimer);
  els.bubbleText.textContent = "";
  const speed = text.length > 240 ? 4 : 18;
  let i = 0;
  typeTimer = setInterval(() => {
    i += Math.max(1, Math.floor(text.length / 120));
    els.bubbleText.textContent = text.slice(0, i);
    if (i >= text.length) {
      els.bubbleText.textContent = text;
      clearInterval(typeTimer);
      typeTimer = null;
    }
  }, speed);
}

function showRound(idx) {
  if (scene !== "team") return;
  const rounds = currentTask.conditionB.rounds;
  clearActiveSprites();
  if (idx < 0) {
    els.bubbleSpeaker.textContent = "대기 중";
    els.bubbleRound.textContent = "라운드 -";
    typeText("재생을 누르면 팀 논의가 순서대로 출력됩니다.");
    updateRoundIndicator();
    updateDots();
    return;
  }
  const r = rounds[idx];
  const mount = getMountByRole(r.speaker);
  if (mount) mount.classList.add("active");
  approachTable(r.speaker);
  els.bubbleSpeaker.textContent = `${SPEAKER_LABELS[r.speaker] || r.speaker} · ${r.label}`;
  els.bubbleRound.textContent = `라운드 ${r.round} / 4`;
  typeText(r.text);
  updateRoundIndicator();
  updateDots();
}

function renderDots() {
  const total = currentTask ? currentTask.conditionB.rounds.length : 0;
  els.progressDots.innerHTML = Array.from({ length: total }, () => `<span class="dot"></span>`).join("");
}

function updateDots() {
  const dots = els.progressDots.querySelectorAll(".dot");
  dots.forEach((d, i) => {
    d.classList.toggle("done", i < roundIndex);
    d.classList.toggle("current", i === roundIndex);
  });
}

function updateRoundIndicator() {
  const total = currentTask ? currentTask.conditionB.rounds.length : 0;
  els.roundIndicator.textContent = `${roundIndex + 1} / ${total}`;
  els.prevBtn.disabled = roundIndex <= -1;
  els.nextBtn.disabled = !currentTask || roundIndex >= total - 1;
}

function step(delta) {
  if (!currentTask || scene !== "team") return;
  const total = currentTask.conditionB.rounds.length;
  const next = Math.min(Math.max(roundIndex + delta, -1), total - 1);
  if (next === roundIndex) return;
  roundIndex = next;
  showRound(roundIndex);
  if (roundIndex >= total - 1) stopPlay();
}

function togglePlay() {
  if (playTimer) {
    stopPlay();
    return;
  }
  els.playBtn.textContent = "❚❚";
  playTimer = setInterval(() => {
    const total = currentTask.conditionB.rounds.length;
    if (roundIndex >= total - 1) {
      stopPlay();
      return;
    }
    step(1);
  }, 3200);
}

function stopPlay() {
  if (playTimer) {
    clearInterval(playTimer);
    playTimer = null;
  }
  els.playBtn.textContent = "▶";
}

function renderJudge() {
  const j = currentTask.judge;
  const items = [
    ["reagent", "시약 적절성"],
    ["condition", "조건 현실성"],
    ["mechanism", "메커니즘 타당성"],
    ["safety", "안전성"],
  ];
  els.scoreBars.innerHTML =
    `<div class="score-legend">
      <span><span class="legend-dot a"></span>SOLO(A)</span>
      <span><span class="legend-dot b"></span>TEAM(B)</span>
    </div>` +
    items
      .map(([key, label]) => {
        const a = j.scoresA[key];
        const b = j.scoresB[key];
        return `<div class="score-row">
          <span class="label">${label}</span>
          <div class="score-track">
            <div class="score-bar-wrap"><div class="score-bar a" data-w="${(a / 5) * 100}"></div></div>
            <div class="score-bar-wrap"><div class="score-bar b" data-w="${(b / 5) * 100}"></div></div>
          </div>
          <span class="vals">${a.toFixed(1)} / ${b.toFixed(1)}</span>
        </div>`;
      })
      .join("");

  requestAnimationFrame(() => {
    els.scoreBars.querySelectorAll(".score-bar").forEach((bar) => {
      bar.style.width = `${bar.dataset.w}%`;
    });
  });

  els.gapChip.textContent = `GAP ${j.gap >= 0 ? "+" : ""}${j.gap.toFixed(2)} · ${j.gap >= 0 ? "TEAM WINS" : "SOLO WINS"}`;

  els.blindGuess.className = `blind-guess ${j.guessedB ? "caught" : "hidden"}`;
  els.blindGuess.innerHTML = j.guessedB
    ? `⚠️ Judge가 <strong>TEAM(B)을 정확히 식별</strong>했습니다 — 블라인딩이 뚫렸을 가능성이 있습니다.`
    : `✅ Judge가 TEAM(B)을 식별하지 못했습니다 — 블라인딩이 유지됐습니다.`;
}

async function loadCampaign() {
  campaignLoaded = true;
  const statsRes = await fetch("/api/stats");
  const stats = await statsRes.json();

  const full = await Promise.all(allTasksSummary.map((t) => fetch(`/api/tasks/${t.id}`).then((r) => r.json())));

  els.campaignGrid.innerHTML = full
    .map((t) => {
      const g = t.judge.gap;
      const cls = g > 0 ? "win" : g < 0 ? "lose" : "tie";
      return `<div class="campaign-cell ${cls}" title="${t.task.id} gap=${g.toFixed(2)}">${t.task.id.replace("T", "")}</div>`;
    })
    .join("");

  document.getElementById("c-h1").textContent = `${stats.b_wins}/${stats.n}`;
  document.getElementById("c-p1").textContent = stats.wilcoxon_p < 0.001 ? "p<0.001" : `p=${stats.wilcoxon_p.toFixed(3)}`;
  document.getElementById("c-dz").textContent = stats.cohen_dz.toFixed(2);
  document.getElementById("c-slope").textContent = stats.h2_slope.toFixed(3);
  document.getElementById("c-p2").textContent = `p=${stats.h2_p.toFixed(3)}`;
  document.getElementById("c-blind").textContent = `${stats.blind_correct}/${stats.n}`;

  const maxGap = Math.max(...Object.values(stats.by_k).map((v) => v.mean_gap), 0.1);
  els.kBars.innerHTML = [1, 2, 3, 4, 5]
    .map((k) => {
      const v = stats.by_k[String(k)] || stats.by_k[k];
      const pct = Math.max(0, (v.mean_gap / maxGap) * 100);
      return `<div class="k-bar-row">
        <span class="k-label">k=${k}</span>
        <div class="k-bar-track"><div class="k-bar-fill" data-w="${pct}"></div></div>
        <span class="k-val">${v.mean_gap >= 0 ? "+" : ""}${v.mean_gap.toFixed(2)}</span>
      </div>`;
    })
    .join("");

  requestAnimationFrame(() => {
    els.kBars.querySelectorAll(".k-bar-fill").forEach((bar) => {
      bar.style.width = `${bar.dataset.w}%`;
    });
  });
}

init();
