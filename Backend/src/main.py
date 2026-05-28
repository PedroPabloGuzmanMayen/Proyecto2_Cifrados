import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from auth.Hashing import hash_password, verify_password
from auth.key_generator import generar_par_llaves, cargar_llave_privada
from crypto.hybrid_cipher import cifrar_mensaje, generar_llave_aes
from crypto.hybrid_decypher import descifrar_mensaje
from signatures.signer import firmar_mensaje, obtener_hash_mensaje
from signatures.verifier import verificar_firma, SignatureInvalidError
from datetime import datetime, timezone, timedelta
import jwt
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from blockchain.chain import Blockchain
from Crypto.Hash import SHA256
import pyotp
import qrcode
import io
import base64

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

blockchain = Blockchain()
secret = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ─── JWT ────────────────────────────────────────────────────────────────────
def crear_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def crear_refresh_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def verificar_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token inválido")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")



# ─── Conexión ────────────────────────────────────────────────────────────────
_conn = None


def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            sslmode="require",
            row_factory=dict_row,
        )
    return _conn


# ─── Schemas ─────────────────────────────────────────────────────────────────
class Usuario(BaseModel):
    name: str
    email: EmailStr
    contrasenas: str


class Usuario_Login(BaseModel):
    email: str
    contrasena: str


class mensaje_model(BaseModel):
    sender: int
    recipient: int
    message: str
    sender_password: str


class GrupoCreate(BaseModel):
    name: str
    miembros: list[int]

class AgregarMiembro(BaseModel):
    user_id: int


class DecryptRequest(BaseModel):
    """
    Para descifrar mensajes el cliente envía su contraseña (nunca se almacena).
    La llave privada se reconstruye en el servidor a partir de la contraseña
    y el blob cifrado que sí está en la BD.
    """
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando servidor...")
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT block_index, hash FROM blockchain ORDER BY block_index DESC LIMIT 1;")
        result = cur.fetchone()
    
    if result is None:
        genesis = blockchain.create_genesis_block()

        try: 
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO blockchain (block_index, sender_id, recipient_id, message_hash, previous_hash, nonce, hash)"
                    " VALUES (%s, %s, %s, %s, %s, %s, %s);",
                    (
                        genesis.index,
                        genesis.data["sender_id"],
                        genesis.data["recipient_id"],
                        genesis.data["message_hash"],
                        genesis.previous_hash,
                        genesis.nonce,
                        genesis.hash,
                    ),
                )
                conn.commit()

        except Exception:
            conn.rollback()
            raise HTTPException(status_code=500, detail="server error")
    else:
        blockchain.index_counter = result["block_index"] + 1
        blockchain.prev_hash = result["hash"]
        

    print("Startup terminado")

    yield  

    print("Apagando servidor...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def insert_into_the_blockchain(sender_id: int, recipient_id: int, message_hash: str):
    
    new_block = blockchain.create_next_block(sender_id, recipient_id, message_hash)
    conn = get_conn()
    try: 
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO blockchain (block_index, sender_id, recipient_id, message_hash, previous_hash, nonce, hash)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s);",
                (
                    new_block.index,
                    sender_id,
                    recipient_id,
                    message_hash,
                    new_block.previous_hash,
                    new_block.nonce,
                    new_block.hash,
                ),
            )
            conn.commit()

    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="server error")


# ─── Endpoints ───────────────────────────────────────────────────────────────
@app.post("/registro")
def registrar(usuario: Usuario):
    conn = get_conn()
    password = hash_password(usuario.contrasenas)
    public, private = generar_par_llaves(usuario.contrasenas)

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s;", (usuario.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Correo ya registrado")

        cur.execute(
            "INSERT INTO users (name, email, contrasenas, public_key, encrypted_private_key, created_at)"
            " VALUES (%s, %s, %s, %s, %s, %s);",
            (usuario.name, usuario.email, password, public, private, datetime.utcnow()),
        )
        conn.commit()

    return {"ok": True}


