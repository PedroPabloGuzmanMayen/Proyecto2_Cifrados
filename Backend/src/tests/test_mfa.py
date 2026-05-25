import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import sys, os, types, pyotp

# Mocks
def _mock(name, *attrs):
    m = types.ModuleType(name)
    for a in attrs:
        setattr(m, a, MagicMock())
    return m

sys.modules.update({
    "auth":                  types.ModuleType("auth"),
    "auth.Hashing":          _mock("auth.Hashing", "hash_password", "verify_password"),
    "auth.key_generator":    _mock("auth.key_generator", "generar_par_llaves", "cargar_llave_privada"),
    "crypto":                types.ModuleType("crypto"),
    "crypto.hybrid_cipher":  _mock("crypto.hybrid_cipher", "cifrar_mensaje", "generar_llave_aes"),
    "crypto.hybrid_decypher":_mock("crypto.hybrid_decypher", "descifrar_mensaje"),
    "signatures":            types.ModuleType("signatures"),
    "signatures.signer":     _mock("signatures.signer", "firmar_mensaje", "obtener_hash_mensaje"),
    "psycopg":               _mock("psycopg", "connect"),
    "psycopg.rows":          _mock("psycopg.rows", "dict_row"),
    "dotenv":                _mock("dotenv", "load_dotenv"),
})

# mock signatures.verifier
verifier_mod = types.ModuleType("signatures.verifier")
class SignatureInvalidError(Exception): pass
verifier_mod.verificar_firma      = MagicMock()
verifier_mod.SignatureInvalidError = SignatureInvalidError
sys.modules["signatures.verifier"] = verifier_mod

# mock blockchain
chain_mod = types.ModuleType("blockchain.chain")
class FakeBlockchain:
    def create_genesis_block(self):
        b = MagicMock()
        b.hash = "a" * 64
        b.previous_hash = "0" * 64
        b.nonce = 0
        b.data = {"sender_id": 1, "recipient_id": 1, "message_hash": "x"}
        return b
chain_mod.Blockchain = FakeBlockchain
sys.modules["blockchain"]       = types.ModuleType("blockchain")
sys.modules["blockchain.chain"] = chain_mod

# mock jwt
import jwt as _real_jwt
jwt_mock = types.ModuleType("jwt")
jwt_mock.encode                = MagicMock(return_value="fake.jwt.token")
jwt_mock.decode                = MagicMock(return_value={"sub": "1", "email": "a@b.com"})
jwt_mock.ExpiredSignatureError = _real_jwt.ExpiredSignatureError
jwt_mock.InvalidTokenError     = _real_jwt.InvalidTokenError
sys.modules["jwt"] = jwt_mock

for k, v in {"JWT_SECRET":"test","POSTGRES_HOST":"localhost","POSTGRES_PORT":"5432",
             "POSTGRES_DB":"vaultchain","POSTGRES_USER":"postgres","POSTGRES_PASSWORD":"postgres"}.items():
    os.environ.setdefault(k, v)

import main as app_module
from main import app

client = TestClient(app, raise_server_exceptions=False)
mock_verify = sys.modules["auth.Hashing"].verify_password

# Helpers
def cur(fetchone=None):
    c = MagicMock()
    c.__enter__ = lambda s: s
    c.__exit__  = MagicMock(return_value=False)
    c.fetchone  = MagicMock(return_value=fetchone)
    c.fetchall  = MagicMock(return_value=[])
    return c

def conn(*cursors):
    c = MagicMock()
    c.closed = False
    s = list(cursors)
    c.cursor = lambda: s.pop(0) if len(s) > 1 else s[0]
    return c

HEADERS = {"Authorization": "Bearer fake.jwt.token"}


class TestMFA(unittest.TestCase):

    # /auth/mfa/enable
    def test_enable_retorna_secret_qr_uri(self):
        with patch.object(app_module, "get_conn", return_value=conn(cur({"email": "u@test.com"}))):
            r = client.post("/auth/mfa/enable", headers=HEADERS)
        self.assertEqual(r.status_code, 200)
        for campo in ["secret", "qr_code", "uri"]:
            self.assertIn(campo, r.json())

    def test_enable_sin_token_retorna_401(self):
        r = client.post("/auth/mfa/enable")
        self.assertEqual(r.status_code, 401)

    def test_enable_usuario_no_encontrado_retorna_404(self):
        with patch.object(app_module, "get_conn", return_value=conn(cur(None))):
            r = client.post("/auth/mfa/enable", headers=HEADERS)
        self.assertEqual(r.status_code, 404)

    # /auth/mfa/verify
    def test_verify_codigo_valido(self):
        secret = pyotp.random_base32()
        codigo = pyotp.TOTP(secret).now()
        with patch.object(app_module, "get_conn", return_value=conn(cur({"totp_secret": secret}))):
            r = client.post(f"/auth/mfa/verify?user_id=1&totp_code={codigo}")
        self.assertEqual(r.status_code, 200)

    def test_verify_codigo_invalido_retorna_401(self):
        with patch.object(app_module, "get_conn", return_value=conn(cur({"totp_secret": pyotp.random_base32()}))):
            r = client.post("/auth/mfa/verify?user_id=1&totp_code=000000")
        self.assertEqual(r.status_code, 401)

    def test_verify_sin_mfa_retorna_400(self):
        with patch.object(app_module, "get_conn", return_value=conn(cur({"totp_secret": None}))):
            r = client.post("/auth/mfa/verify?user_id=1&totp_code=123456")
        self.assertEqual(r.status_code, 400)

    # /auth/mfa/login
    def test_mfa_login_exitoso(self):
        secret = pyotp.random_base32()
        mock_verify.return_value = True
        with patch.object(app_module, "get_conn", return_value=conn(cur(
            {"id": 1, "email": "u@test.com", "contrasenas": "h", "totp_secret": secret}
        ))):
            r = client.post("/auth/mfa/login", json={
                "email": "u@test.com", "contrasena": "pass",
                "totp_code": pyotp.TOTP(secret).now()
            })
        self.assertEqual(r.status_code, 200)
        self.assertIn("access_token", r.json())

    def test_mfa_login_codigo_invalido_retorna_401(self):
        mock_verify.return_value = True
        with patch.object(app_module, "get_conn", return_value=conn(cur(
            {"id": 1, "email": "u@test.com", "contrasenas": "h", "totp_secret": pyotp.random_base32()}
        ))):
            r = client.post("/auth/mfa/login", json={
                "email": "u@test.com", "contrasena": "pass", "totp_code": "000000"
            })
        self.assertEqual(r.status_code, 401)

    # /login con MFA
    def test_login_detecta_mfa_activo(self):
        mock_verify.return_value = True
        with patch.object(app_module, "get_conn", return_value=conn(cur(
            {"id": 1, "email": "u@test.com", "contrasenas": "h", "totp_secret": "ACTIVO"}
        ))):
            r = client.post("/login", json={"email": "u@test.com", "contrasena": "pass"})
        self.assertTrue(r.json()["mfa_required"])

    def test_login_sin_mfa_retorna_token(self):
        mock_verify.return_value = True
        with patch.object(app_module, "get_conn", return_value=conn(cur(
            {"id": 1, "email": "u@test.com", "contrasenas": "h", "totp_secret": None}
        ))):
            r = client.post("/login", json={"email": "u@test.com", "contrasena": "pass"})
        self.assertIn("access_token", r.json())


if __name__ == "__main__":
    unittest.main(verbosity=2)