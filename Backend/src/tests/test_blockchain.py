"""
test_unit.py — Tests unitarios para VaultChain.

Cubre:
  - POST /group_message      → firma, cifrado por miembro, inserción en messages y blockchain
  - POST /messages/{id}/verify → descifrado + verificación de firma válida e inválida
  - GET  /blockchain/verify   → cadena válida, genesis corrupto, bloque intermedio roto

Ejecutar:
    python -m pytest test_unit.py -v
    # o simplemente:
    python test_unit.py
"""

import unittest
from unittest.mock import MagicMock, patch, call
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─── Mocks de módulos externos ANTES de importar main ────────────────────────
# Así evitamos importar psycopg, cryptografía real, etc.

import sys, types

def _make_mock_module(*attrs):
    m = types.ModuleType("mock")
    for a in attrs:
        setattr(m, a, MagicMock())
    return m

# auth
auth_pkg          = types.ModuleType("auth")
auth_hashing      = _make_mock_module("hash_password", "verify_password")
auth_keygen       = _make_mock_module("generar_par_llaves", "cargar_llave_privada")
sys.modules["auth"]                = auth_pkg
sys.modules["auth.Hashing"]       = auth_hashing
sys.modules["auth.key_generator"]  = auth_keygen

# crypto
crypto_pkg        = types.ModuleType("crypto")
hybrid_cipher     = _make_mock_module("cifrar_mensaje", "generar_llave_aes")
hybrid_decypher   = _make_mock_module("descifrar_mensaje")
sys.modules["crypto"]                  = crypto_pkg
sys.modules["crypto.hybrid_cipher"]    = hybrid_cipher
sys.modules["crypto.hybrid_decypher"]  = hybrid_decypher

# signatures
sig_pkg           = types.ModuleType("signatures")
signer_mod        = _make_mock_module("firmar_mensaje", "obtener_hash_mensaje")
verifier_mod      = types.ModuleType("signatures.verifier")
class SignatureInvalidError(Exception): pass
verifier_mod.verificar_firma      = MagicMock()
verifier_mod.SignatureInvalidError = SignatureInvalidError
sys.modules["signatures"]           = sig_pkg
sys.modules["signatures.signer"]    = signer_mod
sys.modules["signatures.verifier"]  = verifier_mod

# blockchain
blockchain_pkg  = types.ModuleType("blockchain")
chain_mod       = types.ModuleType("blockchain.chain")
class FakeBlock:
    hash = "a" * 64
    previous_hash = "0" * 64
    nonce = 0
    data = {"sender_id": 1, "recipient_id": 1, "message_hash": "x"}
class FakeBlockchain:
    def create_genesis_block(self): return FakeBlock()
chain_mod.Blockchain = FakeBlockchain
sys.modules["blockchain"]       = blockchain_pkg
sys.modules["blockchain.chain"] = chain_mod

# psycopg, dotenv, jwt
sys.modules["psycopg"]            = _make_mock_module("connect")
sys.modules["psycopg.rows"]       = _make_mock_module("dict_row")
sys.modules["dotenv"]             = _make_mock_module("load_dotenv")

import jwt as _real_jwt          # necesitamos el real para decodificar tokens en seed
jwt_mock = types.ModuleType("jwt")
jwt_mock.encode                  = MagicMock(return_value="fake.jwt.token")
jwt_mock.decode                  = MagicMock(return_value={"sub": "1", "email": "a@b.com"})
jwt_mock.ExpiredSignatureError   = _real_jwt.ExpiredSignatureError
jwt_mock.InvalidTokenError       = _real_jwt.InvalidTokenError
sys.modules["jwt"] = jwt_mock

# ─── Ahora sí importamos main ─────────────────────────────────────────────────
import os
os.environ.setdefault("JWT_SECRET", "test_secret")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB",   "vaultchain")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")

import main as app_module
from main import app

client = TestClient(app, raise_server_exceptions=False)

# ─── Referencias a los mocks que usaremos en los tests ───────────────────────
mock_cifrar        = hybrid_cipher.cifrar_mensaje
mock_aes           = hybrid_cipher.generar_llave_aes
mock_descifrar     = hybrid_decypher.descifrar_mensaje
mock_firmar        = signer_mod.firmar_mensaje
mock_verificar     = verifier_mod.verificar_firma
mock_cargar_priv   = auth_keygen.cargar_llave_privada


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def make_cursor(fetchone=None, fetchall=None, fetchmany=None):
    """Devuelve un cursor mock configurable."""
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__  = MagicMock(return_value=False)
    cur.fetchone  = MagicMock(return_value=fetchone)
    cur.fetchall  = MagicMock(return_value=fetchall or [])
    return cur