@app.post("/login")
def login(credenciales: Usuario_Login):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, contrasenas, totp_secret FROM users WHERE email = %s;",
            (credenciales.email,),
        )
        result = cur.fetchone()

    if result is None:
        raise HTTPException(status_code=400, detail="Usuario no existe")

    if not verify_password(credenciales.contrasena, result["contrasenas"]):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    
    # MFA
    if result["totp_secret"]:
        return {
            "mfa_required": True,
            "user_id": result["id"]
        }

    token = crear_token(result["id"], result["email"])
    refresh = crear_refresh_token(result["id"], result["email"])
    return {"access_token": token, "refresh_token": refresh, "token_type": "bearer"}


@app.post("/refresh")
def refresh_token(body: TokenRefreshRequest):
    try:
        payload = jwt.decode(body.refresh_token, secret, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    user_id = int(payload["sub"])
    email = payload["email"]
    new_token = crear_token(user_id, email)
    new_refresh = crear_refresh_token(user_id, email)
    return {"access_token": new_token, "refresh_token": new_refresh, "token_type": "bearer"}


@app.get("/users/{user_id}/key")
def obtener_llave_publica(user_id: int, payload: dict = Depends(verificar_token)):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT public_key FROM users WHERE id = %s;", (user_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"user_id": user_id, "public_key": row["public_key"]}


@app.post("/individual_message/")
def send_message(mensaje: mensaje_model, payload: dict = Depends(verificar_token)):
    aes_key = generar_llave_aes()
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT public_key FROM users WHERE id = %s;", (mensaje.recipient,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Destinatario no encontrado")

    with conn.cursor() as cur:
        cur.execute("SELECT encrypted_private_key FROM users WHERE id = %s;", (mensaje.sender,))
        sender_row = cur.fetchone()
    if not sender_row:
        raise HTTPException(status_code=404, detail="Remitente no encontrado")

    try:
        private_key_sender = cargar_llave_privada(mensaje.sender_password, sender_row["encrypted_private_key"])
    except Exception:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    firma_b64 = firmar_mensaje(mensaje.message, private_key_sender)


    encrypted_data = cifrar_mensaje(mensaje.message, row["public_key"], aes_key)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO messages (sender_id, recipient_id, ciphertext, encrypted_key, nonce, auth_tag, signature)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                mensaje.sender,
                mensaje.recipient,
                encrypted_data["ciphertext"],
                encrypted_data["encrypted_key"],
                encrypted_data["nonce"],
                encrypted_data["auth_tag"],
                firma_b64,
            ),
        )
        conn.commit()

    mensaje_hash = obtener_hash_mensaje(mensaje.message)

    insert_into_the_blockchain(mensaje.sender, mensaje.recipient, mensaje_hash)

    return {"ok": True, "message": "Mensaje enviado con éxito"}


# ─── NUEVO: GET mensajes cifrados ────────────────────────────────────────────
@app.get("/messages/{user_id}")
def get_messages(user_id: int, payload: dict = Depends(verificar_token)):
    """
    Devuelve todos los mensajes cifrados recibidos por user_id.
    El cliente recibe los blobs y puede descifrarlos con el endpoint POST debajo.
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cur.execute(
            """
            SELECT m.id, m.sender_id, u.name AS sender_name,
                   m.ciphertext, m.encrypted_key, m.nonce, m.auth_tag,
                   m.created_at
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.recipient_id = %s
            ORDER BY m.created_at DESC;
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    return {"user_id": user_id, "messages": rows}


