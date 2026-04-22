import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import psycopg
from dotenv import load_dotenv

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
    with conn.cursor() as cur:
        
        # verificar si ya existe
        cur.execute("SELECT * FROM users WHERE email = %s;", (usuario.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Correo ya registrado")
        
        # insertar usuario
        cur.execute(
            "INSERT INTO users (name, email, contrasenas) VALUES (%s, %s, %s);",
            (usuario.name, usuario.email, usuario.contrasenas)
        )
        conn.commit()

    return {"ok": True}