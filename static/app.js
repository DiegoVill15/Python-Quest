import { basicSetup } from "codemirror";
import { EditorView, keymap } from "@codemirror/view";
import { python } from "@codemirror/lang-python";
import { indentUnit } from "@codemirror/language";
import { indentWithTab } from "@codemirror/commands";
import { oneDark } from "@codemirror/theme-one-dark";
import { renderKaykitCharacter } from "./kaykit.js";
import { emblemMarkup } from "./emblems.js";

const $ = (id) => document.getElementById(id);
let worlds = [];
let active = null;
let currentHero;
let previewItemId = null;
let wardrobeView;
const editor = new EditorView({
  parent: $("code-editor"),
  extensions: [basicSetup, python(), oneDark, indentUnit.of("    "), keymap.of([indentWithTab]),
    EditorView.updateListener.of((update) => {
      if (update.docChanged && active?.can_submit)
        localStorage.setItem(`python-quest:draft:${active.id}`, update.state.doc.toString());
    }),
    EditorView.contentAttributes.of({ "aria-label": "Tu solución en Python" })],
});

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", "X-Python-Quest": "1", ...(options.headers || {}) },
    });
  } catch {
    throw new Error("No se pudo conectar con Python Quest. Tu código sigue en el editor; intenta enviarlo otra vez.");
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Ocurrió un error.");
  return data;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function plainFeedback(value) {
  return String(value || "")
    .replace(/`([^`]+)`/g, (_, code) => code.replace(/\\n/g, "\n").split("\n").filter(Boolean).join(" → "))
    .replace(/\\n/g, " ")
    .replace(/\*\*/g, "")
    .replace(/^#{1,6}\s*/gm, "")
    .trim();
}

function notice(message, kind = "error") {
  const box = $("wardrobe-dialog")?.open ? $("wardrobe-notice") : $("ai-dialog")?.open ? $("ai-notice") : $("notice");
  box.textContent = message;
  box.className = `notice ${kind}`;
  box.hidden = false;
  if (kind === "success") setTimeout(() => { box.hidden = true; }, 5000);
}

const SVG = "http://www.w3.org/2000/svg";
const svg = (tag, attrs = {}, text) => {
  const node = document.createElementNS(SVG, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
};
const narrowMap = window.matchMedia("(max-width: 700px)");
let lastProgress = null;
let mapState = null;
let heroLen = null;
let heroFrame = 0;

// Mapa serpenteante: 3 mundos por fila en pantallas anchas, 1 por fila en móviles.
function mapLayout(count, perWorld) {
  const narrow = narrowMap.matches;
  const perRow = (narrow ? 1 : 3) * perWorld;
  const width = narrow ? 360 : 1200;
  const x0 = narrow ? 48 : 100, x1 = width - x0;
  const dx = (x1 - x0) / (perRow - 1);
  const rowH = narrow ? 240 : 312, top = narrow ? 240 : 295;
  const rows = Math.ceil(count * perWorld / perRow);
  const nodes = Array.from({ length: count * perWorld }, (_, k) => {
    const row = Math.floor(k / perRow), j = k % perRow;
    const x = row % 2 ? x1 - j * dx : x0 + j * dx;
    return { x, y: top + row * rowH + Math.sin(k * 0.95) * (narrow ? 12 : 20), row, dir: row % 2 ? -1 : 1 };
  });
  return { nodes, width, height: top + (rows - 1) * rowH + 90, narrow };
}

function smoothPath(points) {
  let d = `M${points[0].x},${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const [p0, p1, p2, p3] = [points[Math.max(i - 1, 0)], points[i], points[i + 1], points[Math.min(i + 2, points.length - 1)]];
    d += `C${p1.x + (p2.x - p0.x) / 6},${p1.y + (p2.y - p0.y) / 6} ${p2.x - (p3.x - p1.x) / 6},${p2.y - (p3.y - p1.y) / 6} ${p2.x},${p2.y}`;
  }
  return d;
}