# ─── NUEVO: POST descifrar un mensaje ────────────────────────────────────────
@app.post("/messages/{user_id}/decrypt/{message_id}")
def decrypt_message(user_id: int, message_id: int, body: DecryptRequest, payload: dict = Depends(verificar_token)):
    """
    Descifra un mensaje específico en el servidor usando la contraseña del usuario.

    Flujo:
      1. Recupera el blob cifrado (encrypted_private_key) de la BD.
      2. Reconstruye la llave privada con la contraseña recibida.
      3. Descifra el mensaje y devuelve el texto plano.

    Nota de seguridad: la contraseña viaja sólo en este request y NO se almacena.
    Para producción se recomienda descifrar en el cliente (WebCrypto API).
    """
    conn = get_conn()

    # 1 – Recuperar llave privada cifrada del usuario
    with conn.cursor() as cur:
        cur.execute(
            "SELECT encrypted_private_key FROM users WHERE id = %s;",
            (user_id,),
        )
        user_row = cur.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 2 – Recuperar el mensaje cifrado (sender or recipient can decrypt)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ciphertext, encrypted_key, nonce, auth_tag
            FROM messages
            WHERE id = %s AND (recipient_id = %s OR sender_id = %s);
            """,
            (message_id, user_id, user_id),
        )
        msg_row = cur.fetchone()
    if not msg_row:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    # 3 – Reconstruir llave privada y descifrar
    try:
        private_key = cargar_llave_privada(
            body.password, user_row["encrypted_private_key"]
        )
        plaintext = descifrar_mensaje(
            {
                "ciphertext":    msg_row["ciphertext"],
                "encrypted_key": msg_row["encrypted_key"],
                "nonce":         msg_row["nonce"],
                "auth_tag":      msg_row["auth_tag"],
            },
            private_key,
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="No se pudo descifrar: contraseña incorrecta o mensaje alterado",
        )

    return {"message_id": message_id, "plaintext": plaintext}


@app.get("/users/{user_id}/groups")
def get_user_groups(user_id: int, payload: dict = Depends(verificar_token)):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cur.execute(
            """
            SELECT g.id, g.name
            FROM groups g
            JOIN group_members gm ON gm.id_group = g.id
            WHERE gm.id_user = %s
            ORDER BY g.name;
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    return {"user_id": user_id, "groups": rows}


@app.get("/users/{user_id}/groups/messages")
def get_group_messages(user_id: int, payload: dict = Depends(verificar_token)):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cur.execute(
            """
            SELECT m.id, m.sender_id, u.name AS sender_name,
                   m.group_id, g.name AS group_name,
                   m.ciphertext, m.encrypted_key, m.nonce, m.auth_tag,
                   m.created_at
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            JOIN groups g ON g.id = m.group_id
            WHERE m.recipient_id = %s AND m.group_id IS NOT NULL
            ORDER BY m.created_at DESC;
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    return {"user_id": user_id, "messages": rows}


@app.post("/messages/{user_id}/decrypt_group/{message_id}")
def decrypt_group_message(user_id: int, message_id: int, body: DecryptRequest, payload: dict = Depends(verificar_token)):
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT encrypted_private_key FROM users WHERE id = %s;",
            (user_id,),
        )
        user_row = cur.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ciphertext, encrypted_key, nonce, auth_tag
            FROM messages
            WHERE id = %s AND recipient_id = %s AND group_id IS NOT NULL;
            """,
            (message_id, user_id),
        )
        msg_row = cur.fetchone()
    if not msg_row:
        raise HTTPException(status_code=404, detail="Mensaje de grupo no encontrado")

    try:
        private_key = cargar_llave_privada(
            body.password, user_row["encrypted_private_key"]
        )
        plaintext = descifrar_mensaje(
            {
                "ciphertext":    msg_row["ciphertext"],
                "encrypted_key": msg_row["encrypted_key"],
                "nonce":         msg_row["nonce"],
                "auth_tag":      msg_row["auth_tag"],
            },
            private_key,
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="No se pudo descifrar: contraseña incorrecta o mensaje alterado",
        )

    return {"message_id": message_id, "plaintext": plaintext}


