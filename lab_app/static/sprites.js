/* Team roles use real CC0 pixel-art character sprites (Kenney "RPG Urban Pack",
   kenney.nl, CC0) — 16x16 down-facing walk frames, cropped straight from the
   pack's tilemap. This replaces the earlier hand-drawn bitmap humans, which
   read as flat/paper-like next to genuine sprite-sheet art.
   The solo-agent robot has no equivalent in that pack, so it stays hand-drawn
   on <canvas> exactly as before. */

const ROLE_SPRITE_FILES = {
  pi: ['pi_0.png', 'pi_1.png'],
  synthetic_chemist: ['synthetic_chemist_0.png', 'synthetic_chemist_1.png'],
  mechanistic_chemist: ['mechanistic_chemist_0.png', 'mechanistic_chemist_1.png'],
  safety_specialist: ['safety_specialist_0.png', 'safety_specialist_1.png'],
  critic: ['critic_0.png', 'critic_1.png'],
};
const HUMAN_PX = 6; // 16px source * 6 = 96px on screen, crisp nearest-neighbor

const ROBOT_PALETTE = { k: '#0a1310', g: '#39ffb4', m: '#9aa6b8', d: '#3a4048' };
const ROBOT_A = [
  ['.', '.', '.', '.', 'd', 'd', '.', '.', '.', '.'],
  ['.', '.', '.', '.', 'g', 'g', '.', '.', '.', '.'],
  ['.', '.', 'k', 'k', 'k', 'k', 'k', 'k', '.', '.'],
  ['.', '.', 'k', 'g', 'g', 'g', 'g', 'k', '.', '.'],
  ['.', '.', 'k', 'g', 'k', 'k', 'g', 'k', '.', '.'],
  ['.', '.', 'k', 'g', 'g', 'g', 'g', 'k', '.', '.'],
  ['.', '.', 'k', 'k', 'k', 'k', 'k', 'k', '.', '.'],
  ['.', 'k', 'm', 'm', 'm', 'm', 'm', 'm', 'k', '.'],
  ['.', 'k', 'm', 'm', 'm', 'm', 'm', 'm', 'k', '.'],
  ['.', 'k', 'm', 'm', 'm', 'm', 'm', 'm', 'k', '.'],
  ['.', 'k', 'm', 'm', 'm', 'm', 'm', 'm', 'k', '.'],
  ['.', 'k', 'k', 'k', 'k', 'k', 'k', 'k', 'k', '.'],
  ['.', '.', '.', 'd', 'd', 'd', 'd', '.', '.', '.'],
  ['.', '.', 'd', 'd', 'd', 'd', 'd', 'd', '.', '.'],
];
const ROBOT_B = ROBOT_A.map((row) => row.slice());
ROBOT_B[4] = ['.', '.', 'k', 'g', 'g', 'g', 'g', 'k', '.', '.']; // blink

function renderSpriteCanvas(grid, palette, px) {
  // A real <canvas>, drawn 1 device-independent unit per cell and then
  // upscaled with image-rendering:pixelated — guaranteed nearest-neighbor,
  // zero antialiasing, on every engine.
  const h = grid.length;
  const w = grid[0].length;
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  canvas.style.width = `${w * px}px`;
  canvas.style.height = `${h * px}px`;
  canvas.style.imageRendering = 'pixelated';
  canvas.style.display = 'block';
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const c = grid[y][x];
      if (c === '.') continue;
      ctx.fillStyle = palette[c] || '#ff00ff';
      ctx.fillRect(x, y, 1, 1);
    }
  }
  return canvas;
}

function makeSpriteImg(src, px) {
  const img = document.createElement('img');
  img.src = src;
  img.width = 16;
  img.height = 16;
  img.style.width = `${16 * px}px`;
  img.style.height = `${16 * px}px`;
  img.style.imageRendering = 'pixelated';
  img.style.display = 'block';
  img.alt = '';
  return img;
}

function mountSprite(el, role) {
  el.innerHTML = '<div class="frame frame-a"></div><div class="frame frame-b"></div>';
  if (role === 'robot') {
    el.querySelector('.frame-a').appendChild(renderSpriteCanvas(ROBOT_A, ROBOT_PALETTE, 7));
    el.querySelector('.frame-b').appendChild(renderSpriteCanvas(ROBOT_B, ROBOT_PALETTE, 7));
    return;
  }
  const [fileA, fileB] = ROLE_SPRITE_FILES[role];
  el.querySelector('.frame-a').appendChild(makeSpriteImg(`/static/sprites/${fileA}`, HUMAN_PX));
  el.querySelector('.frame-b').appendChild(makeSpriteImg(`/static/sprites/${fileB}`, HUMAN_PX));
}

function mountAllSprites() {
  document.querySelectorAll('.sprite-canvas').forEach((el) => {
    mountSprite(el, el.dataset.role);
  });
}
