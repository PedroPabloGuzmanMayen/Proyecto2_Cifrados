//Aqui se va a agregar la página de autenticación

import { useState } from 'react'
import { useAuth } from '../context/AuthConext'
import { api } from '../utils/api'

function decodeToken(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return { id: parseInt(payload.sub), email: payload.email }
  } catch { return null }
}

export default function AuthPage() {
  const { login } = useAuth()
  const [mode, setMode] = useState('login') // login | register | mfa | setupMfa
  const [form, setForm] = useState({ name: '', email: '', contrasenas: '', contrasena: '' })
  const [mfaData, setMfaData] = useState({ userId: null, code: '' })
  const [mfaSetup, setMfaSetup] = useState({ token: '', userId: null, qrCode: '', secret: '', code: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const setAuthMode = (nextMode) => {
    setMode(nextMode)
    setError('')
    setSuccess('')
  }

  const handleLogin = async () => {
    setLoading(true); setError('')
    try {
      const res = await api.login({ email: form.email, contrasena: form.contrasenas })
      if (res.mfa_required) {
        setMfaData(m => ({ ...m, userId: res.user_id }))
        setMode('mfa')
      } else {
        const userData = decodeToken(res.access_token)
        login(res.access_token, userData)
      }
    } catch (e) { setError(e.message) }
    setLoading(false)
  }

  const handleRegister = async () => {
    setLoading(true); setError('')
    try {
      await api.registro({ name: form.name, email: form.email, contrasenas: form.contrasenas })
      setSuccess('¡Cuenta creada! Ahora inicia sesión.')
      setMode('login')
    } catch (e) { setError(e.message) }
    setLoading(false)
  }

  const handleMFA = async () => {
    setLoading(true); setError('')
    try {
      const res = await api.loginMFA({ email: form.email, contrasena: form.contrasenas, totp_code: mfaData.code })
      const userData = decodeToken(res.access_token)
      login(res.access_token, userData)
    } catch (e) { setError(e.message) }
    setLoading(false)
  }

  const handleSetupMFA = async () => {
    setLoading(true); setError(''); setSuccess('')
    try {
      const auth = await api.login({ email: form.email, contrasena: form.contrasenas })
      if (auth.mfa_required) {
        setMfaData(m => ({ ...m, userId: auth.user_id }))
        setMode('mfa')
        setError('Esta cuenta ya tiene MFA activo. Ingresa tu código para entrar.')
        setLoading(false)
        return
      }

      const userData = decodeToken(auth.access_token)
      if (!userData?.id) throw new Error('No se pudo leer el token de sesión')

      const setup = await api.enableMFA(auth.access_token)
      setMfaSetup({
        token: auth.access_token,
        userId: userData.id,
        qrCode: setup.qr_code,
        secret: setup.secret,
        code: '',
      })
      setSuccess('QR generado. Escanéalo y escribe el código de 6 dígitos.')
    } catch (e) { setError(e.message) }
    setLoading(false)
  }

  const handleVerifySetupMFA = async () => {
    setLoading(true); setError('')
    try {
      await api.verifyMFA(mfaSetup.userId, mfaSetup.code, mfaSetup.token)
      const userData = decodeToken(mfaSetup.token)
      login(mfaSetup.token, userData)
    } catch (e) { setError(e.message) }
    setLoading(false)
  }

  const handleSubmit = () => {
    if (mode === 'login') return handleLogin()
    if (mode === 'register') return handleRegister()
    if (mode === 'setupMfa') return mfaSetup.qrCode ? handleVerifySetupMFA() : handleSetupMFA()
    return handleMFA()
  }

  const submitText = () => {
    if (mode === 'login') return 'Entrar'
    if (mode === 'register') return 'Crear cuenta'
    if (mode === 'setupMfa') return mfaSetup.qrCode ? 'Verificar y entrar' : 'Generar QR'
    return 'Entrar con MFA'
  }

  return (
    <div className="auth-root">
      <div className="auth-brand">
        <div className="auth-hex">⬡</div>
        <h1 className="auth-title">VaultChain</h1>
        <p className="auth-subtitle">Mensajería cifrada con blockchain</p>
        <div className="auth-badges">
          <span className="badge">AES-256-GCM</span>
          <span className="badge">RSA-OAEP</span>
          <span className="badge">Blockchain</span>
          <span className="badge">MFA</span>
        </div>
      </div>

      <div className="auth-card">
        <div className="auth-tabs">
          <button className={`auth-tab ${mode === 'login' ? 'active' : ''}`} onClick={() => setAuthMode('login')}>
            Iniciar sesión
          </button>
          <button className={`auth-tab ${mode === 'register' ? 'active' : ''}`} onClick={() => setAuthMode('register')}>
            Registrarse
          </button>
          <button className={`auth-tab ${mode === 'mfa' ? 'active' : ''}`} onClick={() => setAuthMode('mfa')}>
            MFA
          </button>
          <button className={`auth-tab ${mode === 'setupMfa' ? 'active' : ''}`} onClick={() => setAuthMode('setupMfa')}>
            Activar
          </button>
        </div>

        {mode === 'mfa' && (
          <div className="auth-form-title">
            <span className="mfa-icon">🔐</span>
            <h2>Verificación MFA</h2>
            <p>Ingresa el código de tu app autenticadora</p>
          </div>
        )}

        {mode === 'setupMfa' && (
          <div className="auth-form-title">
            <span className="mfa-icon">🔐</span>
            <h2>Activar MFA</h2>
            <p>Genera el QR y verifica tu app autenticadora</p>
          </div>
        )}

        {error && <div className="auth-error">{error}</div>}
        {success && <div className="auth-success">{success}</div>}

        <div className="auth-form">
          {mode === 'register' && (
            <div className="field">
              <label>Nombre completo</label>
              <input type="text" placeholder="Alice López" value={form.name} onChange={e => set('name', e.target.value)} />
            </div>
          )}

          <div className="field">
            <label>Correo electrónico</label>
            <input type="email" placeholder="tu@correo.com" value={form.email} onChange={e => set('email', e.target.value)} />
          </div>
          <div className="field">
            <label>Contraseña</label>
            <input type="password" placeholder="••••••••" value={form.contrasenas} onChange={e => set('contrasenas', e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
          </div>

          {mode === 'setupMfa' && mfaSetup.qrCode && (
            <div className="qr-container">
              <img src={`data:image/png;base64,${mfaSetup.qrCode}`} alt="QR MFA" className="qr-img" />
              <div className="secret-box">Secret: <code>{mfaSetup.secret}</code></div>
            </div>
          )}

          {(mode === 'mfa' || (mode === 'setupMfa' && mfaSetup.qrCode)) && (
            <div className="field">
              <label>Código TOTP (6 dígitos)</label>
              <input type="text" placeholder="123456" maxLength={6} value={mode === 'setupMfa' ? mfaSetup.code : mfaData.code}
                onChange={e => mode === 'setupMfa'
                  ? setMfaSetup(m => ({ ...m, code: e.target.value }))
                  : setMfaData(m => ({ ...m, code: e.target.value }))}
                onKeyDown={e => e.key === 'Enter' && handleSubmit()} className="code-input" />
            </div>
          )}

          <button className="auth-btn" disabled={loading}
            onClick={handleSubmit}>
            {loading ? <span className="spinner" /> : submitText()}
          </button>

          {(mode === 'mfa' || mode === 'setupMfa') && (
            <button className="auth-link" onClick={() => setAuthMode('login')}>Usar login normal</button>
          )}
        </div>
      </div>
    </div>
  )
}