@app.post("/group_message")
def send_message_to_group(mensaje: mensaje_model, payload: dict = Depends(verificar_token)):
    aes_key = generar_llave_aes()
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM groups WHERE id = %s;", (mensaje.recipient,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="El grupo al que le quieres enviar un mensaje no existe")
    
    with conn.cursor() as cur:
        cur.execute("SELECT id_user FROM group_members WHERE id_group = %s;", (mensaje.recipient,))
        row = cur.fetchall()
    if not row:
        raise HTTPException(status_code=404, detail="Error, no hay usuarios en el grupo")
    
    with conn.cursor() as cur:
        cur.execute("SELECT encrypted_private_key FROM users WHERE id = %s;", (mensaje.sender,))
        sender_row = cur.fetchone()
    if not sender_row:
        raise HTTPException(status_code=404, detail="Remitente no encontrado")

    try:
        private_key_sender = cargar_llave_privada(mensaje.sender_password, sender_row["encrypted_private_key"])
    except Exception:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    firma_b64 = firmar_mensaje(mensaje.message, private_key_sender)
    
    public_keys = []
    for i in row:

        with conn.cursor() as cur:
            cur.execute("SELECT public_key FROM users WHERE id = %s;", (i['id_user'],))
            result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="El grupo al que le quieres enviar un mensaje no existe")
        public_keys.append({'user_id': i['id_user'], 'public_key': result['public_key']})

    for i in public_keys:
        encrypted_data = cifrar_mensaje(mensaje.message, i["public_key"], aes_key)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages (sender_id, recipient_id, group_id, ciphertext, encrypted_key, nonce, auth_tag, signature)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    mensaje.sender,
                    i['user_id'],
                    mensaje.recipient,
                    encrypted_data["ciphertext"],
                    encrypted_data["encrypted_key"],
                    encrypted_data["nonce"],
                    encrypted_data["auth_tag"],
                    firma_b64
                )
            )
            conn.commit()


        mensaje_hash = obtener_hash_mensaje(mensaje.message)

        insert_into_the_blockchain(mensaje.sender, mensaje.recipient, mensaje_hash)

    return {"ok": True, "message": "mensaje enviado con éxito"}

@app.post("/groups")
def crear_grupo(grupo: GrupoCreate, payload: dict = Depends(verificar_token)):
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM users WHERE id = ANY(%s);",
            (grupo.miembros,)
        )
        encontrados = {row["id"] for row in cur.fetchall()}

    faltantes = set(grupo.miembros) - encontrados
    if faltantes:
        raise HTTPException(
            status_code=404,
            detail=f"Usuarios no encontrados: {sorted(faltantes)}"
        )

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO groups (name) VALUES (%s) RETURNING id;",
            (grupo.name,)
        )
        group_id = cur.fetchone()["id"]

        if grupo.miembros:
            cur.executemany(
                "INSERT INTO group_members (id_user, id_group) VALUES (%s, %s);",
                [(uid, group_id) for uid in grupo.miembros]
            )

        conn.commit()

    return {"ok": True, "group_id": group_id, "name": grupo.name, "miembros": grupo.miembros}