function renderWorlds(progress) {
  lastProgress = progress;
  const holder = $("map-svg");
  const perWorld = Math.max(...Object.values(progress.world_progress).map((item) => item.total));
  const { nodes, width, height, narrow } = mapLayout(worlds.length, perWorld);
  // Curva de giro entre filas para que el camino no salte en línea recta.
  const route = [];
  nodes.forEach((node, k) => {
    route.push(node);
    const next = nodes[k + 1];
    if (next && next.row !== node.row) {
      const bulge = (narrow ? 34 : 70) * node.dir;
      route.push({ x: node.x + bulge, y: node.y + (next.y - node.y) * 0.3 }, { x: node.x + bulge, y: node.y + (next.y - node.y) * 0.7 });
    }
  });
  const root = svg("svg", { viewBox: `0 0 ${width} ${height}`, class: "map-svg", role: "group", "aria-label": "Mapa de la aventura" });
  const d = smoothPath(route);
  root.append(svg("path", { d, class: "map-road-shadow" }), svg("path", { d, class: "map-road" }));
  const trail = svg("path", { d, class: "map-road-done" });
  root.append(trail, svg("path", { d, class: "map-road-dash" }));

  const heroWorld = worlds.findIndex((w) => { const st = progress.world_progress[w.id]; return st.unlocked && !st.finished; });
  let heroTarget = nodes.length - 1, found = false;
  worlds.forEach((world, index) => {
    const status = progress.world_progress[world.id];
    const group = svg("g", { class: `map-world ${status.unlocked ? "" : "locked"} ${status.finished ? "finished" : ""}`, style: `--world-color:${world.color}` });
    const mid = nodes[index * perWorld + Math.floor(perWorld / 2)];
    const title = world.name;
    const bannerW = Math.min(narrow ? 250 : 236, Math.max(178, title.length * 8.6 + 30));
    // Si el aventurero está justo bajo el cartel, el cartel se corre hacia un lado.
    const heroHere = index === heroWorld && Math.abs(status.completed - Math.floor(perWorld / 2)) <= 1;
    let shift = 0;
    if (heroHere) {
      shift = (narrow ? 70 : 150) * (nodes[heroWorld * perWorld + status.completed].x >= mid.x ? -1 : 1);
    }
    const lx = Math.min(width - bannerW / 2 - 8, Math.max(bannerW / 2 + 8, mid.x + shift));
    const label = svg("g", { class: "map-label", transform: `translate(${lx},${mid.y - (narrow ? 38 : 48)})` });
    const emblem = svg("g", { class: "map-emblem", transform: narrow ? "translate(0,-108) scale(.85)" : "translate(0,-120) scale(1.25)" });
    const float = svg("g", { class: "map-float", style: `animation-delay:${-index * 0.7}s` });
    float.innerHTML = emblemMarkup(world.id, world.color);
    emblem.append(float);
    if (!status.unlocked) emblem.append(svg("image", { href: "/static/assets/kenney/lock.png", x: 12, y: -4, width: 34, height: 34, class: "map-lock" }));
    if (status.finished) {
      const badge = svg("g", { class: "map-badge", transform: "translate(34,-34)" });
      badge.append(svg("circle", { r: 13 }), svg("text", { y: 5 }, "★"));
      emblem.append(badge);
    }
    label.append(emblem);
    const banner = svg("g", { class: "map-banner", transform: "translate(0,-32)" });
    banner.append(
      svg("rect", { class: "map-banner-shadow", x: -bannerW / 2 + 3, y: -39 + 3, width: bannerW, height: 42, rx: 5 }),
      svg("rect", { class: "map-banner-box", x: -bannerW / 2, y: -39, width: bannerW, height: 42, rx: 5 }),
      svg("text", { class: "map-name", y: -20 }, title),
      svg("text", { class: "map-count", y: -6 }, `CAP. ${String(index + 1).padStart(2, "0")} · ${status.completed} / ${status.total} MISIONES`),
    );
    label.append(banner);
    group.append(label);
    for (let stage = 0; stage < perWorld; stage++) {
      const k = index * perWorld + stage;
      const node = nodes[k];
      const done = stage < status.completed;
      const current = status.unlocked && !status.finished && stage === status.completed;
      if (current && !found) { heroTarget = k; found = true; }
      const playable = current;
      const g = svg("g", { class: `map-node ${done ? "done" : current ? "current" : "future"}`, transform: `translate(${node.x},${node.y})` });
      if (playable) {
        g.setAttribute("role", "button");
        g.setAttribute("tabindex", "0");
        g.setAttribute("aria-label", `${status.active_id ? "Continuar" : "Empezar"} misión ${stage + 1} de ${world.name}`);
        const go = () => newChallenge(world.id, null);
        g.addEventListener("click", go);
        g.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); go(); } });
        g.append(svg("circle", { r: narrow ? 20 : 22, class: "map-pulse" }));
      }
      g.append(svg("circle", { r: narrow ? 13 : 14, class: "map-dot" }),
        svg("text", { class: "map-num", y: 5 }, done ? "✓" : String(stage + 1)));
      g.append(svg("title", {}, `${world.name} · misión ${stage + 1}${done ? " (completada)" : ""}`));
      group.append(g);
    }
    if (status.unlocked && (status.completed || status.active_id)) {
      const reset = svg("g", { class: "map-reset", role: "button", tabindex: "0", transform: "translate(0,-6)", "aria-label": `Reiniciar ${world.name}` });
      const doReset = () => resetWorld(world.id, world.name);
      reset.addEventListener("click", doReset);
      reset.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); doReset(); } });
      reset.append(svg("rect", { class: "map-reset-box", x: -78, y: -15, width: 156, height: 24, rx: 12 }),
        svg("path", { class: "map-reset-icon", d: "M-62,-4 a5.5,5.5 0 1 1 1.6,3.9 M-62,-9.5 v5.5 h5.5" }),
        svg("text", { class: "map-reset-text", x: -49, y: 1 }, "Reiniciar aldea"));
      label.append(reset);
    }
    root.append(group);
  });
  holder.replaceChildren(root);

  // Longitud sobre el camino de cada nodo, para que el héroe camine por el sendero.
  const road = trail;
  const total = road.getTotalLength();
  const lengths = [];
  let from = 0;
  nodes.forEach((node) => {
    let best = from, bestDist = Infinity;
    for (let len = from; len <= total; len += 3) {
      const point = road.getPointAtLength(len);
      const dist = (point.x - node.x) ** 2 + (point.y - node.y) ** 2;
      if (dist < bestDist) { bestDist = dist; best = len; } else if (dist > bestDist + 4000) break;
    }
    lengths.push(best);
    from = best;
  });
  mapState = { road, lengths, width, height, target: heroTarget, nodes, perWorld };
  const doneLength = progress.campaign_complete ? total : lengths[heroTarget];
  trail.style.strokeDasharray = `${doneLength} ${total}`;
}

