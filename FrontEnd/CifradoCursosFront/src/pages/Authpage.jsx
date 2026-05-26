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
  const [mode, setMode] = useState('login') // login | register | mfa
  const [form, setForm] = useState({ name: '', email: '', contrasenas: '', contrasena: '' })
  const [mfaData, setMfaData] = useState({ userId: null, code: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

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
        {mode !== 'mfa' && (
          <div className="auth-tabs">
            <button className={`auth-tab ${mode === 'login' ? 'active' : ''}`} onClick={() => { setMode('login'); setError(''); setSuccess('') }}>
              Iniciar sesión
            </button>
            <button className={`auth-tab ${mode === 'register' ? 'active' : ''}`} onClick={() => { setMode('register'); setError(''); setSuccess('') }}>
              Registrarse
            </button>
          </div>
        )}

        {mode === 'mfa' && (
          <div className="auth-form-title">
            <span className="mfa-icon">🔐</span>
            <h2>Verificación MFA</h2>
            <p>Ingresa el código de tu app autenticadora</p>
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

          {mode !== 'mfa' && (
            <>
              <div className="field">
                <label>Correo electrónico</label>
                <input type="email" placeholder="tu@correo.com" value={form.email} onChange={e => set('email', e.target.value)} />
              </div>
              <div className="field">
                <label>Contraseña</label>
                <input type="password" placeholder="••••••••" value={form.contrasenas} onChange={e => set('contrasenas', e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && (mode === 'login' ? handleLogin() : handleRegister())} />
              </div>
            </>
          )}

          {mode === 'mfa' && (
            <div className="field">
              <label>Código TOTP (6 dígitos)</label>
              <input type="text" placeholder="123456" maxLength={6} value={mfaData.code}
                onChange={e => setMfaData(m => ({ ...m, code: e.target.value }))}
                onKeyDown={e => e.key === 'Enter' && handleMFA()} className="code-input" />
            </div>
          )}

          <button className="auth-btn" disabled={loading}
            onClick={mode === 'login' ? handleLogin : mode === 'register' ? handleRegister : handleMFA}>
            {loading ? <span className="spinner" /> : mode === 'login' ? 'Entrar' : mode === 'register' ? 'Crear cuenta' : 'Verificar'}
          </button>

          {mode === 'mfa' && (
            <button className="auth-link" onClick={() => { setMode('login'); setError('') }}>← Volver al login</button>
          )}
        </div>
      </div>
    </div>
  )
}