@app.post("/groups/{group_id}/members")
def agregar_miembro(group_id: int, body: AgregarMiembro, payload: dict = Depends(verificar_token)):
    conn = get_conn()

    with conn.cursor() as cur:

        cur.execute("SELECT id FROM groups WHERE id = %s;", (group_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Grupo no encontrado")

        cur.execute("SELECT id FROM users WHERE id = %s;", (body.user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cur.execute(
            """
            INSERT INTO group_members (id_user, id_group)
            VALUES (%s, %s)
            ON CONFLICT ON CONSTRAINT uq_group_member DO NOTHING
            RETURNING id_user;
            """,
            (body.user_id, group_id)
        )
        inserted = cur.fetchone()
        conn.commit()

    if not inserted:
        raise HTTPException(status_code=400, detail="El usuario ya es miembro del grupo")

    return {"ok": True, "group_id": group_id, "user_id": body.user_id}


@app.get("/groups/{group_id}/messages")
def get_group_messages_for_group(group_id: int, payload: dict = Depends(verificar_token)):
    user_id = int(payload["sub"])
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM group_members WHERE id_group = %s AND id_user = %s;",
            (group_id, user_id),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=403, detail="No eres miembro de este grupo")

        cur.execute(
            """
            SELECT m.id, m.sender_id, u.name AS sender_name,
                   m.group_id, g.name AS group_name,
                   m.ciphertext, m.encrypted_key, m.nonce, m.auth_tag,
                   m.created_at
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            JOIN groups g ON g.id = m.group_id
            WHERE m.group_id = %s AND (m.recipient_id = %s OR m.sender_id = %s)
            ORDER BY m.created_at ASC;
            """,
            (group_id, user_id, user_id),
        )
        rows = cur.fetchall()
    return {"group_id": group_id, "messages": rows}


@app.get("/users")
def list_users(payload: dict = Depends(verificar_token)):
    current_user_id = int(payload["sub"])
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, email FROM users WHERE id != %s AND id != 1 ORDER BY name ASC;",
            (current_user_id,),
        )
        rows = cur.fetchall()
    return {"users": rows}


@app.get("/users/me")
def get_me(payload: dict = Depends(verificar_token)):
    user_id = int(payload["sub"])
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, email, created_at FROM users WHERE id = %s;", (user_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return row


@app.get("/messages/{user_id}/conversation/{other_user_id}")
def get_conversation(user_id: int, other_user_id: int, payload: dict = Depends(verificar_token)):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT m.id, m.sender_id, u.name AS sender_name,
                   m.ciphertext, m.encrypted_key, m.nonce, m.auth_tag,
                   m.created_at
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            WHERE (m.recipient_id = %s AND m.sender_id = %s AND m.group_id IS NULL)
               OR (m.recipient_id = %s AND m.sender_id = %s AND m.group_id IS NULL)
            ORDER BY m.created_at ASC;
            """,
            (user_id, other_user_id, other_user_id, user_id),
        )
        rows = cur.fetchall()
    return {"user_id": user_id, "other_user_id": other_user_id, "messages": rows}


@app.get("/messages/{user_id}/conversations")
def get_conversations(user_id: int, payload: dict = Depends(verificar_token)):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                partner.id AS user_id,
                partner.name AS user_name,
                partner.email AS user_email,
                latest.id AS last_msg_id,
                latest.sender_id AS last_sender_id,
                latest.ciphertext AS last_ciphertext,
                latest.created_at AS last_created_at
            FROM (
                SELECT DISTINCT
                    CASE WHEN m.sender_id = %s THEN m.recipient_id ELSE m.sender_id END AS partner_id
                FROM messages m
                WHERE (m.sender_id = %s OR m.recipient_id = %s) AND m.group_id IS NULL
            ) p
            JOIN LATERAL (
                SELECT id, sender_id, ciphertext, created_at
                FROM messages
                WHERE ((sender_id = %s AND recipient_id = p.partner_id) OR (sender_id = p.partner_id AND recipient_id = %s))
                  AND group_id IS NULL
                ORDER BY created_at DESC
                LIMIT 1
            ) latest ON TRUE
            JOIN users partner ON partner.id = p.partner_id
            ORDER BY latest.created_at DESC;
            """,
            (user_id, user_id, user_id, user_id, user_id),
        )
        rows = cur.fetchall()
    return {"user_id": user_id, "conversations": rows}


@app.delete("/messages/{message_id}")
def delete_message(message_id: int, payload: dict = Depends(verificar_token)):
    user_id = int(payload["sub"])
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, sender_id, recipient_id FROM messages WHERE id = %s;",
            (message_id,),
        )
        msg = cur.fetchone()
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    if msg["sender_id"] != user_id and msg["recipient_id"] != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este mensaje")
    # Soft delete: mark as deleted
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM messages WHERE id = %s;",
            (message_id,),
        )
        conn.commit()
    return {"ok": True, "detail": "Mensaje eliminado"}


# Módulo 4: MFA
class MFAEnableRequest(BaseModel):
    pass

class MFALoginRequest(BaseModel):
    email: str
    contrasena: str
    totp_code: str


# Módulo 3: Verificación de firma
class VerifyRequest(BaseModel):
    password: str