// Coloca o anima al aventurero personalizado sobre el nodo actual del mapa.
function updateMapHero(hero) {
  if (!mapState) return;
  const view = renderKaykitCharacter($("map-hero"), hero);
  const { road, lengths, width, height, target } = mapState;
  const place = (len) => {
    heroLen = len;
    const point = road.getPointAtLength(len);
    $("map-hero").style.left = `${(point.x / width) * 100}%`;
    $("map-hero").style.top = `${(point.y / height) * 100}%`;
    return point;
  };
  const face = (angle) => view.rotate(angle - view.character.rotation.y);
  cancelAnimationFrame(heroFrame);
  const goal = lengths[target];
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const start = heroLen ?? goal, distance = Math.abs(goal - start);
  if (distance < 1 || reduced) {
    place(goal);
    $("map-hero").classList.remove("walking");
    return;
  }
  const duration = Math.min(2600, Math.max(700, distance * 5));
  const sign = goal >= start ? 1 : -1;
  const begin = performance.now();
  const step = (now) => {
    const t = Math.min(1, (now - begin) / duration);
    const eased = t < 0.5 ? 2 * t * t : 1 - ((-2 * t + 2) ** 2) / 2;
    const len = start + (goal - start) * eased;
    const point = place(len);
    const ahead = road.getPointAtLength(Math.max(0, len + sign * 4));
    const dx = (ahead.x - point.x) * sign;
    face(dx > 0.4 ? 1.1 : dx < -0.4 ? -1.1 : 0);
    $("map-hero").classList.toggle("walking", t < 1);
    if (t < 1) heroFrame = requestAnimationFrame(step);
    else face(0);
  };
  $("map-hero").classList.add("walking");
  heroFrame = requestAnimationFrame(step);
}

narrowMap.addEventListener("change", () => {
  if (!lastProgress) return;
  heroLen = null;
  renderWorlds(lastProgress);
  if (currentHero) updateMapHero(currentHero);
});

