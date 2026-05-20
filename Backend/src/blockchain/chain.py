from datetime import datetime, timezone
from .block import Block
from .pow import mine_block

GENESIS_PREV_HASH = "0" * 64


class Blockchain:

    def __init__(self):
        self.prev_hash = ""
        self.index_counter = 1

    # ─── Genesis ─────────────────────────────────────────────────────────────

    def create_genesis_block(self) -> Block:
        """
        Crea el bloque génesis con previous_hash = "0" * 64.
        Los datos de la transacción son vacíos porque no corresponde
        a ningún mensaje real.
        """
        genesis = Block(
            index=0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={"sender_id": 0, "recipient_id": 0, "message_hash": "genesis"},
            previous_hash=GENESIS_PREV_HASH,
            nonce=0,
        )
        new_block = mine_block(genesis)
        self.index_counter = 1
        self.prev_hash = new_block.hash
        return new_block

    # ─── Nuevo bloque ────────────────────────────────────────────────────────

    def create_next_block(
        self,
        sender_id: int,
        recipient_id: int,
        message_hash: str,
    ) -> Block:
        """
        Construye y mina el siguiente bloque de la cadena.

        Parámetros:
            sender_id     : ID del remitente del mensaje
            recipient_id  : ID del destinatario del mensaje
            message_hash  : SHA-256 del texto plano del mensaje

        Retorna:
            Block minado con hash válido.
        """
        block = Block(
            index=self.index_counter,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "sender_id":    sender_id,
                "recipient_id": recipient_id,
                "message_hash": message_hash,
            },
            previous_hash=self.prev_hash,
            nonce=0,
        )
        new_block = mine_block(block)
        self.prev_hash = new_block.hash
        self.index_counter += 1
        return new_block

    # ─── Validación ──────────────────────────────────────────────────────────

    def is_chain_valid(self, blocks: list[Block]) -> tuple[bool, str]:
        """
        Recorre la cadena completa verificando:
          1. El hash almacenado coincide con el hash recalculado.
          2. El previous_hash de cada bloque apunta al hash del bloque anterior.
          3. El bloque génesis tiene previous_hash = "0" * 64.

        Retorna:
            (True,  "Cadena válida")           si todo está correcto.
            (False, "Descripción del error")   si se detecta inconsistencia.
        """
        if not blocks:
            return False, "La cadena está vacía"

        # Verificar bloque génesis
        genesis = blocks[0]
        if genesis.previous_hash != GENESIS_PREV_HASH:
            return False, f"El bloque génesis tiene previous_hash inválido: {genesis.previous_hash}"

        for i, block in enumerate(blocks):
            # 1 – Integridad: el hash almacenado debe coincidir con el recalculado
            recalculated = block.compute_hash()
            if block.hash != recalculated:
                return False, (
                    f"Bloque {block.index}: hash almacenado no coincide con el recalculado. "
                    f"Almacenado={block.hash[:16]}… Recalculado={recalculated[:16]}…"
                )

            # 2 – Encadenamiento: a partir del bloque 1, previous_hash debe apuntar al anterior
            if i > 0:
                prev_block = blocks[i - 1]
                if block.previous_hash != prev_block.hash:
                    return False, (
                        f"Bloque {block.index}: previous_hash no apunta al hash del bloque {prev_block.index}."
                    )

        return True, "Cadena válida"