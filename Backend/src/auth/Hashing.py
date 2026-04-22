from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# Parametros
_hasher = PasswordHasher(
    time_cost=2,       
    memory_cost=65536, # 64 MB
    parallelism=2,     # hilos
    hash_len=32,
    salt_len=16,
    type=Type.ID
)


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        _hasher.verify(hashed_password, plain_password)
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    return _hasher.check_needs_rehash(hashed_password)



# Prueba
if __name__ == "__main__":
    test_password = "MiContraseña_Segura123!"

    print("  VaultChain – Prueba de Hashing ")

    hashed = hash_password(test_password)
    print(f"\n  Hash generado        : {hashed}")
    print(f"  Verificación correcta  : {verify_password(test_password, hashed)}")
    print(f"  Verificación incorrecta: {verify_password('ContraseñaWrong', hashed)}")
    print(f"  Necesita rehash        : {needs_rehash(hashed)}")
