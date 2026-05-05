"""
Tests unitarios del módulo de cifrado/descifrado híbrido.

Cubre:
  1. Ciclo completo cifrar → descifrar devuelve el texto original.
  2. Auth tag corrupto lanza ValueError (integridad violada).
  3. Llave privada incorrecta lanza excepción (confidencialidad).
  4. Mensajes distintos producen ciphertexts distintos (nonce único).
  5. El payload cifrado contiene todos los campos requeridos.
"""

import base64
import pytest
from Crypto.PublicKey import RSA

from crypto.hybrid_cipher import cifrar_mensaje
from crypto.hybrid_decypher import descifrar_mensaje


# ─── Fixture: par de llaves de prueba (2048 bits) ────────────────────────────
@pytest.fixture(scope="module")
def key_pair():
    """Genera un par RSA una sola vez para todos los tests del módulo."""
    key = RSA.generate(2048)
    public_pem  = key.publickey().export_key().decode("utf-8")
    private_key = key
    return public_pem, private_key


# ─── Test 1: ciclo completo cifrar → descifrar ───────────────────────────────
def test_cifrado_descifrado_correcto(key_pair):
    """El texto descifrado debe ser idéntico al texto original."""
    public_pem, private_key = key_pair
    mensaje_original = "Hola, esto es un mensaje secreto 🔒"

    encrypted = cifrar_mensaje(mensaje_original, public_pem)
    resultado  = descifrar_mensaje(encrypted, private_key)

    assert resultado == mensaje_original


# ─── Test 2: auth tag corrupto → ValueError ──────────────────────────────────
def test_auth_tag_corrupto_lanza_error(key_pair):
    """
    Alterar el auth_tag debe impedir el descifrado y lanzar ValueError.
    Esto garantiza que AES-GCM detecta manipulación del mensaje.
    """
    public_pem, private_key = key_pair
    encrypted = cifrar_mensaje("Mensaje importante", public_pem)

    # Decodificar, cambiar el primer byte y re-encodear
    tag_bytes     = bytearray(base64.b64decode(encrypted["auth_tag"]))
    tag_bytes[0] ^= 0xFF                                   # flip bits
    encrypted["auth_tag"] = base64.b64encode(bytes(tag_bytes)).decode()

    with pytest.raises(ValueError):
        descifrar_mensaje(encrypted, private_key)


# ─── Test 3: llave privada incorrecta → excepción ────────────────────────────
def test_llave_privada_incorrecta_falla(key_pair):
    """
    Intentar descifrar con una llave privada diferente debe lanzar excepción,
    porque la clave AES cifrada con RSA-OAEP no podrá recuperarse.
    """
    public_pem, _ = key_pair
    encrypted = cifrar_mensaje("Mensaje confidencial", public_pem)

    # Generamos una llave RSA completamente distinta
    otra_llave_privada = RSA.generate(2048)

    with pytest.raises(Exception):
        descifrar_mensaje(encrypted, otra_llave_privada)


# ─── Test 4: nonce único por mensaje ─────────────────────────────────────────
def test_nonce_unico_por_mensaje(key_pair):
    """
    Cifrar el mismo texto dos veces debe producir nonces distintos,
    lo que garantiza que no se reutiliza material criptográfico.
    """
    public_pem, _ = key_pair
    texto = "Mismo mensaje, diferente nonce"

    enc1 = cifrar_mensaje(texto, public_pem)
    enc2 = cifrar_mensaje(texto, public_pem)

    assert enc1["nonce"]      != enc2["nonce"],      "Los nonces deben ser únicos"
    assert enc1["ciphertext"] != enc2["ciphertext"], "Los ciphertexts deben diferir"


# ─── Test 5: estructura del payload cifrado ──────────────────────────────────
def test_payload_contiene_campos_requeridos(key_pair):
    """
    El dict devuelto por cifrar_mensaje debe contener todos los campos
    necesarios para el descifrado: ciphertext, encrypted_key, nonce, auth_tag.
    """
    public_pem, _ = key_pair
    encrypted = cifrar_mensaje("Verificar estructura", public_pem)

    campos_requeridos = {"ciphertext", "encrypted_key", "nonce", "auth_tag", "timestamp"}
    assert campos_requeridos.issubset(encrypted.keys())

    # Además cada campo debe ser un string base64 no vacío
    for campo in ("ciphertext", "encrypted_key", "nonce", "auth_tag"):
        assert isinstance(encrypted[campo], str)
        assert len(encrypted[campo]) > 0
        # Verificar que es base64 válido
        base64.b64decode(encrypted[campo])  # no debe lanzar excepción