function renderProgress(data) {
  worlds = data.worlds;
  const progress = data.progress;
  $("campaign-heading").textContent = `✦ CRÓNICAS DEL CÓDIGO · CAMPAÑA DE ${progress.total_missions} MISIONES`;
  $("campaign-description").textContent = `${worlds.length} mundos te esperan. Aprende Python misión a misión, domina cada desafío y escribe tu propia leyenda.`;
  $("world-count").textContent = `01 — ${String(worlds.length).padStart(2, "0")} · MUNDOS`;
  $("level").textContent = progress.level;
  $("xp").textContent = progress.xp;
  $("completed").textContent = `${progress.completed} / ${progress.total_missions}`;
  const usage = data.ai_usage;
  const formatTokens = (value) => value.toLocaleString("es-MX");
  $("ai-tokens").textContent = formatTokens(usage.input_tokens + usage.output_tokens);
  $("ai-usage-detail").textContent = `${formatTokens(usage.input_tokens)} de entrada (${formatTokens(usage.cached_input_tokens)} reutilizados), ${formatTokens(usage.output_tokens)} de salida · ${usage.calls} ${usage.calls === 1 ? "llamada medida" : "llamadas medidas"}. Desde que se activó el contador; incluye creación y revisión de misiones.`;
  $("victory").hidden = !progress.campaign_complete;
  renderWorlds(progress);
  renderHero(data.hero);
  updateMapHero(data.hero);

  const recent = $("recent");
  recent.replaceChildren();
  if (!data.recent.length) recent.append(el("p", "empty", "Tu historia comienza con la primera misión."));
  data.recent.forEach((item) => {
    const row = el("button", "recent-item");
    row.type = "button";
    row.append(el("span", "recent-icon", "◆"), el("span", "recent-title", item.title),
      el("span", "", item.can_submit ? "Continuar →" : "Ver archivo →"));
    row.addEventListener("click", () => openChallenge(item.id));
    recent.append(row);
  });

  const trophies = $("trophies");
  trophies.replaceChildren();
  if (!progress.trophies.length) trophies.append(el("p", "empty", "Los trofeos aparecerán aquí."));
  progress.trophies.forEach((trophy) => {
    const row = el("div", "trophy-item");
    const copy = el("div");
    copy.append(el("strong", "", trophy.name), el("small", "", trophy.detail));
    row.append(el("span", "trophy-icon", trophy.icon), copy);
    trophies.append(row);
  });
}

function renderWardrobePreview() {
  if (!currentHero) return;
  const item = currentHero.items.find((entry) => entry.id === previewItemId);
  const equipped = item ? { ...currentHero.equipped, [item.slot]: item.id } : currentHero.equipped;
  wardrobeView = renderKaykitCharacter($("wardrobe-character"), { ...currentHero, equipped });
  $("preview-label").textContent = item ? `Vista previa 3D: ${item.name} · arrastra para girar` : "Tu equipo actual · arrastra para girar";
  $("preview-reset").hidden = !item;
  $("shop-items").querySelectorAll(".shop-card").forEach((card) => card.classList.toggle("previewing", card.dataset.itemId === previewItemId));
}

function renderHero(hero) {
  currentHero = hero;
  $("hero-name").textContent = hero.name;
  $("hero-coins").textContent = hero.coins;
  $("hero-name-input").value = hero.name;
  const appearance = $("hero-appearance");
  if (!appearance.options.length) {
    Object.entries(hero.appearances).forEach(([value, label]) => appearance.add(new Option(label, value)));
  }
  appearance.value = hero.appearance;
  renderKaykitCharacter($("hero-character"), hero, (preview) => {
    $("top-avatar").style.backgroundImage = `url(${preview})`;
    $("top-avatar").textContent = "";
  });
  const shop = $("shop-items");
  shop.replaceChildren();
  hero.items.forEach((item) => {
    const owned = hero.owned.includes(item.id);
    const equipped = hero.equipped[item.slot] === item.id;
    const card = el("article", `shop-card ${item.unlocked ? "" : "shop-locked"} ${item.rarity === "Legendario" ? "legendary" : item.rarity === "Mítico" ? "mythic" : ""}`);
    card.dataset.itemId = item.id;
    const info = el("div", "shop-info");
    info.append(el("small", "shop-rarity", `${item.rarity.toUpperCase()} · ${{ head: "CABEZA", body: "CUERPO", back: "ESPALDA", hand: "MANO" }[item.slot]}`), el("h3", "", item.name),
      el("p", "", item.unlocked ? `${item.price} monedas · ${item.requirement}` : `🔒 ${item.requirement}`));
    const preview = el("button", "shop-preview", "Ver en 3D");
    preview.type = "button";
    preview.setAttribute("aria-label", `Ver ${item.name} en el personaje 3D`);
    preview.addEventListener("click", () => { previewItemId = item.id; renderWardrobePreview(); });
    const action = el("button", "shop-action", equipped ? "Quitar" : owned ? "Equipar" : !item.unlocked ? "Bloqueado" : hero.coins < item.price ? "Faltan monedas" : `Comprar · ${item.price}`);
    action.type = "button";
    action.disabled = !owned && (!item.unlocked || hero.coins < item.price);
    if (item.unlocked && !owned && hero.coins < item.price) action.title = "Te faltan monedas";
    action.addEventListener("click", async () => {
      action.disabled = true;
      try {
        const path = owned ? "/api/hero/equipment" : "/api/hero/purchase";
        const body = owned ? { slot: item.slot, item_id: equipped ? null : item.id } : { item_id: item.id };
        renderProgress(await api(path, { method: owned ? "PUT" : "POST", body: JSON.stringify(body) }));
        notice(owned ? equipped ? `${item.name} guardado.` : `${item.name} equipado.` : `${item.name} comprado y equipado.`, "success");
      } catch (error) {
        notice(error.message);
        action.disabled = false;
      }
    });
    card.append(info, preview, action);
    shop.append(card);
  });
  renderWardrobePreview();
}