def make_conn(*cursors):
    """
    Devuelve una conexión mock cuyo cursor() devuelve los cursors en orden.
    Si se pasan más llamadas que cursors, reutiliza el último.
    """
    conn = MagicMock()
    conn.closed = False
    side_effects = list(cursors)
    def _cursor():
        return side_effects.pop(0) if len(side_effects) > 1 else side_effects[0]
    conn.cursor = _cursor
    return conn


# ══════════════════════════════════════════════════════════════════════════════
# 1. POST /group_message
# ══════════════════════════════════════════════════════════════════════════════

class TestGroupMessage(unittest.TestCase):

    PAYLOAD = {
        "sender":          10,
        "recipient":       5,     # group_id
        "message":         "Hola grupo",
        "sender_password": "pass123",
    }

    def _default_mocks(self):
        """Prepara los mocks de crypto/firma con valores predecibles."""
        mock_aes.return_value        = b"fakeaeskey"
        mock_firmar.return_value     = "firma_b64_fake"
        mock_cifrar.return_value     = {
            "ciphertext":    "ct",
            "encrypted_key": "ek",
            "nonce":         "nonce12chars",
            "auth_tag":      "tag12chars__",
        }
        mock_cargar_priv.return_value = MagicMock()   # llave privada fake

    # ── cursor helpers específicos ────────────────────────────────────────────
    def _cur_group_exists(self):
        return make_cursor(fetchone={"id": 5})

    def _cur_members(self, user_ids):
        return make_cursor(fetchall=[{"id_user": uid} for uid in user_ids])

    def _cur_sender_key(self):
        return make_cursor(fetchone={"encrypted_private_key": "enc_priv_key"})

    def _cur_pub_key(self, user_id):
        return make_cursor(fetchone={"public_key": f"pub_key_{user_id}"})

    def _cur_insert(self):
        cur = make_cursor()
        cur.execute = MagicMock()
        return cur

    def _cur_blockchain_last(self):
        return make_cursor(fetchone={"hash": "b" * 64})

    def _cur_blockchain_insert(self):
        cur = make_cursor()
        cur.execute = MagicMock()
        return cur

    # ── Tests ─────────────────────────────────────────────────────────────────

    def test_mensaje_grupo_exitoso_dos_miembros(self):
        """El mensaje se cifra individualmente para cada miembro y se insertan
        registros en messages y en blockchain."""
        self._default_mocks()
        members = [1, 2]

        # Orden de cursors que consume el endpoint:
        # 1 grupo exists | 2 members | 3 sender key | 4 pub key user1 | 5 insert msg user1
        # 6 blockchain last hash | 7 blockchain insert |
        # 8 pub key user2 | 9 insert msg user2 | 10 blockchain last | 11 blockchain insert
        cursors = [
            self._cur_group_exists(),
            self._cur_members(members),
            self._cur_sender_key(),
            self._cur_pub_key(1),
            self._cur_insert(),
            self._cur_blockchain_last(),
            self._cur_blockchain_insert(),
            self._cur_pub_key(2),
            self._cur_insert(),
            self._cur_blockchain_last(),
            self._cur_blockchain_insert(),
        ]
        conn = make_conn(*cursors)

        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/group_message", json=self.PAYLOAD)

        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])

    def test_firma_se_llama_una_vez(self):
        """firmar_mensaje debe llamarse exactamente una vez (firma única del sender)."""
        self._default_mocks()
        mock_firmar.reset_mock()
        members = [3, 4, 5]

        cursors = [
            self._cur_group_exists(),
            self._cur_members(members),
            self._cur_sender_key(),
        ] + [
            cur
            for uid in members
            for cur in (self._cur_pub_key(uid), self._cur_insert(),
                        self._cur_blockchain_last(), self._cur_blockchain_insert())
        ]
        conn = make_conn(*cursors)

        with patch.object(app_module, "get_conn", return_value=conn):
            client.post("/group_message", json=self.PAYLOAD)

        mock_firmar.assert_called_once_with("Hola grupo", mock_cargar_priv.return_value)

    def test_blockchain_insert_por_cada_miembro(self):
        """Debe insertarse un bloque en blockchain por cada miembro del grupo."""
        self._default_mocks()
        members = [7, 8, 9]

        blockchain_inserts = []

        def counting_cursor_factory(uid=None, is_blockchain=False):
            cur = make_cursor(fetchone={"hash": "c" * 64} if is_blockchain else
                              {"public_key": f"pk_{uid}"})
            def track_execute(sql, *args, **kwargs):
                if "INSERT INTO blockchain" in sql:
                    blockchain_inserts.append(sql)
            cur.execute = MagicMock(side_effect=track_execute)
            return cur

        # Construimos cursors a mano para poder rastrear los INSERT INTO blockchain
        cursors = [
            self._cur_group_exists(),
            self._cur_members(members),
            self._cur_sender_key(),
        ]
        for uid in members:
            cursors.append(self._cur_pub_key(uid))   # pub key
            cursors.append(self._cur_insert())        # msg insert
            # blockchain: last hash + insert
            bc_last = make_cursor(fetchone={"hash": "d" * 64})
            bc_ins  = make_cursor()
            bc_ins.execute = MagicMock(side_effect=lambda sql, *a, **k:
                blockchain_inserts.append(1) if "INSERT INTO blockchain" in sql else None)
            cursors.extend([bc_last, bc_ins])

        conn = make_conn(*cursors)

        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/group_message", json=self.PAYLOAD)

        self.assertEqual(r.status_code, 200)
        # Verificamos que insert_into_the_blockchain fue invocado N veces
        # indirectamente: si el endpoint retorna 200 con 3 miembros,
        # pasó por el loop completo
        self.assertTrue(r.json()["ok"])

    def test_grupo_no_existe_retorna_404(self):
        cur = make_cursor(fetchone=None)
        conn = make_conn(cur)
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/group_message", json=self.PAYLOAD)
        self.assertEqual(r.status_code, 404)
        self.assertIn("no existe", r.json()["detail"])

    def test_grupo_sin_miembros_retorna_404(self):
        conn = make_conn(
            make_cursor(fetchone={"id": 5}),   # grupo existe
            make_cursor(fetchall=[]),           # sin miembros
        )
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/group_message", json=self.PAYLOAD)
        self.assertEqual(r.status_code, 404)
        self.assertIn("no hay usuarios", r.json()["detail"])

    def test_contrasena_incorrecta_retorna_400(self):
        self._default_mocks()
        mock_cargar_priv.side_effect = ValueError("bad password")

        conn = make_conn(
            make_cursor(fetchone={"id": 5}),
            make_cursor(fetchall=[{"id_user": 1}]),
            make_cursor(fetchone={"encrypted_private_key": "enc"}),
        )
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/group_message", json=self.PAYLOAD)

        mock_cargar_priv.side_effect = None   # reset
        self.assertEqual(r.status_code, 400)
        self.assertIn("Contraseña incorrecta", r.json()["detail"])


