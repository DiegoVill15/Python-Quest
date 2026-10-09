// Ilustraciones de cada aldea: islas flotantes dibujadas en SVG (origen = centro del césped).
const island = `
  <ellipse cx="0" cy="34" rx="30" ry="5" fill="#0b1218" opacity=".3"/>
  <path d="M-42,2 Q-40,18 -20,24 L-8,36 L0,30 L8,38 L20,24 Q40,18 42,2 Z" fill="#7b573a"/>
  <path d="M-30,14 L-24,20 M18,16 L24,12 M-4,24 L2,20" stroke="#5a3b27" stroke-width="2" stroke-linecap="round"/>
  <ellipse cx="0" cy="2" rx="43" ry="12" fill="#5f9e45"/>
  <ellipse cx="0" cy="0" rx="43" ry="12" fill="#7bc15a"/>
  <ellipse cx="-12" cy="-2" rx="16" ry="4" fill="#97d56f" opacity=".7"/>`;

const tree = (x, y, s = 1, c = "#3f8f4a") => `<g transform="translate(${x},${y}) scale(${s})">
  <rect x="-2" y="-6" width="4" height="8" fill="#6b4423"/>
  <path d="M0,-34 L-12,-10 L12,-10 Z" fill="${c}"/><path d="M0,-26 L-15,-2 L15,-2 Z" fill="${c}"/>
  <path d="M0,-34 L-4,-27 L4,-27 Z" fill="#ffffff" opacity=".35"/></g>`;

const flag = (x, y, color, s = 1) => `<g transform="translate(${x},${y}) scale(${s})">
  <rect x="-1" y="-20" width="2" height="22" fill="#4a3322"/><path d="M1,-20 L15,-15 L1,-9 Z" fill="${color}" stroke="#0b1218" stroke-width=".8"/></g>`;

