from Crypto.PublicKey import RSA
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
import base64

def generar_par_llaves(password: str, bits: int = 2048) -> tuple[str, str]:
    # Generar par de llaves
    key = RSA.generate(bits)

    salt = get_random_bytes(16)
    derived_key = scrypt(
        password.encode(),
        salt,
        key_len=32,
        N=2**17,
        r=8,
        p=1
    )

    # Cifrar llave privada con clave derivada
    private_key_encrypted = key.export_key(
        passphrase=derived_key,
        pkcs=8,
        protection="scryptAndAES256-CBC"
    )

    # Llave pública en PEM plano
    public_key_pem = key.publickey().export_key().decode("utf-8")

    # Empaquetar salt + llave cifrada en Base64 para guardar en DB
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    encrypted_b64 = base64.b64encode(private_key_encrypted).decode("utf-8")
    encrypted_private_key = f"{salt_b64}:{encrypted_b64}"

    return public_key_pem, encrypted_private_key


def cargar_llave_privada(password: str, encrypted_private_key: str) -> RSA.RsaKey:
    salt_b64, encrypted_b64 = encrypted_private_key.split(":")
    salt = base64.b64decode(salt_b64)
    private_key_encrypted = base64.b64decode(encrypted_b64)

    derived_key = scrypt(
        password.encode(),
        salt,
        key_len=32,
        N=2**17,
        r=8,
        p=1
    )

    return RSA.import_key(private_key_encrypted, passphrase=derived_key)


# Prueba
if __name__ == "__main__":
    password = "MiContraseña_Segura123!"

    print("VaultChain – Prueba de Generación de Llaves")

    pub, enc_priv = generar_par_llaves(password)
    print(f"\nLlave pública (primeros 60 chars):\n{pub[:60]}...")
    print(f"\nLlave privada cifrada (primeros 60 chars):\n{enc_priv[:60]}...")

    # Verificar que se puede recuperar
    priv = cargar_llave_privada(password, enc_priv)
    print(f"\nLlave privada recuperada correctamente: {priv.has_private()}")