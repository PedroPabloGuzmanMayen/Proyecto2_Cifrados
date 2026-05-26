// Aqui vamos a agregar la página para realizar chats

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthConext'
import { api } from '../utils/api'

function MessageBubble({ msg, currentUserId, onDecrypt, onVerify }) {
  const isMine = msg.sender_id === currentUserId
  const [decrypted, setDecrypted] = useState(null)
  const [verified, setVerified] = useState(null)
  const [showActions, setShowActions] = useState(false)
  const [pwd, setPwd] = useState('')
  const [asking, setAsking] = useState(false)

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

  return (
    <div className={`bubble-wrapper ${isMine ? 'mine' : 'theirs'}`}>
      {!isMine && <div className="bubble-sender">{msg.sender_name || `Usuario ${msg.sender_id}`}</div>}
      <div className="bubble" onMouseEnter={() => setShowActions(true)} onMouseLeave={() => setShowActions(false)}>
        {decrypted ? (
          <div className="bubble-text decrypted">
            <span className="decrypted-tag">🔓</span>
            {decrypted}
          </div>
        ) : (
          <div className="bubble-text encrypted">
            <span className="lock-icon">🔒</span>
            <span className="cipher-preview">{msg.ciphertext?.slice(0, 20)}…</span>
          </div>
        )}

        {verified !== null && (
          <div className={`sig-badge ${verified ? 'valid' : 'invalid'}`}>
            {verified ? '✓ Firma válida' : '✗ Firma inválida'}
          </div>
        )}

        {showActions && !asking && (
          <div className="bubble-actions">
            <button onClick={() => setAsking('decrypt')}>Descifrar</button>
            <button onClick={() => setAsking('verify')}>Verificar firma</button>
          </div>
        )}

        {asking && (
          <div className="bubble-pwd-form">
            <input type="password" placeholder="Tu contraseña" value={pwd}
              onChange={e => setPwd(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (asking === 'decrypt' ? doDecrypt() : doVerify())} />
            <button onClick={asking === 'decrypt' ? doDecrypt : doVerify}>
              {asking === 'decrypt' ? '🔓' : '✓'}
            </button>
            <button onClick={() => { setAsking(false); setPwd('') }}>✕</button>
          </div>
        )}
      </div>
      <div className="bubble-time">{msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</div>
    </div>
  )
}

export default function ChatPage() {
  const { user, token } = useAuth()
  const [messages, setMessages] = useState([])
  const [recipientId, setRecipientId] = useState('')
  const [text, setText] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [chatMode, setChatMode] = useState('individual') // individual | group
  const [groupId, setGroupId] = useState('')
  const [sendError, setSendError] = useState('')
  const [sendOk, setSendOk] = useState('')
  const bottomRef = useRef()

  const loadMessages = async () => {
    if (!user?.id) return
    try {
      const res = await api.getMessages(user.id, token)
      setMessages(res.messages || [])
    } catch (e) { setError(e.message) }
  }

  useEffect(() => {
    const userId = user?.id
    if (!userId) return

    let cancelled = false
    const fetchMessages = async () => {
      try {
        const res = await api.getMessages(userId, token)
        if (!cancelled) setMessages(res.messages || [])
      } catch (e) {
        if (!cancelled) setError(e.message)
      }
    }

    fetchMessages()
    return () => { cancelled = true }
  }, [user?.id, token])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const sendMessage = async () => {
    if (!text.trim() || !password) { setSendError('Escribe un mensaje y tu password'); return }
    setSendError(''); setSendOk('')
    setLoading(true)
    try {
      if (chatMode === 'individual') {
        if (!recipientId) { setSendError('Ingresa el ID del destinatario'); setLoading(false); return }
        await api.sendMessage({ sender: user.id, recipient: parseInt(recipientId), message: text, sender_password: password }, token)
      } else {
        if (!groupId) { setSendError('Ingresa el ID del grupo'); setLoading(false); return }
        await api.sendGroupMessage({ sender: user.id, recipient: parseInt(groupId), message: text, sender_password: password }, token)
      }
      setSendOk('✓ Mensaje enviado y registrado en blockchain')
      setText('')
      setTimeout(() => setSendOk(''), 3000)
      await loadMessages()
    } catch (e) { setSendError(e.message) }
    setLoading(false)
  }

  const handleDecrypt = async (msgId, pwd) => {
    try {
      const res = await api.decryptMessage(user.id, msgId, pwd, token)
      return res.plaintext
    } catch (e) { setSendError(e.message); return null }
  }

  const handleVerify = async (msgId, pwd) => {
    try {
      return await api.verifySignature(msgId, pwd, token)
    } catch (e) { setSendError(e.message); return null }
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div className="chat-header-info">
          <h2>💬 Mensajes cifrados</h2>
          <span className="chat-subtitle">Todos los mensajes usan AES-256-GCM + RSA-OAEP</span>
        </div>
        <button className="refresh-btn" onClick={loadMessages}>↻ Actualizar</button>
      </div>

      {error && <div className="chat-error">{error}</div>}

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-icon">🔐</div>
            <p>No hay mensajes aún</p>
            <span>Los mensajes que recibas aparecerán aquí cifrados</span>
          </div>
        ) : (
          messages.map(msg => (
            <MessageBubble key={msg.id} msg={msg} currentUserId={user?.id}
              onDecrypt={handleDecrypt} onVerify={handleVerify} />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        {sendError && <div className="send-error">{sendError}</div>}
        {sendOk && <div className="send-ok">{sendOk}</div>}

        <div className="mode-toggle">
          <button className={chatMode === 'individual' ? 'active' : ''} onClick={() => setChatMode('individual')}>
            👤 Individual
          </button>
          <button className={chatMode === 'group' ? 'active' : ''} onClick={() => setChatMode('group')}>
            👥 Grupo
          </button>
        </div>

        <div className="input-row">
          <label className="chat-field recipient-field">
            <span>{chatMode === 'individual' ? 'Destinatario' : 'Grupo'}</span>
            <input
              className="recipient-input"
              type="number"
              placeholder={chatMode === 'individual' ? 'ID destinatario' : 'ID grupo'}
              value={chatMode === 'individual' ? recipientId : groupId}
              onChange={e => chatMode === 'individual' ? setRecipientId(e.target.value) : setGroupId(e.target.value)}
            />
          </label>
          <label className="chat-field password-field">
            <span>Password</span>
            <input
              className="password-input"
              type="password"
              placeholder="Password de tu cuenta"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </label>
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
            {loading ? <span className="spinner" /> : '→'}
          </button>
        </div>
      </div>
    </div>
  )
}