const scenes = {
  // Aldea Inicial: casa con humo y bandera
  fundamentos: (c) => `
    <rect x="-17" y="-24" width="34" height="24" fill="#ecd9a8" stroke="#8c6a45" stroke-width="1.5"/>
    <path d="M-23,-23 L0,-46 L23,-23 Z" fill="#c4553f" stroke="#7d2f22" stroke-width="1.5"/>
    <rect x="9" y="-44" width="6" height="12" fill="#8a6f55"/>
    <circle cx="14" cy="-50" r="3.5" fill="#fff" opacity=".7"><animate attributeName="cy" values="-48;-60" dur="2.6s" repeatCount="indefinite"/><animate attributeName="opacity" values=".7;0" dur="2.6s" repeatCount="indefinite"/></circle>
    <rect x="-5" y="-14" width="10" height="14" rx="1" fill="#6b4423"/><circle cx="3" cy="-7" r="1" fill="#f6c96e"/>
    <rect x="-14" y="-19" width="7" height="7" fill="${c}" stroke="#8c6a45"/>
    ${tree(-32, 2, .7)}${flag(30, 2, c, .9)}`,
  // Bosque de Decisiones: pinos y señal con dos caminos
  condicionales: (c) => `
    ${tree(-28, 0, 1.05)}${tree(26, 0, .9, "#2f7d4a")}${tree(-10, -4, .7, "#4aa35a")}
    <rect x="-1.5" y="-28" width="3" height="30" fill="#6b4423" transform="translate(14,2)"/>
    <path d="M14,-26 L32,-26 L37,-21 L32,-16 L14,-16 Z" fill="#e9d29c" stroke="#8c6a45"/>
    <path d="M14,-12 L-4,-12 L-9,-7 L-4,-2 L14,-2 Z" fill="${c}" stroke="#4a6b4a"/>`,
  // Montañas del Bucle: picos nevados y un anillo en bucle
  bucles: (c) => `
    <path d="M-40,2 L-14,-36 L8,2 Z" fill="#7d8a97"/><path d="M-14,-36 L-22,-22 L-14,-26 L-8,-20 Z" fill="#fff"/>
    <path d="M-6,2 L20,-46 L42,2 Z" fill="#94a3b0"/><path d="M20,-46 L10,-28 L20,-33 L28,-26 Z" fill="#fff"/>
    <path d="M20,-46 L42,2 L28,2 Z" fill="#000" opacity=".12"/>
    <g transform="translate(-2,-50)"><g><path d="M-12,0 A12,12 0 1 1 -4,11" fill="none" stroke="${c}" stroke-width="3.5" stroke-linecap="round"/><path d="M-9,7 L-3,13 L-1,5 Z" fill="${c}"/>
    <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="6s" repeatCount="indefinite"/></g></g>`,
  // Archipiélago de Datos: palmera y cajas con índices (como una lista)
  listas: (c) => `
    <path d="M-22,0 Q-24,-18 -18,-34" fill="none" stroke="#8a5a34" stroke-width="4" stroke-linecap="round"/>
    <path d="M-18,-34 Q-34,-38 -40,-28 M-18,-34 Q-26,-46 -36,-44 M-18,-34 Q-10,-48 0,-42 M-18,-34 Q-6,-34 0,-26" fill="none" stroke="#3f9a4a" stroke-width="4" stroke-linecap="round"/>
    ${[0, 1, 2].map((i) => `<g transform="translate(${-6 + i * 17},-4)"><rect width="15" height="15" rx="2" fill="${c}" stroke="#4a3a7a" stroke-width="1.5"/><text x="7.5" y="11.5" text-anchor="middle" font-size="10" font-weight="900" font-family="ui-monospace,Menlo,monospace" fill="#2a1f55">${i}</text></g>`).join("")}`,
  // Torre de Funciones: torre alta con almenas y bandera
  funciones: (c) => `
    <rect x="-12" y="-50" width="24" height="52" fill="#d8c3c8" stroke="#8a6f78" stroke-width="1.5"/>
    <path d="M-12,-50 h5 v-6 h4 v6 h6 v-6 h4 v6 h5 v-6 h4 v6 h-28" fill="#d8c3c8"/>
    <path d="M-17,-50 L0,-72 L17,-50 Z" fill="${c}" stroke="#a04c5a" stroke-width="1.5"/>
    <rect x="-3" y="-40" width="6" height="11" rx="3" fill="#2b3340"/><rect x="-3" y="-20" width="6" height="11" rx="3" fill="#2b3340"/>
    <rect x="-5" y="-9" width="10" height="11" rx="1" fill="#6b4423"/>
    ${flag(0, -70, "#f6c96e", .8)}${tree(-30, 2, .6)}${tree(30, 2, .6)}`,
  // Biblioteca de Claves: templo con columnas y llave dorada flotando
  diccionarios: (c) => `
    <path d="M-28,-24 L0,-42 L28,-24 Z" fill="#e8d7b0" stroke="#8c6a45" stroke-width="1.5"/>
    ${[-21, -7, 7, 21].map((x) => `<rect x="${x - 3}" y="-24" width="6" height="24" fill="#f4e8c8" stroke="#8c6a45"/>`).join("")}
    <rect x="-31" y="0" width="62" height="5" fill="#cdb98a" stroke="#8c6a45"/>
    <rect x="-3" y="-34" width="6" height="8" fill="${c}"/>
    <g transform="translate(0,-60)"><circle cx="-8" cy="0" r="6" fill="none" stroke="#f6c96e" stroke-width="3.5"/><path d="M-2,0 H14 M10,0 v6 M14,0 v5" stroke="#f6c96e" stroke-width="3.5" stroke-linecap="round" fill="none"/>
    <animateTransform attributeName="transform" type="translate" values="0,-60;0,-64;0,-60" dur="2.4s" repeatCount="indefinite"/></g>`,
  // Taller de Alquimia: caldero burbujeante y matraz
  taller: (c) => `
    <path d="M-20,-18 Q-24,6 -8,6 L8,6 Q24,6 20,-18 Z" fill="#37444d" stroke="#1b252b" stroke-width="1.5"/>
    <ellipse cx="0" cy="-18" rx="20" ry="5.5" fill="#37444d" stroke="#1b252b" stroke-width="1.5"/><ellipse cx="0" cy="-18" rx="16" ry="3.8" fill="${c}"/>
    <circle cx="-5" cy="-30" r="4" fill="${c}" opacity=".85"><animate attributeName="cy" values="-20;-46" dur="2.2s" repeatCount="indefinite"/><animate attributeName="opacity" values=".9;0" dur="2.2s" repeatCount="indefinite"/></circle>
    <circle cx="6" cy="-30" r="3" fill="${c}" opacity=".85"><animate attributeName="cy" values="-20;-52" dur="1.7s" repeatCount="indefinite"/><animate attributeName="opacity" values=".9;0" dur="1.7s" repeatCount="indefinite"/></circle>
    <path d="M-6,8 Q0,-6 6,8 Z" fill="#f59e3f"/>
    <g transform="translate(30,-2)"><path d="M-2,-22 h4 v9 l7,13 h-18 l7,-13 Z" fill="#cfeaf0" stroke="#5c8591" stroke-width="1.2"/><path d="M-6,-5 l-3,5 h18 l-3,-5 Z" fill="#e879c8"/></g>`,
  // Laberinto de Rutas: seto-laberinto con bandera en el centro
  rutas: (c) => `
    <rect x="-30" y="-30" width="60" height="30" rx="3" fill="#2f7d3a" stroke="#1f5a2a" stroke-width="1.5"/>
    <path d="M-30,-22 H-12 M-12,-22 V-8 M-30,-10 H-20 M0,-30 V-16 M0,-16 H18 M18,-16 V-4 M8,0 V-8 M24,-30 V-22 M12,-22 H30" stroke="${c}" stroke-width="3.5" stroke-linecap="round" fill="none"/>
    <circle cx="-6" cy="-12" r="3" fill="#f6c96e"/>${flag(4, -26, "#e11d48", .9)}`,
  // Ciudadela del Aventurero: castillo con torres y banderas
  proyecto: (c) => `
    <rect x="-26" y="-34" width="14" height="36" fill="#d9ccd4" stroke="#8a7782" stroke-width="1.5"/>
    <rect x="12" y="-34" width="14" height="36" fill="#d9ccd4" stroke="#8a7782" stroke-width="1.5"/>
    <rect x="-14" y="-26" width="28" height="28" fill="#e6dce2" stroke="#8a7782" stroke-width="1.5"/>
    <path d="M-30,-34 L-19,-52 L-8,-34 Z M8,-34 L19,-52 L30,-34 Z" fill="${c}" stroke="#a5527a" stroke-width="1.5"/>
    <path d="M-6,2 V-10 a6,6 0 0 1 12,0 V2 Z" fill="#4a3322"/>
    <path d="M-14,-26 h4 v-5 h4 v5 h4 v-5 h4 v5 h4 v-5 h4 v5" fill="#e6dce2" stroke="#8a7782"/>
    ${flag(-19, -50, "#f6c96e", .7)}${flag(19, -50, "#f6c96e", .7)}`,
};

export function emblemMarkup(id, color) {
  return island + (scenes[id] || scenes.fundamentos)(color);
}
