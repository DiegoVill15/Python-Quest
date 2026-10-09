import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const ASSETS = "/static/assets/kaykit/";
const MODELS = ["Barbarian", "Knight", "Mage", "Ranger", "Rogue", "Rogue_Hooded"];
const views = new WeakMap();

function crown() {
  const gold = new THREE.MeshStandardMaterial({ color: 0xf8cc60, metalness: 0.45, roughness: 0.35 });
  const group = new THREE.Group();
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.40, 0.14, 8, 1, true), gold);
  group.add(ring);
  for (let i = 0; i < 8; i++) {
    const angle = i * Math.PI / 4;
    const point = new THREE.Mesh(new THREE.ConeGeometry(0.085, i % 2 ? 0.18 : 0.25, 4), gold);
    point.position.set(Math.sin(angle) * 0.41, 0.15, Math.cos(angle) * 0.41);
    group.add(point);
  }
  group.position.y = 0.95;
  return group;
}

function compass() {
  const group = new THREE.Group();
  const gold = new THREE.MeshStandardMaterial({ color: 0xdcae55, metalness: 0.55, roughness: 0.3 });
  const face = new THREE.MeshStandardMaterial({ color: 0xf8edc9, roughness: 0.7 });
  group.add(new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 0.055, 20), gold));
  const dial = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.058, 20), face);
  group.add(dial);
  const needle = new THREE.Mesh(new THREE.ConeGeometry(0.045, 0.17, 3),
    new THREE.MeshStandardMaterial({ color: 0xc85447 }));
  needle.rotation.z = Math.PI / 2;
  needle.position.y = 0.055;
  group.add(needle);
  group.rotation.x = Math.PI / 2;
  group.position.set(0, -0.04, 0.23);
  return group;
}

function aura() {
  const group = new THREE.Group();
  const material = new THREE.MeshBasicMaterial({ color: 0xb89aff, transparent: true, opacity: 0.57, side: THREE.DoubleSide, depthWrite: false });
  for (const [radius, y, tilt] of [[0.63, 0.18, 0.2], [0.82, 0.72, -0.2]]) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(radius, 0.024, 8, 64), material);
    ring.rotation.x = Math.PI / 2 + tilt;
    ring.position.y = y;
    group.add(ring);
  }
  return group;
}

