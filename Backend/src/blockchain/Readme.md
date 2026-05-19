# VaultChain – Mini Blockchain

Módulo de auditoría basado en blockchain que registra cada mensaje enviado como una transacción inmutable.

---

## ¿Qué hace?

Cada vez que un usuario envía un mensaje, el sistema genera automáticamente un bloque que contiene:

- Quién envió el mensaje (`sender_id`)
- Quién lo recibió (`recipient_id`)
- Una huella digital del mensaje (`message_hash`)
- El hash del bloque anterior (encadenamiento)
- Un `nonce` calculado por proof-of-work
- El hash del bloque actual

Esto crea un **registro de auditoría a prueba de manipulación**: si alguien altera un bloque, toda la cadena que viene después queda inválida.

---

## Estructura de archivos

```
blockchain/
├── __init__.py   → API pública del módulo
├── block.py      → Dataclass Block + compute_hash()
├── chain.py      → Blockchain: génesis, encadenamiento, validación
└── pow.py        → Proof-of-work (mine_block)
```

---

## Estructura de un bloque

```json
{
  "index":         1,
  "timestamp":     "2026-05-19T10:00:00+00:00",
  "data": {
    "sender_id":    3,
    "recipient_id": 7,
    "message_hash": "a3f9c2..."
  },
  "previous_hash": "00d4e1f...",
  "nonce":         142,
  "hash":          "003af7b..."
}
```

### ¿Por qué `message_hash` y no el mensaje?

El blockchain **nunca almacena el contenido del mensaje**, solo su huella SHA-256.  
Esto preserva la confidencialidad: nadie puede leer el mensaje desde el blockchain,  
pero sí puede verificar que no fue alterado.

---

## Cómo se calcula el hash

```
hash = SHA-256(index + timestamp + data + previous_hash + nonce)
```

`data` se serializa como JSON con claves ordenadas (`sort_keys=True`) para garantizar  
que el mismo contenido siempre produzca el mismo hash.

---

## Bloque Génesis

El primer bloque de la cadena se crea automáticamente con:

```python
previous_hash = "0" * 64
data = {"sender_id": 0, "recipient_id": 0, "message_hash": "genesis"}
```

---

## Proof-of-Work

Antes de agregar un bloque a la cadena, se ejecuta un proceso de minado:  
el `nonce` se incrementa hasta que el hash del bloque empiece con `DIFFICULTY` ceros.

```
DIFFICULTY = 2  →  el hash debe empezar con "00..."
```

Aumentar `DIFFICULTY` hace el minado más lento pero más seguro.  
Está definido en `pow.py` y se puede ajustar fácilmente.

---

## Flujo completo de un mensaje

```
1. Usuario envía mensaje (POST /individual_message/)
        ↓
2. Se firma el mensaje con la llave privada del remitente
        ↓
3. Se cifra el mensaje con la llave pública del destinatario
        ↓
4. Se calcula SHA-256 del texto plano  ← este es el message_hash
        ↓
5. Se guarda el mensaje cifrado en la tabla messages
        ↓
6. Se mina un nuevo bloque con (sender_id, recipient_id, message_hash)
        ↓
7. El bloque queda registrado en la tabla blockchain
```

---

## Verificación de la cadena

El endpoint `GET /blockchain/verify` recorre todos los bloques y comprueba:

1. El hash almacenado coincide con el hash recalculado
2. El `previous_hash` de cada bloque apunta al hash del bloque anterior
3. El bloque génesis tiene `previous_hash = "0" * 64`

Si cualquier bloque fue alterado, la verificación falla e indica exactamente cuál.

---

## Verificación de un mensaje

Para comprobar que un mensaje no fue alterado:

```
1. Descifrar el mensaje con la llave privada del destinatario
2. Calcular SHA-256 del texto descifrado
3. Comparar con el message_hash guardado en el bloque correspondiente
```

Si coinciden → el mensaje es auténtico e íntegro.

---

## Tabla en base de datos

```sql
CREATE TABLE IF NOT EXISTS blockchain (
    id            SERIAL PRIMARY KEY,
    index         INT          NOT NULL UNIQUE,
    timestamp     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    sender_id     INT          NOT NULL REFERENCES users(id),
    recipient_id  INT          NOT NULL REFERENCES users(id),
    message_hash  TEXT         NOT NULL,
    previous_hash CHAR(64)     NOT NULL,
    nonce         INT          NOT NULL,
    hash          CHAR(64)     NOT NULL UNIQUE
);
```

---

## Dependencias

No requiere librerías externas. Usa únicamente:

- `hashlib` – SHA-256 (stdlib de Python)
- `json` – serialización determinista (stdlib de Python)
- `dataclasses` – definición del bloque (stdlib de Python)