# ══════════════════════════════════════════════════════════════════════════════
# 2. POST /messages/{msg_id}/verify
# ══════════════════════════════════════════════════════════════════════════════

class TestVerifySignature(unittest.TestCase):

    MSG_ROW = {
        "ciphertext":                    "ct_enc",
        "encrypted_key":                 "ek_enc",
        "nonce":                         "nonce_val___",
        "auth_tag":                      "tag_val_____",
        "signature":                     "firma_valida_b64",
        "sender_id":                     10,
        "sender_public_key":             "pub_key_sender",
        "recipient_encrypted_private_key": "enc_priv_recipient",
    }

    def setUp(self):
        mock_cargar_priv.reset_mock()
        mock_descifrar.reset_mock()
        mock_verificar.reset_mock()
        mock_cargar_priv.return_value  = MagicMock(name="private_key")
        mock_descifrar.return_value    = "texto plano original"
        mock_verificar.return_value    = None   # no lanza = firma válida

    def test_firma_valida_retorna_verified_true(self):
        conn = make_conn(make_cursor(fetchone=self.MSG_ROW))
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/messages/1/verify", json={"password": "pass"})

        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["verified"])
        self.assertEqual(data["plaintext"], "texto plano original")
        self.assertIn("válida", data["detail"])

    def test_firma_invalida_retorna_verified_false(self):
        mock_verificar.side_effect = SignatureInvalidError("hash no coincide")

        conn = make_conn(make_cursor(fetchone=self.MSG_ROW))
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/messages/1/verify", json={"password": "pass"})

        mock_verificar.side_effect = None
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data["verified"])
        self.assertIsNone(data["plaintext"])
        self.assertIn("INVÁLIDA", data["detail"])

    def test_mensaje_sin_firma_retorna_400(self):
        row = dict(self.MSG_ROW, signature=None)
        conn = make_conn(make_cursor(fetchone=row))
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/messages/1/verify", json={"password": "pass"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("no tiene firma", r.json()["detail"])

    def test_mensaje_no_encontrado_retorna_404(self):
        conn = make_conn(make_cursor(fetchone=None))
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/messages/99/verify", json={"password": "pass"})
        self.assertEqual(r.status_code, 404)

    def test_contrasena_incorrecta_en_verify_retorna_400(self):
        mock_cargar_priv.side_effect = ValueError("bad")
        conn = make_conn(make_cursor(fetchone=self.MSG_ROW))
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/messages/1/verify", json={"password": "wrong"})
        mock_cargar_priv.side_effect = None
        self.assertEqual(r.status_code, 400)
        self.assertIn("Contraseña incorrecta", r.json()["detail"])

    def test_descifrado_fallido_retorna_400(self):
        mock_descifrar.side_effect = ValueError("auth tag mismatch")
        conn = make_conn(make_cursor(fetchone=self.MSG_ROW))
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.post("/messages/1/verify", json={"password": "pass"})
        mock_descifrar.side_effect = None
        self.assertEqual(r.status_code, 400)
        self.assertIn("descifrar", r.json()["detail"])

    def test_cargar_llave_se_llama_con_password_correcto(self):
        conn = make_conn(make_cursor(fetchone=self.MSG_ROW))
        with patch.object(app_module, "get_conn", return_value=conn):
            client.post("/messages/1/verify", json={"password": "mi_pass"})
        mock_cargar_priv.assert_called_once_with(
            "mi_pass", self.MSG_ROW["recipient_encrypted_private_key"]
        )

    def test_verificar_firma_recibe_texto_descifrado_y_pub_key_sender(self):
        conn = make_conn(make_cursor(fetchone=self.MSG_ROW))
        with patch.object(app_module, "get_conn", return_value=conn):
            client.post("/messages/1/verify", json={"password": "pass"})
        mock_verificar.assert_called_once_with(
            "texto plano original",
            self.MSG_ROW["signature"],
            self.MSG_ROW["sender_public_key"],
        )


