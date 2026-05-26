//Aqui vamos a agregar todos los endpoints para ver si funciona o no. 

import { useState } from 'react'
import { useAuth } from '../context/AuthConext'
import { api } from '../utils/api'

function Panel({ title, icon, children }) {
  const [open, setOpen] = useState(false)
  return (
    <div className={`panel ${open ? 'open' : ''}`}>
      <button className="panel-header" onClick={() => setOpen(o => !o)}>
        <span className="panel-icon">{icon}</span>
        <span className="panel-title">{title}</span>
        <span className="panel-chevron">{open ? '▲' : '▼'}</span>
      </button>
      {open && <div className="panel-body">{children}</div>}
    </div>
  )
}

function ResultBox({ result, error }) {
  if (!result && !error) return null
  return (
    <div className={`result-box ${error ? 'error' : 'ok'}`}>
      <div className="result-label">{error ? '✗ Error' : '✓ Respuesta'}</div>
      <pre>{JSON.stringify(error ? { error: error } : result, null, 2)}</pre>
    </div>
  )
}

function Field({ label, type = 'text', value, onChange, placeholder }) {
  return (
    <div className="dash-field">
      <label>{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder || label} />
    </div>
  )
}

export default function DashboardPage() {
  const { user, token } = useAuth()

  // Estado general
  const [loading, setLoading] = useState({})
  const [results, setResults] = useState({})
  const [errors, setErrors] = useState({})

  const run = async (key, fn) => {
    setLoading(l => ({ ...l, [key]: true }))
    setErrors(e => ({ ...e, [key]: null }))
    try {
      const res = await fn()
      setResults(r => ({ ...r, [key]: res }))
    } catch (e) {
      setErrors(er => ({ ...er, [key]: e.message }))
    }
    setLoading(l => ({ ...l, [key]: false }))
  }

  // Campos por endpoint
  const [regName, setRegName] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regPass, setRegPass] = useState('')

  const [loginEmail, setLoginEmail] = useState('')
  const [loginPass, setLoginPass] = useState('')

  const [keyUserId, setKeyUserId] = useState('')

  const [getMsgUserId, setGetMsgUserId] = useState(user?.id || '')

  const [sendSender, setSendSender] = useState(user?.id || '')
  const [sendRecipient, setSendRecipient] = useState('')
  const [sendMsg, setSendMsg] = useState('')
  const [sendPwd, setSendPwd] = useState('')

  const [decUserId, setDecUserId] = useState(user?.id || '')
  const [decMsgId, setDecMsgId] = useState('')
  const [decPwd, setDecPwd] = useState('')

  const [verMsgId, setVerMsgId] = useState('')
  const [verPwd, setVerPwd] = useState('')

  const [grpSender, setGrpSender] = useState(user?.id || '')
  const [grpId, setGrpId] = useState('')
  const [grpMsg, setGrpMsg] = useState('')
  const [grpPwd, setGrpPwd] = useState('')

  const [newGrpName, setNewGrpName] = useState('')
  const [newGrpMembers, setNewGrpMembers] = useState('')

  const [addGrpId, setAddGrpId] = useState('')
  const [addUserId, setAddUserId] = useState('')

  const [mfaTotp, setMfaTotp] = useState('')
  const [mfaUserId, setMfaUserId] = useState(user?.id || '')

  const btn = (key, label) => (
    <button className="dash-btn" disabled={loading[key]} onClick={() => {}}>
      {loading[key] ? <span className="spinner sm" /> : label}
    </button>
  )

  return (
    <div className="dashboard-page">
      <div className="dash-header">
        <h2>⚙ API Explorer</h2>
        <p>Prueba todos los endpoints de VaultChain desde aquí</p>
        <div className="dash-user-info">
          <span>Tu ID: <strong>{user?.id}</strong></span>
          <span>Email: <strong>{user?.email}</strong></span>
        </div>
      </div>

      <div className="panels">

        {/* AUTH */}
        <Panel title="Registro de usuario  POST /registro" icon="👤">
          <Field label="Nombre" value={regName} onChange={setRegName} placeholder="Alice López" />
          <Field label="Email" type="email" value={regEmail} onChange={setRegEmail} placeholder="alice@ejemplo.com" />
          <Field label="Contraseña" type="password" value={regPass} onChange={setRegPass} placeholder="••••••••" />
          <button className="dash-btn" disabled={loading.registro}
            onClick={() => run('registro', () => api.registro({ name: regName, email: regEmail, contrasenas: regPass }))}>
            {loading.registro ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.registro} error={errors.registro} />
        </Panel>

        <Panel title="Login  POST /login" icon="🔑">
          <Field label="Email" type="email" value={loginEmail} onChange={setLoginEmail} />
          <Field label="Contraseña" type="password" value={loginPass} onChange={setLoginPass} />
          <button className="dash-btn" disabled={loading.login}
            onClick={() => run('login', () => api.login({ email: loginEmail, contrasena: loginPass }))}>
            {loading.login ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.login} error={errors.login} />
        </Panel>

        <Panel title="Llave pública  GET /users/:id/key" icon="🗝">
          <Field label="User ID" type="number" value={keyUserId} onChange={setKeyUserId} placeholder="1" />
          <button className="dash-btn" disabled={loading.getKey}
            onClick={() => run('getKey', () => api.getUserKey(keyUserId))}>
            {loading.getKey ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.getKey} error={errors.getKey} />
        </Panel>

        {/* MENSAJES */}
        <Panel title="Ver mensajes  GET /messages/:userId" icon="📨">
          <Field label="User ID" type="number" value={getMsgUserId} onChange={setGetMsgUserId} />
          <button className="dash-btn" disabled={loading.getMsg}
            onClick={() => run('getMsg', () => api.getMessages(getMsgUserId))}>
            {loading.getMsg ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.getMsg} error={errors.getMsg} />
        </Panel>

        <Panel title="Enviar mensaje individual  POST /individual_message" icon="📤">
          <Field label="Sender ID" type="number" value={sendSender} onChange={setSendSender} />
          <Field label="Recipient ID" type="number" value={sendRecipient} onChange={setSendRecipient} />
          <Field label="Mensaje" value={sendMsg} onChange={setSendMsg} placeholder="Hola, mensaje secreto" />
          <Field label="Contraseña del sender" type="password" value={sendPwd} onChange={setSendPwd} />
          <button className="dash-btn" disabled={loading.sendMsg}
            onClick={() => run('sendMsg', () => api.sendMessage({
              sender: parseInt(sendSender), recipient: parseInt(sendRecipient), message: sendMsg, sender_password: sendPwd
            }))}>
            {loading.sendMsg ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.sendMsg} error={errors.sendMsg} />
        </Panel>

        <Panel title="Descifrar mensaje  POST /messages/:userId/decrypt/:msgId" icon="🔓">
          <Field label="User ID (receptor)" type="number" value={decUserId} onChange={setDecUserId} />
          <Field label="Message ID" type="number" value={decMsgId} onChange={setDecMsgId} />
          <Field label="Contraseña" type="password" value={decPwd} onChange={setDecPwd} />
          <button className="dash-btn" disabled={loading.decrypt}
            onClick={() => run('decrypt', () => api.decryptMessage(decUserId, decMsgId, decPwd))}>
            {loading.decrypt ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.decrypt} error={errors.decrypt} />
        </Panel>

        <Panel title="Verificar firma  POST /messages/:msgId/verify" icon="✍">
          <Field label="Message ID" type="number" value={verMsgId} onChange={setVerMsgId} />
          <Field label="Contraseña (receptor)" type="password" value={verPwd} onChange={setVerPwd} />
          <button className="dash-btn" disabled={loading.verify}
            onClick={() => run('verify', () => api.verifySignature(verMsgId, verPwd))}>
            {loading.verify ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.verify} error={errors.verify} />
        </Panel>

        {/* GRUPOS */}
        <Panel title="Enviar mensaje a grupo  POST /group_message" icon="👥">
          <Field label="Sender ID" type="number" value={grpSender} onChange={setGrpSender} />
          <Field label="Group ID" type="number" value={grpId} onChange={setGrpId} />
          <Field label="Mensaje" value={grpMsg} onChange={setGrpMsg} />
          <Field label="Contraseña del sender" type="password" value={grpPwd} onChange={setGrpPwd} />
          <button className="dash-btn" disabled={loading.grpMsg}
            onClick={() => run('grpMsg', () => api.sendGroupMessage({
              sender: parseInt(grpSender), recipient: parseInt(grpId), message: grpMsg, sender_password: grpPwd
            }))}>
            {loading.grpMsg ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.grpMsg} error={errors.grpMsg} />
        </Panel>

        <Panel title="Crear grupo  POST /groups" icon="🗂">
          <Field label="Nombre del grupo" value={newGrpName} onChange={setNewGrpName} placeholder="Equipo Alpha" />
          <Field label="IDs de miembros (separados por coma)" value={newGrpMembers} onChange={setNewGrpMembers} placeholder="1,2,3" />
          <button className="dash-btn" disabled={loading.createGrp}
            onClick={() => run('createGrp', () => api.createGroup({
              name: newGrpName, miembros: newGrpMembers.split(',').map(s => parseInt(s.trim())).filter(Boolean)
            }))}>
            {loading.createGrp ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.createGrp} error={errors.createGrp} />
        </Panel>

        <Panel title="Agregar miembro  POST /groups/:id/members" icon="➕">
          <Field label="Group ID" type="number" value={addGrpId} onChange={setAddGrpId} />
          <Field label="User ID a agregar" type="number" value={addUserId} onChange={setAddUserId} />
          <button className="dash-btn" disabled={loading.addMember}
            onClick={() => run('addMember', () => api.addMember(addGrpId, parseInt(addUserId)))}>
            {loading.addMember ? <span className="spinner sm" /> : '▶ Ejecutar'}
          </button>
          <ResultBox result={results.addMember} error={errors.addMember} />
        </Panel>

        {/* BLOCKCHAIN */}
        <Panel title="Verificar blockchain  GET /blockchain/verify" icon="⛓">
          <p className="panel-desc">Verifica la integridad completa de la cadena de bloques</p>
          <button className="dash-btn" disabled={loading.blockchain}
            onClick={() => run('blockchain', () => api.verifyBlockchain())}>
            {loading.blockchain ? <span className="spinner sm" /> : '▶ Ejecutar verificación'}
          </button>
          <ResultBox result={results.blockchain} error={errors.blockchain} />
        </Panel>

        {/* MFA */}
        <Panel title="Activar MFA  POST /auth/mfa/enable" icon="🛡">
          <p className="panel-desc">Activa autenticación de dos factores para tu cuenta. Necesitas estar autenticado.</p>
          <button className="dash-btn" disabled={loading.enableMFA}
            onClick={() => run('enableMFA', () => api.enableMFA(token))}>
            {loading.enableMFA ? <span className="spinner sm" /> : '▶ Activar MFA'}
          </button>
          {results.enableMFA?.qr_code && (
            <div className="qr-container">
              <p>Escanea con Google Authenticator o similar:</p>
              <img src={`data:image/png;base64,${results.enableMFA.qr_code}`} alt="QR MFA" className="qr-img" />
              <div className="secret-box">Secret: <code>{results.enableMFA.secret}</code></div>
            </div>
          )}
          {errors.enableMFA && <ResultBox error={errors.enableMFA} />}
        </Panel>

        <Panel title="Verificar código TOTP  POST /auth/mfa/verify" icon="🔢">
          <Field label="User ID" type="number" value={mfaUserId} onChange={setMfaUserId} />
          <Field label="Código TOTP (6 dígitos)" value={mfaTotp} onChange={setMfaTotp} placeholder="123456" />
          <button className="dash-btn" disabled={loading.verifyMFA}
            onClick={() => run('verifyMFA', () => api.verifyMFA(mfaUserId, mfaTotp))}>
            {loading.verifyMFA ? <span className="spinner sm" /> : '▶ Verificar código'}
          </button>
          <ResultBox result={results.verifyMFA} error={errors.verifyMFA} />
        </Panel>

      </div>
    </div>
  )
}