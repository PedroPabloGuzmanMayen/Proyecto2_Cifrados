"""
Tests unitarios del módulo blockchain.

Cubre:
  1. El bloque génesis tiene previous_hash = "0" * 64 y hash válido.
  2. Encadenamiento correcto: previous_hash del bloque N apunta al hash del bloque N-1.
  3. Cadena válida pasa la verificación completa.
  4. Cadena manipulada es detectada por is_chain_valid().
"""
import sys
import os

sys.path.insert(0, os.path.abspath(".."))
import pytest
from blockchain.block import Block
from blockchain.chain import Blockchain, GENESIS_PREV_HASH
from blockchain.pow import DIFFICULTY


# ─── Test 1: bloque génesis ───────────────────────────────────────────────────
def test_genesis_block():
    bc = Blockchain()
    genesis = bc.create_genesis_block()

    r1 = genesis.index == 0
    r2 = genesis.previous_hash == GENESIS_PREV_HASH
    r3 = genesis.hash == genesis.compute_hash()
    r4 = genesis.hash.startswith("0" * DIFFICULTY) if DIFFICULTY > 0 else True

    print(f"\n  index == 0                : {r1}")
    print(f"  previous_hash == '0'*64   : {r2}")
    print(f"  hash almacenado == hash   : {r3}")
    print(f"  hash cumple proof-of-work : {r4}")

    assert r1 and r2 and r3 and r4


# ─── Test 2: encadenamiento correcto ─────────────────────────────────────────
def test_encadenamiento():
    bc = Blockchain()
    genesis = bc.create_genesis_block()
    block1  = bc.create_next_block(sender_id=1, recipient_id=2, message_hash="a" * 64)

    r1 = block1.previous_hash == genesis.hash
    r2 = block1.index == 1
    r3 = block1.hash == block1.compute_hash()

    print(f"\n  previous_hash apunta al génesis : {r1}")
    print(f"  index == 1                      : {r2}")
    print(f"  hash almacenado == hash         : {r3}")

    assert r1 and r2 and r3


# ─── Test 3: cadena válida ────────────────────────────────────────────────────
def test_cadena_valida():
    bc = Blockchain()
    genesis = bc.create_genesis_block()
    block1  = bc.create_next_block(sender_id=1, recipient_id=2, message_hash="b" * 64)
    block2  = bc.create_next_block(sender_id=2, recipient_id=3, message_hash="c" * 64)

    valid, message = bc.is_chain_valid([genesis, block1, block2])

    print(f"\n  is_chain_valid retorna True : {valid}")
    print(f"  mensaje                     : {message}")

    assert valid is True, f"La cadena debería ser válida: {message}"
    assert "válida" in message.lower()


# ─── Test 4: cadena manipulada es detectada ───────────────────────────────────
def test_cadena_manipulada_detectada():
    bc = Blockchain()
    genesis = bc.create_genesis_block()
    block1  = bc.create_next_block(sender_id=1, recipient_id=2, message_hash="d" * 64)
    block2  = bc.create_next_block(sender_id=2, recipient_id=3, message_hash="e" * 64)

    block1.data["message_hash"] = "manipulado" * 5

    valid, message = bc.is_chain_valid([genesis, block1, block2])

    r1 = valid is False
    r2 = "1" in message

    print(f"\n  manipulación detectada (valid==False) : {r1}")
    print(f"  error menciona bloque 1               : {r2}")
    print(f"  mensaje                               : {message}")

    assert r1 and r2