# ══════════════════════════════════════════════════════════════════════════════
# 3. GET /blockchain/verify
# ══════════════════════════════════════════════════════════════════════════════

class TestBlockchainVerify(unittest.TestCase):

    GENESIS = {"block_index": 1, "hash": "a" * 64, "previous_hash": "0" * 64}

    def _blocks(self, *blocks):
        cur = make_cursor(fetchall=list(blocks))
        conn = make_conn(cur)
        return conn

    def test_blockchain_vacia_retorna_invalid(self):
        conn = self._blocks()   # fetchall vacío
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.get("/blockchain/verify")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["valid"])

    def test_solo_genesis_valido(self):
        conn = self._blocks(self.GENESIS)
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.get("/blockchain/verify")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["valid"])

    def test_genesis_con_previous_hash_incorrecto(self):
        bad_genesis = {"block_index": 1, "hash": "a" * 64, "previous_hash": "x" * 64}
        conn = self._blocks(bad_genesis)
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.get("/blockchain/verify")
        self.assertFalse(r.json()["valid"])
        self.assertIn("Genesis", r.json()["detail"])

    def test_cadena_valida_de_tres_bloques(self):
        b1 = {"block_index": 1, "hash": "a" * 64, "previous_hash": "0" * 64}
        b2 = {"block_index": 2, "hash": "b" * 64, "previous_hash": "a" * 64}
        b3 = {"block_index": 3, "hash": "c" * 64, "previous_hash": "b" * 64}
        conn = self._blocks(b1, b2, b3)
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.get("/blockchain/verify")
        self.assertTrue(r.json()["valid"])

    def test_bloque_intermedio_roto(self):
        b1 = {"block_index": 1, "hash": "a" * 64, "previous_hash": "0" * 64}
        b2 = {"block_index": 2, "hash": "b" * 64, "previous_hash": "WRONG" + "a" * 59}
        b3 = {"block_index": 3, "hash": "c" * 64, "previous_hash": "b" * 64}
        conn = self._blocks(b1, b2, b3)
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.get("/blockchain/verify")
        self.assertFalse(r.json()["valid"])
        self.assertIn("2", r.json()["detail"])   # menciona el bloque roto

    def test_ultimo_bloque_roto(self):
        b1 = {"block_index": 1, "hash": "a" * 64, "previous_hash": "0" * 64}
        b2 = {"block_index": 2, "hash": "b" * 64, "previous_hash": "a" * 64}
        b3 = {"block_index": 3, "hash": "c" * 64, "previous_hash": "XXXXXXXX" + "b" * 56}
        conn = self._blocks(b1, b2, b3)
        with patch.object(app_module, "get_conn", return_value=conn):
            r = client.get("/blockchain/verify")
        self.assertFalse(r.json()["valid"])


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    unittest.main(verbosity=2)