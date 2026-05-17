from .block import Block

DIFFICULTY = 2          # el hash debe empezar con DIFFICULTY ceros: "00..."
PREFIX = "0" * DIFFICULTY


def mine_block(block: Block) -> Block:
    """
    Incrementa el nonce hasta que el hash del bloque
    empiece con DIFFICULTY ceros (proof-of-work simplificado).
    Retorna el bloque con nonce y hash finales asignados.
    """
    block.nonce = 0
    candidate = block.compute_hash()

    while not candidate.startswith(PREFIX):
        block.nonce += 1
        candidate = block.compute_hash()

    block.hash = candidate
    return block