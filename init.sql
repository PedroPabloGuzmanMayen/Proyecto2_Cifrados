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
    id            SERIAL PRIMARY KEY,
    block_index   SERIAL UNIQUE,
    timestamp     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    sender_id     INT          NOT NULL REFERENCES users(id),
    recipient_id  INT          NOT NULL REFERENCES users(id),
    message_hash  TEXT         NOT NULL,
    previous_hash CHAR(64)     NOT NULL,
    nonce         INT          NOT NULL,
    hash          CHAR(64)     NOT NULL UNIQUE
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
ON CONFLICT (id) DO NOTHING;