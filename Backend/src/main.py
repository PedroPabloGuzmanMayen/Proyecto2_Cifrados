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
from signatures.signer import firmar_mensaje
from signatures.verifier import verificar_firma, SignatureInvalidError
from datetime import datetime, timezone, timedelta
import jwt
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

secret = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60


# ─── JWT ────────────────────────────────────────────────────────────────────
def crear_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def verificar_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
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
            "SELECT id, email, contrasenas FROM users WHERE email = %s;",
            (credenciales.email,),
        )
        result = cur.fetchone()

    if result is None:
        raise HTTPException(status_code=400, detail="Usuario no existe")

    if not verify_password(credenciales.contrasena, result["contrasenas"]):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    token = crear_token(result["id"], result["email"])
    return {"access_token": token, "token_type": "bearer"}


@app.get("/users/{user_id}/key")
def obtener_llave_publica(user_id: int):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT public_key FROM users WHERE id = %s;", (user_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"user_id": user_id, "public_key": row["public_key"]}


@app.post("/individual_message/")
def send_message(mensaje: mensaje_model):
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

    return {"ok": True, "message": "Mensaje enviado con éxito"}


# ─── NUEVO: GET mensajes cifrados ────────────────────────────────────────────
@app.get("/messages/{user_id}")
def get_messages(user_id: int):
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
def decrypt_message(user_id: int, message_id: int, body: DecryptRequest):
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

    # 2 – Recuperar el mensaje cifrado
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ciphertext, encrypted_key, nonce, auth_tag
            FROM messages
            WHERE id = %s AND recipient_id = %s;
            """,
            (message_id, user_id),
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


@app.post("/group_message")

def send_message_to_group(mensaje: mensaje_model):
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
                INSERT INTO messages (sender_id, recipient_id, group_id, ciphertext, encrypted_key, nonce, auth_tag)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    mensaje.sender,
                    i['user_id'],
                    mensaje.recipient,
                    encrypted_data["ciphertext"],
                    encrypted_data["encrypted_key"],
                    encrypted_data["nonce"],
                    encrypted_data["auth_tag"],
                )
            )
            conn.commit()
    return {"ok": True, "message": "mensaje enviado con éxito"}

@app.post("/groups")
def crear_grupo(grupo: GrupoCreate):
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
def agregar_miembro(group_id: int, body: AgregarMiembro):
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

# Módulo 3: Verificación de firma
class VerifyRequest(BaseModel):
    password: str

@app.post("/messages/{msg_id}/verify")
def verify_message_signature(msg_id: int, body: VerifyRequest):
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