@app.post("/messages/{msg_id}/verify")
def verify_message_signature(msg_id: int, body: VerifyRequest, payload: dict = Depends(verificar_token)):
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT m.ciphertext, m.encrypted_key, m.nonce, m.auth_tag,
                   m.signature, m.sender_id,
                   u_sender.public_key AS sender_public_key,
                   u_recipient.encrypted_private_key AS recipient_encrypted_private_key
            FROM messages m
            JOIN users u_sender    ON u_sender.id    = m.sender_id
            JOIN users u_recipient ON u_recipient.id = m.recipient_id
            WHERE m.id = %s;
            """,
            (msg_id,),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    if not row["signature"]:
        raise HTTPException(status_code=400, detail="Este mensaje no tiene firma digital")

    try:
        private_key_recipient = cargar_llave_privada(body.password, row["recipient_encrypted_private_key"])
    except Exception:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    try:
        plaintext = descifrar_mensaje(
            {
                "ciphertext":    row["ciphertext"],
                "encrypted_key": row["encrypted_key"],
                "nonce":         row["nonce"],
                "auth_tag":      row["auth_tag"],
            },
            private_key_recipient,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="No se pudo descifrar el mensaje")

    try:
        verificar_firma(plaintext, row["signature"], row["sender_public_key"])
        verified = True
        detail = "Firma válida: el mensaje es auténtico."
    except SignatureInvalidError as e:
        verified = False
        detail = f"FIRMA INVÁLIDA: {str(e)}"

    return {
        "message_id": msg_id,
        "sender_id":  row["sender_id"],
        "verified":   verified,
        "detail":     detail,
        "plaintext":  plaintext if verified else None,
    }


@app.get("/blockchain/verify")
def verify_blockchain(payload: dict = Depends(verificar_token)):

    conn = get_conn()

    with conn.cursor() as cur:

        cur.execute("""
            SELECT block_index, hash, previous_hash
            FROM blockchain
            ORDER BY block_index ASC;
        """)

        blocks = cur.fetchall()

    if not blocks:
        return {
            "valid": False,
            "detail": "Blockchain vacía"
        }


    genesis = blocks[0]

    if genesis["previous_hash"] != "0" * 64:
        return {
            "valid": False,
            "detail": "Genesis block inválido"
        }

    for i in range(1, len(blocks)):

        current_block = blocks[i]
        previous_block = blocks[i - 1]

        if current_block["previous_hash"] != previous_block["hash"]:

            return {
                "valid": False,
                "detail": (
                    f"Bloque {current_block['block_index']} "
                    f"no apunta correctamente al bloque anterior"
                )
            }

    return {
        "valid": True,
        "detail": "Blockchain válida"
    }

# ─── Módulo 4: MFA ───────────────────────────────────────────────────────────
@app.post("/auth/mfa/enable")
def enable_mfa(payload: dict = Depends(verificar_token)):
    user_id = int(payload["sub"])
    conn = get_conn()

    secret = pyotp.random_base32()

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET totp_secret = %s WHERE id = %s RETURNING email;",
            (secret, user_id)
        )
        row = cur.fetchone()
        conn.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=row["email"],
        issuer_name="VaultChain"
    )

    qr = qrcode.make(uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "secret": secret,
        "qr_code": qr_b64,
        "uri": uri
    }


@app.post("/auth/mfa/verify")
def verify_mfa_code(user_id: int, totp_code: str, payload: dict = Depends(verificar_token)):
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT totp_secret FROM users WHERE id = %s;",
            (user_id,)
        )
        row = cur.fetchone()

    if not row or not row["totp_secret"]:
        raise HTTPException(status_code=400, detail="MFA no activado para este usuario")

    totp = pyotp.TOTP(row["totp_secret"])
    if not totp.verify(totp_code):
        raise HTTPException(status_code=401, detail="Código TOTP inválido o expirado")

    return {"ok": True, "detail": "Código TOTP válido"}


@app.post("/auth/mfa/login")
def login_with_mfa(body: MFALoginRequest):
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, contrasenas, totp_secret FROM users WHERE email = %s;",
            (body.email,),
        )
        result = cur.fetchone()

    if not result:
        raise HTTPException(status_code=400, detail="Usuario no existe")

    if not verify_password(body.contrasena, result["contrasenas"]):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    if not result["totp_secret"]:
        raise HTTPException(status_code=400, detail="MFA no activado para este usuario")

    totp = pyotp.TOTP(result["totp_secret"])
    if not totp.verify(body.totp_code):
        raise HTTPException(status_code=401, detail="Código TOTP inválido")

    token = crear_token(result["id"], result["email"])
    refresh = crear_refresh_token(result["id"], result["email"])
    return {"access_token": token, "refresh_token": refresh, "token_type": "bearer"}