for (const id of ["wardrobe-open", "avatar-open"]) $(id).addEventListener("click", () => $("wardrobe-dialog").showModal());
$("wardrobe-dialog").addEventListener("close", () => { previewItemId = null; renderWardrobePreview(); });
$("preview-reset").addEventListener("click", () => { previewItemId = null; renderWardrobePreview(); });
$("rotate-left").addEventListener("click", () => wardrobeView?.rotate(-Math.PI / 4));
$("rotate-right").addEventListener("click", () => wardrobeView?.rotate(Math.PI / 4));

$("hero-name-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("hero-name-form").querySelector("button");
  button.disabled = true;
  try {
    renderProgress(await api("/api/hero/name", { method: "PUT", body: JSON.stringify({ name: $("hero-name-input").value }) }));
    notice("Nombre guardado.", "success");
  } catch (error) { notice(error.message); }
  finally { button.disabled = false; }
});

$("hero-appearance").addEventListener("change", async (event) => {
  const select = event.currentTarget;
  select.disabled = true;
  try {
    renderProgress(await api("/api/hero/appearance", { method: "PUT", body: JSON.stringify({ appearance: select.value }) }));
    notice("Aspecto guardado.", "success");
  } catch (error) { notice(error.message); }
  finally { select.disabled = false; }
});

function missionSection(label, value, legacy = false) {
  if (!value) return null;
  const section = el("section", "mission-section");
  section.append(el("h3", "", label));
  const paragraphs = legacy ? value.split(/(?<=\.)\s+(?=[A-ZÁÉÍÓÚ])/u) : [value];
  paragraphs.forEach((paragraph) => section.append(el("p", "", paragraph)));
  return section;
}

function setCode(value) {
  editor.dispatch({ changes: { from: 0, to: editor.state.doc.length, insert: value || "" } });
}

