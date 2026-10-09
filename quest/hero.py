from .curriculum import WORLDS, STAGES_PER_WORLD

ITEMS = [
    {"id": "capucha", "name": "Capucha viajera", "slot": "head", "rarity": "Común", "price": 10,
     "requires": None, "requirement": "Disponible desde el inicio"},
    {"id": "capa", "name": "Capa de aventura", "slot": "back", "rarity": "Común", "price": 15,
     "requires": None, "requirement": "Disponible desde el inicio"},
    {"id": "tunica", "name": "Túnica del Bosque", "slot": "body", "rarity": "Poco común", "price": 20,
     "requires": "condicionales:5", "requirement": "Completa el Bosque de Decisiones"},
    {"id": "brujula", "name": "Brújula de los Bucles", "slot": "hand", "rarity": "Poco común", "price": 25,
     "requires": "bucles:5", "requirement": "Completa las Montañas del Bucle"},
    {"id": "armadura", "name": "Armadura de Datos", "slot": "body", "rarity": "Raro", "price": 35,
     "requires": "listas:5", "requirement": "Completa el Archipiélago de Datos"},
    {"id": "baston", "name": "Bastón de Funciones", "slot": "hand", "rarity": "Raro", "price": 40,
     "requires": "funciones:5", "requirement": "Completa la Torre de Funciones"},
    {"id": "corona", "name": "Corona del Código", "slot": "head", "rarity": "Legendario", "price": 60,
     "requires": "funciones:5", "requirement": "Completa la Torre de Funciones"},
    {"id": "aura", "name": "Aura de Python", "slot": "back", "rarity": "Mítico", "price": 80,
     "requires": "campaign", "requirement": "Completa toda la campaña"},
]
ITEM_BY_ID = {item["id"]: item for item in ITEMS}
SLOTS = {"head", "body", "back", "hand"}
APPEARANCES = {"Rogue": "Pícaro", "Ranger": "Explorador", "Mage": "Mago", "Knight": "Caballero", "Barbarian": "Bárbaro"}


def unlocked(item, state):
    required = item["requires"]
    awards = state["campaign"]["awarded_stages"]
    return required is None or (all(f"{world['id']}:{stage}" in awards
                                    for world in WORLDS for stage in range(1, STAGES_PER_WORLD + 1))
                               if required == "campaign" else required in awards)


def public_hero(state):
    hero = state["hero"]
    return {
        "name": hero["name"], "coins": state["campaign"]["coins"],
        "appearance": hero["appearance"], "appearances": APPEARANCES,
        "owned": hero["owned"], "equipped": hero["equipped"],
        "items": [{**item, "unlocked": unlocked(item, state)} for item in ITEMS],
    }


def rename(store, name):
    if not isinstance(name, str):
        raise ValueError("Escribe un nombre de 1 a 24 caracteres.")
    name = name.strip()
    if not 1 <= len(name) <= 24 or not name.isprintable():
        raise ValueError("Escribe un nombre de 1 a 24 caracteres sin saltos de línea.")
    state = store.load()
    state["hero"]["name"] = name
    store.save(state)


def change_appearance(store, appearance):
    if not isinstance(appearance, str) or appearance not in APPEARANCES:
        raise ValueError("Elige uno de los aventureros disponibles.")
    state = store.load()
    state["hero"]["appearance"] = appearance
    store.save(state)


def purchase(store, item_id):
    item = ITEM_BY_ID.get(item_id) if isinstance(item_id, str) else None
    if not item:
        raise ValueError("Ese objeto no existe.")
    state = store.load()
    if item_id in state["hero"]["owned"]:
        raise ValueError("Ya tienes ese objeto.")
    if not unlocked(item, state):
        raise ValueError("Completa el hito indicado para desbloquear este objeto.")
    if state["campaign"]["coins"] < item["price"]:
        raise ValueError("Todavía no tienes suficientes monedas.")
    state["campaign"]["coins"] -= item["price"]
    state["hero"]["owned"].append(item_id)
    state["hero"]["equipped"][item["slot"]] = item_id
    store.save(state)


def equip(store, slot, item_id):
    if not isinstance(slot, str) or slot not in SLOTS:
        raise ValueError("Esa posición del personaje no existe.")
    state = store.load()
    if item_id is not None:
        item = ITEM_BY_ID.get(item_id) if isinstance(item_id, str) else None
        if not item or item["slot"] != slot or item_id not in state["hero"]["owned"]:
            raise ValueError("Solo puedes equipar un objeto tuyo en su posición.")
    state["hero"]["equipped"][slot] = item_id
    store.save(state)
