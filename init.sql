CREATE TABLE IF NOT EXISTS users (
    id                    SERIAL PRIMARY KEY,
    name                  VARCHAR(100) NOT NULL,
    email                 VARCHAR(255) NOT NULL UNIQUE,
    contrasenas           TEXT NOT NULL,
    public_key            TEXT NOT NULL,
    encrypted_private_key TEXT NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);