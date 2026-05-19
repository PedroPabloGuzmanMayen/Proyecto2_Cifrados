"""
seed.py — Crea 3 usuarios y 3 grupos en VaultChain.
Ejecutar UNA sola vez antes de correr test_messages.py

Uso:
    python seed.py [--base-url http://localhost:8000]
"""

import requests
import json
import argparse

# ─── Configuración ────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://localhost:8000")
args = parser.parse_args()
BASE = args.base_url

# ─── Datos de los 3 usuarios ──────────────────────────────────────────────────
USUARIOS = [
    {"name": "Alice López",   "email": "alice@vaultchain.dev",  "contrasenas": "AlicePass123!"},
    {"name": "Bob Martínez",  "email": "bob@vaultchain.dev",    "contrasenas": "BobPass456!"},
    {"name": "Carol Jiménez", "email": "carol@vaultchain.dev",  "contrasenas": "CarolPass789!"},
]

# ─── Helpers ──────────────────────────────────────────────────────────────────
def ok(label, r):
    if r.status_code in (200, 201):
        print(f"  ✓ {label}")
        return r.json()
    else:
        print(f"  ✗ {label} → {r.status_code}: {r.text}")
        return None


# ─── 1. Registrar usuarios ────────────────────────────────────────────────────
print("\n=== Registrando usuarios ===")
user_ids = {}

for u in USUARIOS:
    r = requests.post(f"{BASE}/registro", json=u)
    ok(f"Registro de {u['name']}", r)

print("\n=== Haciendo login para obtener IDs ===")
for u in USUARIOS:
    r = requests.post(f"{BASE}/login", json={"email": u["email"], "contrasena": u["contrasenas"]})
    data = ok(f"Login de {u['name']}", r)
    if data:
        import jwt as _jwt
        payload = _jwt.decode(data["access_token"], options={"verify_signature": False})
        user_ids[u["email"]] = int(payload["sub"])
        print(f"    → ID: {user_ids[u['email']]}")

# Guardar IDs resueltos en los datos de usuario para usarlos después
for u in USUARIOS:
    u["id"] = user_ids.get(u["email"])

# ─── 2. Crear grupos ──────────────────────────────────────────────────────────
ids = [u["id"] for u in USUARIOS if u["id"] is not None]

GRUPOS = [
    {"name": "Grupo Alpha",   "miembros": ids[:2]},          # Alice + Bob
    {"name": "Grupo Beta",    "miembros": ids[1:]},           # Bob + Carol
    {"name": "Grupo General", "miembros": ids},               # Los 3
]

print("\n=== Creando grupos ===")
group_ids = {}
for g in GRUPOS:
    r = requests.post(f"{BASE}/groups", json=g)
    data = ok(f"Grupo '{g['name']}'", r)
    if data:
        group_ids[g["name"]] = data["group_id"]
        print(f"    → ID: {data['group_id']}  miembros: {g['miembros']}")

# ─── 3. Guardar estado para test_messages.py ─────────────────────────────────
state = {
    "base_url": BASE,
    "users": [
        {
            "id":    u["id"],
            "name":  u["name"],
            "email": u["email"],
            "password": u["contrasenas"],
        }
        for u in USUARIOS
    ],
    "groups": [
        {"id": gid, "name": gname}
        for gname, gid in group_ids.items()
    ],
}

with open("seed_state.json", "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print("\n=== Resumen ===")
print(json.dumps(state, indent=2, ensure_ascii=False))
print("\n✅ seed_state.json guardado. Ya puedes correr: python test_messages.py")