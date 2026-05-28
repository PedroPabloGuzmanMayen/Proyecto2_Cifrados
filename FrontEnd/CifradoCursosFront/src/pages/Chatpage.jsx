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
              type="password" placeholder="Tu contraseña" value={pwd}
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

function Sidebar({ users, groups, conversationsMap, selectedChat, onSelect, loading }) {
  return (
    <div className="conv-list">
      {loading ? (
        <div className="conv-loading">
          <span className="spinner sm" />
        </div>
      ) : (
        <>
          <div className="conv-section">
            <div className="conv-section-title">Usuarios</div>
            {users.length === 0 ? (
              <div className="conv-empty"><p>No hay usuarios</p></div>
            ) : (
              users.map(u => {
                const conv = conversationsMap[u.id]
                return (
                  <button
                    key={u.id}
                    className={`conv-item ${selectedChat?.type === 'user' && selectedChat.id === u.id ? 'active' : ''}`}
                    onClick={() => onSelect({ type: 'user', id: u.id, name: u.name, email: u.email })}
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

          {groups.length > 0 && (
            <div className="conv-section">
              <div className="conv-section-title">Grupos</div>
              {groups.map(g => (
                <button
                  key={g.id}
                  className={`conv-item ${selectedChat?.type === 'group' && selectedChat.id === g.id ? 'active' : ''}`}
                  onClick={() => onSelect({ type: 'group', id: g.id, name: g.name })}
                >
                  <div className="conv-avatar group-avatar">G</div>
                  <div className="conv-info">
                    <span className="conv-name">{g.name}</span>
                    <span className="conv-email">Grupo #{g.id}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default function ChatPage() {
  const { user, token } = useAuth()
  const [messages, setMessages] = useState([])
  const [allUsers, setAllUsers] = useState([])
  const [groups, setGroups] = useState([])
  const [conversationsMap, setConversationsMap] = useState({})
  const [selectedChat, setSelectedChat] = useState(null)
  const [text, setText] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarLoading, setSidebarLoading] = useState(true)
  const [error, setError] = useState('')
  const [sendError, setSendError] = useState('')
  const [sendOk, setSendOk] = useState('')
  const bottomRef = useRef()

  useEffect(() => {
    if (!user?.id) return
    let cancelled = false

    const load = async () => {
      try {
        setSidebarLoading(true)
        const [usersRes, convsRes, groupsRes] = await Promise.all([
          api.listUsers(token),
          api.getConversations(user.id, token),
          api.getUserGroups(user.id, token),
        ])
        if (cancelled) return
        setAllUsers(usersRes.users || [])
        setGroups(groupsRes.groups || [])
        const map = {}
        for (const c of (convsRes.conversations || [])) {
          map[c.user_id] = c
        }
        setConversationsMap(map)
      } catch (e) {
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setSidebarLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [user?.id, token])

  const loadMessages = async (chat) => {
    if (!user?.id || !chat) return
    try {
      if (chat.type === 'user') {
        const res = await api.getConversation(user.id, chat.id, token)
        setMessages(res.messages || [])
      } else {
        const res = await api.getGroupMessages(chat.id, token)
        setMessages(res.messages || [])
      }
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    if (selectedChat) {
      loadMessages(selectedChat)
    } else {
      setMessages([])
    }
  }, [selectedChat])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const refreshSidebar = async () => {
    if (!user?.id) return
    try {
      const [convsRes, groupsRes] = await Promise.all([
        api.getConversations(user.id, token),
        api.getUserGroups(user.id, token),
      ])
      setGroups(groupsRes.groups || [])
      const map = {}
      for (const c of (convsRes.conversations || [])) {
        map[c.user_id] = c
      }
      setConversationsMap({ ...map })
    } catch (e) {
      setError(e.message)
    }
  }

  const sendMessage = async () => {
    if (!text.trim() || !password || !selectedChat) {
      setSendError('Escribe un mensaje, tu password y selecciona un destinatario')
      return
    }
    setSendError('')
    setSendOk('')
    setLoading(true)
    try {
      if (selectedChat.type === 'user') {
        await api.sendMessage({
          sender: user.id,
          recipient: selectedChat.id,
          message: text,
          sender_password: password,
        }, token)
      } else {
        await api.sendGroupMessage({
          sender: user.id,
          recipient: selectedChat.id,
          message: text,
          sender_password: password,
        }, token)
      }
      setSendOk('\u2713 Mensaje enviado')
      setText('')
      setTimeout(() => setSendOk(''), 2500)
      await loadMessages(selectedChat)
      await refreshSidebar()
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
      await refreshSidebar()
    } catch (e) {
      setError(e.message)
    }
  }

  const chatLabel = selectedChat
    ? selectedChat.type === 'user'
      ? `${selectedChat.name} (${selectedChat.email})`
      : `${selectedChat.name} (Grupo)`
    : 'Ninguno'

  return (
    <div className="chat-page">
      <Sidebar
        users={allUsers}
        groups={groups}
        conversationsMap={conversationsMap}
        selectedChat={selectedChat}
        onSelect={setSelectedChat}
        loading={sidebarLoading}
      />
      <div className="chat-main">
        {selectedChat ? (
          <>
            <div className="chat-header">
              <div className="chat-header-info">
                <h2>{selectedChat.name}</h2>
                <span className="chat-subtitle">
                  {selectedChat.type === 'user' ? selectedChat.email : 'Grupo'}
                </span>
              </div>
              <button className="refresh-btn" onClick={() => loadMessages(selectedChat)}>
                {'\u21bb'} Actualizar
              </button>
            </div>

            {error && <div className="chat-error">{error}</div>}

            <div className="chat-messages">
              {messages.length === 0 ? (
                <div className="empty-chat">
                  <div className="empty-icon">{'\u{1f513}'}</div>
                  <p>No hay mensajes con {selectedChat.name}</p>
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

              <div className="input-row">
                <div className="chat-field recipient-field">
                  <span>Para:</span>
                  <input
                    className="recipient-input"
                    type="text"
                    value={chatLabel}
                    disabled
                  />
                </div>
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
            <p>Selecciona un usuario o grupo</p>
            <span>Elige en la barra lateral con qui&eacute;n chatear</span>
          </div>
        )}
      </div>
    </div>
  )
}
