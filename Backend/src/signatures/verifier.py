import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256


class SignatureInvalidError(Exception):
    pass


def verificar_firma(plaintext: str, firma_b64: str, public_key_pem: str) -> bool:
    # Reconstruir el hash del mensaje
    mensaje_hash = SHA256.new(plaintext.encode("utf-8"))

    # Decodificar la firma desde Base64
    try:
        firma_bytes = base64.b64decode(firma_b64)
    except Exception:
        raise ValueError("La firma no es Base64 válido.")

    # Cargar la llave pública y verificar
    public_key = RSA.import_key(public_key_pem)
    verificador = pss.new(public_key)

    try:
        verificador.verify(mensaje_hash, firma_bytes)
        return True
    except (ValueError, TypeError):
        raise SignatureInvalidError(
            "Firma inválida: el mensaje puede haber sido alterado "
            "o no corresponde al remitente declarado."
        )
