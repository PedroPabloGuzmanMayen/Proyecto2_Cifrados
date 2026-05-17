import hashlib
import json
from dataclasses import dataclass


@dataclass
class Block:
    index: int
    timestamp: str
    data: dict          # {"sender_id": int, "recipient_id": int, "message_hash": str}
    previous_hash: str
    nonce: int
    hash: str = ""

    def compute_hash(self) -> str:
        """
        4. Encadenamiento correcto de hashes SHA-256
        
        hash_actual = SHA-256(index + timestamp + data + previous_hash + nonce)
        data se serializa como JSON con claves ordenadas para garantizar determinismo.
        """
        raw = (
            str(self.index)
            + self.timestamp
            + json.dumps(self.data, sort_keys=True)
            + self.previous_hash
            + str(self.nonce)
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()