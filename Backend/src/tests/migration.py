import os
import psycopg
from psycopg.rows import dict_row

# =========================
# CONFIGURACIÓN RENDER DB
# =========================

DATABASE_URL = "postgresql://vaultchain_vy3p_user:MT4dyNRtiwYFzi9xlBHIyfdbckqQJC2O@dpg-d86g6p8jo89c73ckn7eg-a.oregon-postgres.render.com/vaultchain_vy3p"

# =========================
# CONEXIÓN GLOBAL
# =========================

_conn = None

def get_conn():
    global _conn

    if _conn is None or _conn.closed:
        _conn = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )

    return _conn


# =========================
# SCRIPT SQL
# =========================

SQL_SCRIPT = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    contrasenas TEXT NOT NULL,
    public_key TEXT NOT NULL,
    encrypted_private_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INT NOT NULL REFERENCES users(id),
    recipient_id INT REFERENCES users(id),
    group_id INT REFERENCES groups(id),
    ciphertext TEXT NOT NULL,
    encrypted_key TEXT NOT NULL,
    nonce VARCHAR(24) NOT NULL,
    auth_tag VARCHAR(24) NOT NULL,
    signature TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_members (
    id_user INT NOT NULL REFERENCES users(id),
    id_group INT NOT NULL REFERENCES groups(id),
    CONSTRAINT uq_group_member UNIQUE (id_user, id_group)
);

CREATE TABLE IF NOT EXISTS blockchain (
    id SERIAL PRIMARY KEY,
    block_index SERIAL UNIQUE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sender_id INT NOT NULL REFERENCES users(id),
    recipient_id INT NOT NULL REFERENCES users(id),
    message_hash TEXT NOT NULL,
    previous_hash CHAR(64) NOT NULL,
    nonce INT NOT NULL,
    hash CHAR(64) NOT NULL UNIQUE
);

INSERT INTO users (
    name,
    email,
    contrasenas,
    public_key,
    encrypted_private_key
)
VALUES (
    'Genesis',
    'genesis@system.local',
    '',
    '',
    ''
)
ON CONFLICT (email) DO NOTHING;
"""


# =========================
# EJECUTAR MIGRACIÓN
# =========================

def run_migration():
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute(SQL_SCRIPT)

    conn.commit()

    print("✅ Tablas creadas correctamente")


if __name__ == "__main__":
    run_migration()
