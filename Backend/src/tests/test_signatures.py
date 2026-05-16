import base64
import pytest
from Crypto.PublicKey import RSA
from signatures.signer import firmar_mensaje, obtener_hash_mensaje
from signatures.verifier import verificar_firma, SignatureInvalidError

# Fixture: par de llaves RSA de prueba
@pytest.fixture(scope="module")
def key_pair():
    """Genera un par RSA-2048 una sola vez para todos los tests."""
    key = RSA.generate(2048)
    return key, key.publickey().export_key().decode("utf-8")


# Test 1: firma correcta y verificación exitosa
def test_firma_correcta_verifica_ok(key_pair):
    """
    Flujo:
    firmar con llave privada → verificar con llave pública → True.
    """
    private_key, public_key_pem = key_pair
    plaintext = "Informe de auditoría Q1-2026 confidencial"

    firma = firmar_mensaje(plaintext, private_key)
    resultado = verificar_firma(plaintext, firma, public_key_pem)

    assert resultado is True


# Test 2: mensaje alterado prueba de SignatureInvalidError
def test_mensaje_alterado_falla(key_pair):
    """
    Si el plaintext fue modificado después de firmar,
    la verificación debe lanzar SignatureInvalidError.
    Esto garantiza integridad del mensaje.
    """
    private_key, public_key_pem = key_pair
    plaintext_original = "Presupuesto aprobado: Q500,000"

    firma = firmar_mensaje(plaintext_original, private_key)

    # Simulamos que alguien alteró el mensaje
    plaintext_alterado = "Presupuesto aprobado: Q5,000,000"

    with pytest.raises(SignatureInvalidError):
        verificar_firma(plaintext_alterado, firma, public_key_pem)


# Test 3: llave pública incorrecta prueba de SignatureInvalidError
def test_llave_publica_incorrecta_falla(key_pair):
    """
    Verificar con la llave pública de otro usuario debe fallar.
    Garantiza autenticidad: solo el remitente real pudo firmar.
    """
    private_key, _ = key_pair
    plaintext = "Contrato de servicios #2026-001"

    firma = firmar_mensaje(plaintext, private_key)

    # Generamos otra llave completamente distinta
    otra_llave = RSA.generate(2048)
    otra_public_pem = otra_llave.publickey().export_key().decode("utf-8")

    with pytest.raises(SignatureInvalidError):
        verificar_firma(plaintext, firma, otra_public_pem)


# Test 4: firma Base64 corrupta → ValueError
def test_firma_base64_invalido_lanza_error(key_pair):
    """
    Enviar basura como firma debe lanzar ValueError,
    no un crash silencioso ni un False.
    """
    _, public_key_pem = key_pair

    with pytest.raises(ValueError):
        verificar_firma("Cualquier mensaje", "esto-no-es-base64!!!", public_key_pem)

