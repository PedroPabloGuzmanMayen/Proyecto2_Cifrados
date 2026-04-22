import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import psycopg
from dotenv import load_dotenv
from auth.Hashing import hash_password
from auth.key_generator import generar_par_llaves
from datetime import datetime

load_dotenv()

app = FastAPI()

# 🔌 Conexión
conn = psycopg.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)

# 📦 Schema
class Usuario(BaseModel):
    name: str
    email: EmailStr
    contrasenas: str


# 🚀 Endpoint
@app.post("/registro")
def registrar(usuario: Usuario):


    password = hash_password(usuario.contrasenas)

    public, private = generar_par_llaves(usuario.contrasenas)

    with conn.cursor() as cur:
        
        # verificar si ya existe
        cur.execute("SELECT * FROM users WHERE email = %s;", (usuario.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Correo ya registrado")
        
        # insertar usuario
        cur.execute(
            "INSERT INTO users (name, email, contrasenas, public_key, encrypted_private_key  ) VALUES (%s, %s, %s);",
            (usuario.name, usuario.email, password, public, private, datetime.utcnow())
        )
        conn.commit()

    return {"ok": True}