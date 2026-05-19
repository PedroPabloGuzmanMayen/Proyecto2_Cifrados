import os
import base64
from datetime import datetime, timezone
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256


def cifrar_mensaje(plaintext: str, public_key_pem: str, aes_key: bytes) -> dict:
    """
    Criterio 1: Cifrado AES-256-GCM con nonce único por mensaje
    Criterio 2: Clave AES cifrada con RSA-OAEP
    """
    # Nonce único
    nonce = os.urandom(16)

    # Cifrar con AES-256-GCM usando el nonce único
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    ciphertext, auth_tag = cipher_aes.encrypt_and_digest(plaintext.encode("utf-8"))

    # Cifrar la clave AES con RSA-OAEP usando la llave pública del destinatario
    recipient_key = RSA.import_key(public_key_pem)
    cipher_rsa = PKCS1_OAEP.new(recipient_key, hashAlgo=SHA256)
    encrypted_key = cipher_rsa.encrypt(aes_key)

    return {
        "ciphertext":    base64.b64encode(ciphertext).decode("utf-8"),
        "encrypted_key": base64.b64encode(encrypted_key).decode("utf-8"),
        "nonce":         base64.b64encode(nonce).decode("utf-8"),
        "auth_tag":      base64.b64encode(auth_tag).decode("utf-8"),
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    }

def generar_llave_aes() -> bytes:
    return os.urandom(32)