function showChallenge(challenge) {
  if (active?.id === challenge.id && active.can_submit) {
    $("quest-panel").scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }
  active = challenge;
  const world = worlds.find((item) => item.id === challenge.world_id);
  $("quest-world").textContent = world ? world.name.toUpperCase() : "MISIÓN";
  $("quest-stage").textContent = `MISIÓN ${challenge.stage} / ${challenge.total_stages} · ${challenge.focus}`;
  $("quest-title").textContent = challenge.title;
  $("quest-story").textContent = challenge.story;
  $("quest-badge").textContent = challenge.can_submit ? "MISIÓN ACTIVA" : "ARCHIVO";
  const lesson = $("lesson");
  lesson.hidden = !challenge.lesson;
  if (challenge.lesson) {
    lesson.open = true;
    $("lesson-title").textContent = `📖 Antes de empezar · ${challenge.lesson.title}`;
    $("lesson-explanation").textContent = challenge.lesson.explanation;
    $("lesson-input").textContent = challenge.lesson.input;
    $("lesson-code").textContent = challenge.lesson.code;
    $("lesson-output").textContent = challenge.lesson.output;
  }
  const task = $("quest-task");
  task.replaceChildren();
  for (const section of [
    missionSection("Objetivo", challenge.objective, !challenge.input_format && !challenge.output_format),
    missionSection("Entrada", challenge.input_format),
    missionSection("Salida", challenge.output_format),
  ]) if (section) task.append(section);
  if (challenge.rules?.length) {
    const section = el("section", "mission-section");
    section.append(el("h3", "", "Reglas"));
    const list = el("ul");
    challenge.rules.forEach((rule) => list.append(el("li", "", rule)));
    section.append(list);
    task.append(section);
  }
  setCode(challenge.can_submit ? localStorage.getItem(`python-quest:draft:${challenge.id}`) || "" : "");
  $("hint").textContent = challenge.hint;
  $("hint").hidden = true;
  $("hint-button").hidden = false;
  $("feedback").hidden = true;
  $("run-result").hidden = true;
  $("run-input").value = "";
  $("run-button").disabled = !challenge.can_submit;
  $("submit-button").disabled = !challenge.can_submit;
  $("archive-note").hidden = challenge.can_submit;
  $("learning-note").hidden = !challenge.last_mistake;
  $("learning-note-text").textContent = plainFeedback(challenge.last_mistake);
  const examples = $("examples");
  examples.replaceChildren();
  challenge.examples.forEach((example, index) => {
    const box = el("div", "example");
    box.append(el("span", "example-number", `EJEMPLO ${index + 1}`), el("small", "", "ENTRADA"),
      el("pre", "", example.input || "(vacía)"), el("small", "", "SALIDA"), el("pre", "", example.expected));
    if (challenge.can_submit) {
      const use = el("button", "example-use", "Usar esta entrada");
      use.type = "button";
      use.addEventListener("click", () => {
        $("run-input").value = example.input;
        $("run-input").focus();
      });
      box.append(use);
    }
    examples.append(box);
  });
  $("quest-panel").hidden = false;
  $("quest-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function refresh() {
  const data = await api("/api/progress");
  renderProgress(data);
  return data;
}

async function newChallenge(worldId, button) {
  const label = button?.textContent;
  if (button) { button.disabled = true; button.textContent = "Creando misión…"; }
  try {
    showChallenge(await api("/api/challenges", { method: "POST", body: JSON.stringify({ world_id: worldId }) }));
    await refresh();
    renderPreferences(await api("/api/preferences"));
  } catch (error) {
    notice(error.message);
  } finally {
    if (button) { button.disabled = false; button.textContent = label; }
  }
}

async function openChallenge(id) {
  try { showChallenge(await api(`/api/challenges/${encodeURIComponent(id)}`)); }
  catch (error) { notice(error.message); }
}

async function resetWorld(worldId, name) {
  if (!window.confirm(`¿Reiniciar ${name}? Volverás a la misión 1. Conservarás XP, trofeos y mundos desbloqueados.`)) return;
  try {
    renderProgress(await api(`/api/worlds/${encodeURIComponent(worldId)}/reset`, { method: "POST" }));
    if (active?.world_id === worldId) { active = null; $("quest-panel").hidden = true; }
    notice(`${name} está lista para una nueva partida.`, "success");
  } catch (error) { notice(error.message); }
}

function renderFeedback(data) {
  const box = $("feedback");
  box.className = `feedback ${data.passed ? "passed" : "failed"}`;
  box.replaceChildren();
  const heading = el("div", "feedback-heading");
  heading.append(el("span", "feedback-symbol", data.passed ? "✦" : "↻"),
    el("h3", "", data.passed ? "¡Misión completada!" : data.syntax_error ? "Error de sintaxis" : "Aún puedes mejorar"));
  if (data.xp_gained) heading.append(el("span", "xp-award", `+${data.xp_gained} XP`));
  if (data.coins_gained) heading.append(el("span", "coin-award", `+${data.coins_gained} monedas`));
  box.append(heading, el("p", "", plainFeedback(data.review.note)),
    el("p", "improvement", `Consejo: ${plainFeedback(data.review.improvement)}`));
  const list = el("div", "test-list");
  data.results.forEach((result) => {
    const row = el("div", `test-item ${result.passed ? "ok" : "bad"} ${!result.passed ? "explained" : ""}`);
    row.append(el("span", "", `${result.passed ? "✓" : "×"} Prueba ${result.number}${result.number > 2 ? " · caso adicional" : ""}`));
    if (!result.passed) {
      const comparison = el("div", "test-comparison");
      for (const [label, value] of [
        ["Entrada", result.input || "(vacía)"],
        ["Se esperaba", result.expected || "(sin salida)"],
        ["Tu programa mostró", result.error || result.actual || "(sin salida)"],
      ]) {
        const column = el("div");
        column.append(el("strong", "", label), el("pre", "", value));
        comparison.append(column);
      }
      row.append(comparison);
    }
    list.append(row);
  });
  if (data.results.length) box.append(list);
  if (data.passed) {
    active.can_submit = false;
    $("run-button").disabled = true;
    $("submit-button").disabled = true;
    const wardrobe = el("button", "wardrobe-reward-link", "Ver equipo y guardarropa →");
    wardrobe.type = "button";
    wardrobe.addEventListener("click", () => $("wardrobe-dialog").showModal());
    box.append(wardrobe);
    if (data.next_world_id) {
      const next = el("button", "primary-button next-button",
        data.next_world_id === active.world_id ? "Siguiente misión →" : "Continuar al siguiente mundo →");
      next.type = "button";
      next.addEventListener("click", () => newChallenge(data.next_world_id, next));
      box.append(next);
    } else {
      box.append(el("p", "victory-line", "¡Campaña completada! Eres una leyenda de Python."));
      const map = el("button", "primary-button next-button", "Ver mapa y trofeos →");
      map.addEventListener("click", () => $("worlds-title").scrollIntoView({ behavior: "smooth" }));
      box.append(map);
    }
  }
  box.hidden = false;
  box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

$("hint-button").addEventListener("click", () => {
  $("hint").hidden = false;
  $("hint-button").hidden = true;
});

$("run-button").addEventListener("click", async () => {
  if (!active?.can_submit) return;
  const button = $("run-button");
  button.disabled = true;
  button.textContent = "Ejecutando…";
  try {
    const result = await api("/api/run", { method: "POST", body: JSON.stringify({
      source: editor.state.doc.toString(), stdin: $("run-input").value,
    }) });
    const panel = $("run-result");
    panel.replaceChildren(el("strong", "", result.error ? "Error al ejecutar" : "Salida del programa"),
      el("pre", "", result.stdout || "(sin salida)"));
    if (result.error) panel.append(el("pre", "run-error", result.error));
    panel.hidden = false;
  } catch (error) {
    notice(error.message);
  } finally {
    button.disabled = !active?.can_submit;
    button.textContent = "Ejecutar";
  }
});

$("submit-button").addEventListener("click", async () => {
  if (!active?.can_submit) return;
  const button = $("submit-button");
  button.disabled = true;
  button.textContent = "Revisando…";
  try {
    const data = await api(`/api/challenges/${active.id}/submit`, {
      method: "POST", body: JSON.stringify({ source: editor.state.doc.toString() }),
    });
    renderFeedback(data);
    await refresh();
  } catch (error) {
    notice(error.message);
  } finally {
    button.disabled = !active?.can_submit;
    button.textContent = "Enviar solución ➜";
  }
});

function renderPreferences(memory) {
  $("preferences-summary").textContent = memory.summary || "Todavía no hay preferencias resumidas.";
  const count = memory.pending.length;
  $("preferences-pending").textContent = count
    ? `${count} comentario${count === 1 ? "" : "s"} pendiente${count === 1 ? "" : "s"} de resumir al crear la siguiente misión.`
    : "No hay comentarios pendientes.";
}

$("preference-save").addEventListener("click", async () => {
  const field = $("preference-note");
  const button = $("preference-save");
  button.disabled = true;
  try {
    renderPreferences(await api("/api/preferences", { method: "POST", body: JSON.stringify({ note: field.value }) }));
    field.value = "";
    notice("Comentario guardado para la siguiente misión.", "success");
  } catch (error) {
    notice(error.message);
  } finally {
    button.disabled = false;
  }
});

$("preference-clear").addEventListener("click", async () => {
  if (!window.confirm("¿Borrar todas tus preferencias de aprendizaje?")) return;
  try {
    renderPreferences(await api("/api/preferences", { method: "DELETE" }));
    notice("Preferencias borradas.", "success");
  } catch (error) {
    notice(error.message);
  }
});

api("/api/preferences").then(renderPreferences).catch((error) => notice(error.message));

$("ai-open").addEventListener("click", () => {
  $("ai-dialog").showModal();
  if (aiState) loadAiModels();
});

let aiState;
let aiModelRequest = 0;

function toggleManualModel() {
  const manual = $("ai-model").value === "";
  $("ai-model-manual").hidden = !manual;
  $("ai-model-manual-label").hidden = !manual;
}

async function loadAiModels(selectedModel = $("ai-model").value || $("ai-model-manual").value) {
  const request = ++aiModelRequest;
  const connectionId = $("ai-connection").value;
  const select = $("ai-model");
  select.replaceChildren(el("option", "", "Cargando modelos…"));
  select.disabled = true;
  $("ai-save").disabled = true;
  $("ai-model-manual").hidden = true;
  $("ai-model-manual-label").hidden = true;
  $("ai-help").textContent = "Consultando los modelos del proveedor…";
  try {
    const data = await api(`/api/ai/connections/${encodeURIComponent(connectionId)}/models`);
    if (request !== aiModelRequest) return;
    const models = [...new Set(data.models)];
    if (selectedModel && !models.includes(selectedModel)) models.unshift(selectedModel);
    select.replaceChildren(...models.map((model) => {
      const option = el("option", "", model);
      option.value = model;
      return option;
    }));
    const manual = el("option", "", "Escribir ID manualmente…");
    manual.value = "";
    select.append(manual);
    select.value = selectedModel || models[0] || "";
    $("ai-help").textContent = data.models.length
      ? "Puedes abrir la lista y cambiar de modelo cuando quieras. Pulsa «Usar este modelo» para guardar."
      : "El proveedor no devolvió modelos. Puedes escribir un ID manualmente.";
    if (aiState.connections.find((item) => item.id === connectionId)?.provider === "openrouter")
      $("ai-help").textContent += " OpenRouter lista modelos gratis, sujetos a límites. Un ID manual puede corresponder a un modelo de pago.";
  } catch (error) {
    if (request !== aiModelRequest) return;
    const manual = el("option", "", "Escribir ID manualmente…");
    manual.value = "";
    select.replaceChildren(manual);
    $("ai-model-manual").value = selectedModel;
    $("ai-help").textContent = `${error.message} Vuelve a seleccionar el proveedor para reintentar.`;
  } finally {
    if (request === aiModelRequest) {
      select.disabled = false;
      $("ai-save").disabled = false;
      toggleManualModel();
    }
  }
}

$("ai-model").addEventListener("change", toggleManualModel);

function renderAi(data) {
  aiState = data;
  const select = $("ai-connection");
  select.replaceChildren();
  data.connections.forEach((item) => {
    const option = el("option", "", `${item.label}${item.available === false ? " · CLI no instalada" : ""}`);
    option.value = item.id;
    select.append(option);
  });
  select.value = data.selection.id;
  const model = el("option", "", data.selection.model);
  model.value = data.selection.model;
  $("ai-model").replaceChildren(model);
  $("ai-model-manual").value = data.selection.model;
  $("ai-remove").hidden = !data.connections.some((item) => item.id === select.value && item.kind === "api");
  if ($("ai-dialog").open) loadAiModels(data.selection.model);
}

$("ai-connection").addEventListener("change", () => {
  const item = aiState.connections.find((entry) => entry.id === $("ai-connection").value);
  $("ai-remove").hidden = item?.kind !== "api";
  const model = item?.id === aiState.selection.id ? aiState.selection.model : "";
  $("ai-model-manual").value = model;
  loadAiModels(model);
});

function updateAiProvider() {
  const provider = $("ai-provider").value;
  const compatible = provider === "compatible";
  $("ai-endpoint").hidden = !compatible;
  $("ai-endpoint").previousElementSibling.hidden = !compatible;
  const help = {
    ollama: ["Conecta tu cuenta de Ollama Cloud. Free incluye uso inicial limitado; los modelos disponibles dependen de tu plan y saldo.", "https://ollama.com/settings/keys"],
    openrouter: ["La lista mostrará modelos gratis. Necesitas una clave API de OpenRouter; se aplican límites de uso.", "https://openrouter.ai/settings/keys"],
  }[provider];
  $("ai-provider-help").textContent = help?.[0] || "La clave se guardará en el llavero de este equipo.";
  $("ai-key-link").hidden = !help;
  if (help) $("ai-key-link").href = help[1];
}
$("ai-provider").addEventListener("change", updateAiProvider);
updateAiProvider();

$("ai-save").addEventListener("click", async () => {
  try {
    renderAi(await api("/api/ai/selection", { method: "PUT", body: JSON.stringify({
      id: $("ai-connection").value, model: ($("ai-model").value || $("ai-model-manual").value).trim(),
    }) }));
    notice("Modelo seleccionado para las próximas misiones.", "success");
  } catch (error) { notice(error.message); }
});

$("ai-add").addEventListener("click", async () => {
  const button = $("ai-add");
  button.disabled = true;
  try {
    const data = await api("/api/ai/connections", { method: "POST", body: JSON.stringify({
      provider: $("ai-provider").value, label: $("ai-label").value.trim(),
      endpoint: $("ai-endpoint").value.trim(), token: $("ai-token").value,
    }) });
    const added = data.connections.at(-1);
    renderAi(data);
    $("ai-connection").value = added.id;
    $("ai-connection").dispatchEvent(new Event("change"));
    $("ai-token").value = "";
    notice("Conexión guardada. Elige un modelo para usarla.", "success");
  } catch (error) { notice(error.message); }
  finally { button.disabled = false; }
});

$("ai-remove").addEventListener("click", async () => {
  if (!window.confirm("¿Quitar esta conexión y su clave API?")) return;
  try {
    renderAi(await api(`/api/ai/connections/${encodeURIComponent($("ai-connection").value)}`, { method: "DELETE" }));
    notice("Conexión eliminada.", "success");
  } catch (error) { notice(error.message); }
});

api("/api/ai").then(renderAi).catch((error) => notice(error.message));

refresh().then((data) => {
  const current = worlds.find((world) => data.progress.world_progress[world.id].active_id);
  if (current) openChallenge(data.progress.world_progress[current.id].active_id);
}).catch((error) => notice(error.message));
