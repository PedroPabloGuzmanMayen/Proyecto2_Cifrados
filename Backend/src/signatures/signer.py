import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256


def firmar_mensaje(plaintext: str, private_key: RSA.RsaKey) -> str:
    # Calcular el hash SHA-256 del mensaje original
    mensaje_hash = SHA256.new(plaintext.encode("utf-8"))

    # Firmar con RSA-PSS
    firma = pss.new(private_key).sign(mensaje_hash)

    # Codificar en Base64 para almacenamiento
    return base64.b64encode(firma).decode("utf-8")


def obtener_hash_mensaje(plaintext: str) -> str:
    return SHA256.new(plaintext.encode("utf-8")).hexdigest()
