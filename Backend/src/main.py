import os
from fastapi import FastAPI, HTTPException,Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from auth.Hashing import hash_password, verify_password
from auth.key_generator import generar_par_llaves
from datetime import datetime, timezone, timedelta
import jwt
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
#CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

secret = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

# JWT
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

# 🔌 Conexión
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

# 📦 Schema
class Usuario(BaseModel):
    name: str
    email: EmailStr
    contrasenas: str

class Usuario_Login(BaseModel):
    email: str
    contrasena:str


# 🚀 Endpoint
@app.post("/registro")
def registrar(usuario: Usuario):

    conn = get_conn()
    password = hash_password(usuario.contrasenas)

    public, private = generar_par_llaves(usuario.contrasenas)

    with conn.cursor() as cur:
        
        # verificar si ya existe
        cur.execute("SELECT * FROM users WHERE email = %s;", (usuario.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Correo ya registrado")
        
        # insertar usuario
        cur.execute(
            "INSERT INTO users (name, email, contrasenas, public_key, encrypted_private_key, created_at ) VALUES (%s, %s, %s, %s, %s, %s);",
            (usuario.name, usuario.email, password, public, private, datetime.utcnow())
        )
        conn.commit()

    return {"ok": True}

# LOGIN
@app.post("/login")
def login(credenciales: Usuario_Login):
    conn = get_conn()
    with conn.cursor() as cur:

        cur.execute("SELECT id, email, contrasenas FROM users WHERE email = (%s);", (credenciales.email, ) )
        result = cur.fetchone() 

    if result is None:
        raise HTTPException(status_code=400, detail="usuario no existe :(")
    
    user_id = result["id"]
    email = result["email"]
    hashed_password = result["contrasenas"]

    if not verify_password(credenciales.contrasena, hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta >:()")
    
    token = crear_token(user_id, email)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.get("/users/{user_id}/key")
def obtener_llave_publica(user_id: int):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT public_key FROM users WHERE id = %s;", (user_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"user_id": user_id, "public_key": row["public_key"]}
