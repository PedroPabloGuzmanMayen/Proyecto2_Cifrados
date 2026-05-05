import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256


def descifrar_mensaje(encrypted_data: dict, private_key: RSA.RsaKey) -> str:
    """
    Descifra un mensaje cifrado con el esquema híbrido RSA-OAEP + AES-256-GCM.

    Parámetros:
        encrypted_data: dict con claves:
            - ciphertext     (str, base64)
            - encrypted_key  (str, base64)
            - nonce          (str, base64)
            - auth_tag       (str, base64)
        private_key: llave privada RSA (objeto RSA.RsaKey)

    Retorna:
        El texto plano descifrado (str).

    Lanza:
        ValueError  – si el auth_tag no coincide (mensaje alterado).
        Exception   – si la llave privada no corresponde al destinatario.
    """
    # Decodificar todos los campos de base64
    ciphertext    = base64.b64decode(encrypted_data["ciphertext"])
    encrypted_key = base64.b64decode(encrypted_data["encrypted_key"])
    nonce         = base64.b64decode(encrypted_data["nonce"])
    auth_tag      = base64.b64decode(encrypted_data["auth_tag"])

    # Paso 1 – Descifrar la clave AES con la llave privada RSA-OAEP
    cipher_rsa = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
    aes_key = cipher_rsa.decrypt(encrypted_key)

    # Paso 2 – Descifrar el mensaje con AES-256-GCM
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)

    # decrypt_and_verify lanza ValueError si el auth_tag no coincide
    plaintext_bytes = cipher_aes.decrypt_and_verify(ciphertext, auth_tag)

    return plaintext_bytes.decode("utf-8")