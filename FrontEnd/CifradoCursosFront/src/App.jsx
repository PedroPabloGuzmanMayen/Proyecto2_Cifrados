import { useState, useEffect } from 'react'
import AuthPage from './pages/Authpage'
import ChatPage from './pages/Chatpage'
import DashboardPage from './pages/Dashboardpage'
import { AuthContext } from './context/AuthConext'
import './App.css'

export default function App() {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [activeView, setActiveView] = useState('chat')

  useEffect(() => {
    const savedToken = localStorage.getItem('vc_token')
    const savedUser = localStorage.getItem('vc_user')
    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))
    }
  }, [])

  const login = (tokenVal, userData) => {
    setToken(tokenVal)
    setUser(userData)
    localStorage.setItem('vc_token', tokenVal)
    localStorage.setItem('vc_user', JSON.stringify(userData))
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('vc_token')
    localStorage.removeItem('vc_user')
  }

  if (!token) return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      <AuthPage />
    </AuthContext.Provider>
  )

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      <div className="app-shell">
        <nav className="sidebar">
          <div className="sidebar-logo">
            <span className="logo-icon">⬡</span>
            <span className="logo-text">VaultChain</span>
          </div>
          <div className="sidebar-nav">
            <button
              className={`nav-item ${activeView === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveView('chat')}
            >
              <span className="nav-icon">◈</span>
              <span>Mensajes</span>
            </button>
            <button
              className={`nav-item ${activeView === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveView('dashboard')}
            >
              <span className="nav-icon">◎</span>
              <span>API Explorer</span>
            </button>
          </div>
          <div className="sidebar-user">
            <div className="user-avatar">{user?.email?.[0]?.toUpperCase() || 'U'}</div>
            <div className="user-info">
              <span className="user-email">{user?.email || 'Usuario'}</span>
              <span className="user-id">ID: {user?.id}</span>
            </div>
            <button className="logout-btn" onClick={logout} title="Cerrar sesión">⏻</button>
          </div>
        </nav>
        <main className="main-content">
          {activeView === 'chat' && <ChatPage />}
          {activeView === 'dashboard' && <DashboardPage />}
        </main>
      </div>
    </AuthContext.Provider>
  )
}