class CharacterView {
  constructor(target, onSnapshot) {
    this.target = target;
    this.onSnapshot = onSnapshot;
    this.hero = null;
    this.visible = false;
    this.clock = new THREE.Clock();
    this.scene = new THREE.Scene();
    this.character = new THREE.Group();
    this.scene.add(this.character);
    this.scene.add(new THREE.HemisphereLight(0xfff1d1, 0x46616e, 2.6));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(2, 4, 4);
    this.scene.add(key);
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.01, 100);
    this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, preserveDrawingBuffer: Boolean(onSnapshot) });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.domElement.setAttribute("aria-hidden", "true");
    this.renderer.domElement.addEventListener("pointerdown", (event) => {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      this.dragX = event.clientX;
      this.renderer.domElement.setPointerCapture(event.pointerId);
    });
    this.renderer.domElement.addEventListener("pointermove", (event) => {
      if (this.dragX === undefined) return;
      this.rotate((event.clientX - this.dragX) * 0.012);
      this.dragX = event.clientX;
    });
    this.renderer.domElement.addEventListener("pointerup", () => { this.dragX = undefined; });
    this.renderer.domElement.addEventListener("pointercancel", () => { this.dragX = undefined; });
    target.replaceChildren(this.renderer.domElement);
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(target);
    this.observer = new IntersectionObserver(([entry]) => { this.visible = entry.isIntersecting; if (this.visible) this.draw(); });
    this.observer.observe(target);
    this.load();
  }

  async load() {
    try {
      const loader = new GLTFLoader();
      const results = await Promise.all([...MODELS.map((name) => loader.loadAsync(`${ASSETS}${name}.glb`)),
        loader.loadAsync(`${ASSETS}Rig_Medium_General.glb`), loader.loadAsync(`${ASSETS}staff.gltf`)]);
      this.models = Object.fromEntries(MODELS.map((name, i) => [name, results[i].scene]));
      const idle = results[MODELS.length].animations.find((clip) => clip.name === "Idle_A");
      this.mixers = MODELS.map((name) => {
        const model = this.models[name];
        this.character.add(model);
        const mixer = new THREE.AnimationMixer(model);
        if (idle) mixer.clipAction(idle).play();
        return mixer;
      });
      this.staff = results[MODELS.length + 1].scene;
      this.staff.scale.setScalar(0.82);
      this.staff.position.set(-0.1, -0.12, 0.21);
      this.crown = crown();
      this.compass = compass();
      this.aura = aura();
      for (const prop of [this.staff, this.crown, this.compass])
        prop.traverse((object) => { if (object.isMesh) object.userData.cosmetic = true; });
      this.character.add(this.aura);
      const bounds = new THREE.Box3().setFromObject(this.models.Rogue);
      const center = bounds.getCenter(new THREE.Vector3());
      const height = bounds.getSize(new THREE.Vector3()).y;
      this.camera.position.set(height * 0.42, center.y + height * 0.13, height * 2.35);
      this.camera.lookAt(center.x, center.y, center.z);
      this.resize();
      this.apply();
    } catch (error) {
      console.error("KayKit:", error);
      this.target.textContent = "No se pudo cargar el aventurero 3D.";
      this.target.classList.add("character-error");
    }
  }

  update(hero) {
    this.hero = hero;
    this.target.setAttribute("aria-label", `${hero.name} con su equipo`);
    if (this.models) this.apply();
  }

  rotate(angle) {
    this.character.rotation.y += angle;
    this.pendingSnapshot = true;
    this.draw();
  }

  apply() {
    if (!this.hero || !this.models) return;
    const { appearance, equipped } = this.hero;
    const base = this.models[appearance] ? appearance : "Rogue";
    const body = equipped.body === "tunica" ? "Mage" : equipped.body === "armadura" ? "Knight" : base;
    const head = equipped.head === "capucha" ? "Rogue_Hooded" : base;
    const cape = equipped.back === "capa" ? "Mage" : null;
    for (const [name, model] of Object.entries(this.models)) {
      model.traverse((object) => {
        if (!object.isMesh || object.userData.cosmetic) return;
        const part = object.name.split("_").pop();
        object.visible = (name === body && ["ArmLeft", "ArmRight", "Body", "LegLeft", "LegRight"].includes(part))
          || (name === head && (part === "Head" || equipped.head === "capucha" && part === "Mask"))
          || (name === base && equipped.head !== "capucha" && equipped.head !== "corona" && ["Hat", "Helmet", "HelmetVisor"].includes(part))
          || (name === cape && part === "Cape");
      });
    }
    this.models[head].getObjectByName("head").add(this.crown);
    this.crown.visible = equipped.head === "corona";
    const hand = this.models[body].getObjectByName("handr");
    hand.add(this.staff, this.compass);
    this.staff.visible = equipped.hand === "baston";
    this.compass.visible = equipped.hand === "brujula";
    this.aura.visible = equipped.back === "aura";
    this.pendingSnapshot = true;
    this.draw();
  }

  resize() {
    const width = this.target.clientWidth;
    const height = this.target.clientHeight;
    if (!width || !height) return;
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.draw();
  }

  draw() {
    if (!this.visible || !this.models) return;
    cancelAnimationFrame(this.frame);
    const tick = () => {
      const delta = this.clock.getDelta();
      if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches)
        this.mixers.forEach((mixer) => mixer.update(delta));
      this.renderer.render(this.scene, this.camera);
      if (this.onSnapshot && this.pendingSnapshot) {
        this.onSnapshot(this.renderer.domElement.toDataURL());
        this.pendingSnapshot = false;
      }
      if (this.visible) this.frame = requestAnimationFrame(tick);
    };
    tick();
  }
}

export function renderKaykitCharacter(target, hero, onSnapshot) {
  let view = views.get(target);
  if (!view) {
    view = new CharacterView(target, onSnapshot);
    views.set(target, view);
  }
  view.update(hero);
  return view;
}
