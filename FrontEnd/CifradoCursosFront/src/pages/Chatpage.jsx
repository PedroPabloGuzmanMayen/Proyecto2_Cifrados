import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthConext'
import { api } from '../utils/api'

function MessageBubble({ msg, currentUserId, onDecrypt, onVerify, onDelete }) {
  const isMine = msg.sender_id === currentUserId
  const [decrypted, setDecrypted] = useState(null)
  const [verified, setVerified] = useState(null)
  const [showActions, setShowActions] = useState(false)
  const [pwd, setPwd] = useState('')
  const [asking, setAsking] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const doDecrypt = async () => {
    if (!pwd) return
    const result = await onDecrypt(msg.id, pwd)
    if (result) { setDecrypted(result); setAsking(false); setPwd('') }
  }

  const doVerify = async () => {
    if (!pwd) return
    const result = await onVerify(msg.id, pwd)
    if (result) { setVerified(result.verified); setAsking(false); setPwd('') }
  }

  const doDelete = async () => {
    if (deleting) return
    setDeleting(true)
    await onDelete(msg.id)
    setDeleting(false)
  }

  const time = msg.created_at
    ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : ''

  return (
    <div className={`bubble-wrapper ${isMine ? 'mine' : 'theirs'}`}>
      {!isMine && <div className="bubble-sender">{msg.sender_name || `Usuario ${msg.sender_id}`}</div>}
      <div
        className={`bubble ${deleting ? 'deleting' : ''}`}
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
      >
        {decrypted ? (
          <div className="bubble-text decrypted">
            <span className="decrypted-tag">&#x1f513;</span>
            {decrypted}
          </div>
        ) : (
          <div className="bubble-text encrypted">
            <span className="lock-icon">&#x1f512;</span>
            <span className="cipher-preview">{msg.ciphertext?.slice(0, 20)}&hellip;</span>
          </div>
        )}

        {verified !== null && (
          <div className={`sig-badge ${verified ? 'valid' : 'invalid'}`}>
            {verified ? '\u2713 Firma v\u00e1lida' : '\u2717 Firma inv\u00e1lida'}
          </div>
        )}

        {showActions && !asking && (
          <div className="bubble-actions">
            <button onClick={() => setAsking('decrypt')}>Descifrar</button>
            <button onClick={() => setAsking('verify')}>Verificar firma</button>
            {isMine && (
              <button className="delete-btn" onClick={doDelete} disabled={deleting}>
                {deleting ? '...' : 'Eliminar'}
              </button>
            )}
          </div>
        )}

        {asking && (
          <div className="bubble-pwd-form">
            <input
              type="password" placeholder="Tu contrase\u00f1a" value={pwd}
              onChange={e => setPwd(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (asking === 'decrypt' ? doDecrypt() : doVerify())}
            />
            <button onClick={asking === 'decrypt' ? doDecrypt : doVerify}>
              {asking === 'decrypt' ? '\u{1f513}' : '\u2713'}
            </button>
            <button onClick={() => { setAsking(false); setPwd('') }}>{'\u2715'}</button>
          </div>
        )}
      </div>
      <div className="bubble-time">{time}</div>
    </div>
  )
}

function UserList({ users, conversationsMap, selectedId, onSelect, loading }) {
  return (
    <div className="conv-list">
      <div className="conv-list-header">
        <h3>Usuarios</h3>
      </div>
      <div className="conv-items">
        {loading ? (
          <div className="conv-loading">
            <span className="spinner sm" />
          </div>
        ) : users.length === 0 ? (
          <div className="conv-empty">
            <p>No hay usuarios</p>
          </div>
        ) : (
          users.map(u => {
            const conv = conversationsMap[u.id]
            return (
              <button
                key={u.id}
                className={`conv-item ${selectedId === u.id ? 'active' : ''}`}
                onClick={() => onSelect(u)}
              >
                <div className="conv-avatar">{u.name?.[0]?.toUpperCase() || '?'}</div>
                <div className="conv-info">
                  <span className="conv-name">{u.name}</span>
                  <span className="conv-email">{u.email}</span>
                  {conv && (
                    <span className="conv-preview">{conv.last_ciphertext?.slice(0, 30)}...</span>
                  )}
                </div>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { user, token } = useAuth()
  const [messages, setMessages] = useState([])
  const [allUsers, setAllUsers] = useState([])
  const [conversationsMap, setConversationsMap] = useState({})
  const [selectedUser, setSelectedUser] = useState(null)
  const [text, setText] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [usersLoading, setUsersLoading] = useState(true)
  const [error, setError] = useState('')
  const [sendError, setSendError] = useState('')
  const [sendOk, setSendOk] = useState('')
  const [chatMode, setChatMode] = useState('individual')
  const [groupId, setGroupId] = useState('')
  const bottomRef = useRef()

  useEffect(() => {
    if (!user?.id) return
    let cancelled = false

    const load = async () => {
      try {
        setUsersLoading(true)
        const [usersRes, convsRes] = await Promise.all([
          api.listUsers(token),
          api.getConversations(user.id, token),
        ])
        if (cancelled) return
        setAllUsers(usersRes.users || [])
        const map = {}
        for (const c of (convsRes.conversations || [])) {
          map[c.user_id] = c
        }
        setConversationsMap(map)
      } catch (e) {
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setUsersLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [user?.id, token])

  const loadMessages = async (otherUserId) => {
    if (!user?.id || !otherUserId) return
    try {
      const res = await api.getConversation(user.id, otherUserId, token)
      setMessages(res.messages || [])
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    if (selectedUser) {
      loadMessages(selectedUser.id)
    } else {
      setMessages([])
    }
  }, [selectedUser])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSelectUser = (u) => {
    setSelectedUser(u)
  }

  const sendMessage = async () => {
    if (chatMode === 'individual') {
      if (!text.trim() || !password || !selectedUser) {
        setSendError('Escribe un mensaje, tu password y selecciona un destinatario')
        return
      }
    } else {
      if (!text.trim() || !password || !groupId) {
        setSendError('Escribe un mensaje, tu password y el ID del grupo')
        return
      }
    }
    setSendError('')
    setSendOk('')
    setLoading(true)
    try {
      if (chatMode === 'individual') {
        await api.sendMessage({
          sender: user.id,
          recipient: selectedUser.id,
          message: text,
          sender_password: password,
        }, token)
      } else {
        await api.sendGroupMessage({
          sender: user.id,
          recipient: parseInt(groupId),
          message: text,
          sender_password: password,
        }, token)
      }
      setSendOk('\u2713 Mensaje enviado')
      setText('')
      setTimeout(() => setSendOk(''), 2500)
      await loadMessages(selectedUser.id)
      const convsRes = await api.getConversations(user.id, token)
      const map = {}
      for (const c of (convsRes.conversations || [])) {
        map[c.user_id] = c
      }
      setConversationsMap({ ...map })
    } catch (e) {
      setSendError(e.message)
    }
    setLoading(false)
  }

  const handleDecrypt = async (msgId, pwd) => {
    try {
      const res = await api.decryptMessage(user.id, msgId, pwd, token)
      return res.plaintext
    } catch (e) {
      setSendError(e.message)
      return null
    }
  }

  const handleVerify = async (msgId, pwd) => {
    try {
      return await api.verifySignature(msgId, pwd, token)
    } catch (e) {
      setSendError(e.message)
      return null
    }
  }

  const handleDelete = async (msgId) => {
    try {
      await api.deleteMessage(msgId, token)
      setMessages(prev => prev.filter(m => m.id !== msgId))
      const convsRes = await api.getConversations(user.id, token)
      const map = {}
      for (const c of (convsRes.conversations || [])) {
        map[c.user_id] = c
      }
      setConversationsMap({ ...map })
    } catch (e) {
      setError(e.message)
    }
  }

  const recipientLabel = selectedUser
    ? `${selectedUser.name} (${selectedUser.email})`
    : 'Ninguno'

  return (
    <div className="chat-page">
      <UserList
        users={allUsers}
        conversationsMap={conversationsMap}
        selectedId={selectedUser?.id}
        onSelect={handleSelectUser}
        loading={usersLoading}
      />
      <div className="chat-main">
        {selectedUser ? (
          <>
            <div className="chat-header">
              <div className="chat-header-info">
                <h2>{selectedUser.name}</h2>
                <span className="chat-subtitle">{selectedUser.email}</span>
              </div>
              <button className="refresh-btn" onClick={() => loadMessages(selectedUser.id)}>
                {'\u21bb'} Actualizar
              </button>
            </div>

            {error && <div className="chat-error">{error}</div>}

            <div className="chat-messages">
              {messages.length === 0 ? (
                <div className="empty-chat">
                  <div className="empty-icon">{'\u{1f513}'}</div>
                  <p>No hay mensajes con {selectedUser.name}</p>
                  <span>Env&iacute;a el primer mensaje cifrado</span>
                </div>
              ) : (
                messages.map(msg => (
                  <MessageBubble
                    key={msg.id}
                    msg={msg}
                    currentUserId={user?.id}
                    onDecrypt={handleDecrypt}
                    onVerify={handleVerify}
                    onDelete={handleDelete}
                  />
                ))
              )}
              <div ref={bottomRef} />
            </div>

            <div className="chat-input-area">
              {sendError && <div className="send-error">{sendError}</div>}
              {sendOk && <div className="send-ok">{sendOk}</div>}

              <div className="mode-toggle">
                <button
                  className={chatMode === 'individual' ? 'active' : ''}
                  onClick={() => setChatMode('individual')}
                >
                  {'\u{1f464}'} Individual
                </button>
                <button
                  className={chatMode === 'group' ? 'active' : ''}
                  onClick={() => setChatMode('group')}
                >
                  {'\u{1f465}'} Grupo
                </button>
              </div>

              <div className="input-row">
                {chatMode === 'individual' ? (
                  <div className="chat-field recipient-field">
                    <span>Para:</span>
                    <input
                      className="recipient-input"
                      type="text"
                      value={recipientLabel}
                      disabled
                    />
                  </div>
                ) : (
                  <div className="chat-field recipient-field">
                    <span>Grupo ID</span>
                    <input
                      className="recipient-input"
                      type="number"
                      placeholder="ID grupo"
                      value={groupId}
                      onChange={e => setGroupId(e.target.value)}
                    />
                  </div>
                )}
                <div className="chat-field password-field">
                  <span>Password</span>
                  <input
                    className="password-input"
                    type="password"
                    placeholder="Tu contrase&ntilde;a"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                  />
                </div>
              </div>
              <div className="message-row">
                <input
                  className="message-input"
                  type="text"
                  placeholder="Escribe tu mensaje..."
                  value={text}
                  onChange={e => setText(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                />
                <button className="send-btn" onClick={sendMessage} disabled={loading}>
                  {loading ? <span className="spinner" /> : '\u2192'}
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="chat-no-selection">
            <div className="no-sel-icon">{'\u{1f4ec}'}</div>
            <p>Selecciona un usuario</p>
            <span>Elige a qui&eacute;n escribirle en la barra lateral</span>
          </div>
        )}
      </div>
    </div>
  )
}
