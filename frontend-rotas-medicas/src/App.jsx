import { useState, useEffect, useRef, useCallback } from 'react'
import Sidebar from './components/Sidebar.jsx'
import RouteForm from './components/RouteForm.jsx'
import MapView from './components/MapView.jsx'
import MedicalIllustration from './components/MedicalIllustration.jsx'
import AnalysisPanel from './components/AnalysisPanel.jsx'
import LoginForm from './components/LoginForm.jsx'

const AUTH_STORAGE_KEY = 'rota_medica_auth'

function extractErrorMessage(data) {
  if (data?.erro) return data.erro
  if (Array.isArray(data?.detail)) return data.detail.map(e => e.msg).join('; ')
  if (typeof data?.detail === 'string') return data.detail
  return 'Erro ao calcular rota. Verifique os parâmetros e tente novamente.'
}

function lerAuthArmazenada() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const auth = JSON.parse(raw)
    if (!auth?.token || !auth?.usuario || !auth?.expiresAt || auth.expiresAt <= Date.now()) {
      localStorage.removeItem(AUTH_STORAGE_KEY)
      return null
    }
    return auth
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
}

export default function App() {
  const [auth, setAuth] = useState(lerAuthArmazenada)
  const [loginLoading, setLoginLoading] = useState(false)
  const [loginError, setLoginError] = useState(null)
  const [sessaoExpirou, setSessaoExpirou] = useState(false)
  const logoutTimerRef = useRef(null)

  const [geoJson, setGeoJson] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [formKey, setFormKey] = useState(0)

  const efetuarLogout = useCallback((porExpiracao) => {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    if (logoutTimerRef.current) {
      clearTimeout(logoutTimerRef.current)
      logoutTimerRef.current = null
    }
    setAuth(null)
    setGeoJson(null)
    setError(null)
    setFormKey(k => k + 1)
    setSessaoExpirou(Boolean(porExpiracao))
  }, [])

  // Agenda o logout automático no exato instante em que o token expira,
  // mesmo que o usuário não faça nenhuma outra ação enquanto olha o formulário.
  useEffect(() => {
    if (!auth) return undefined

    const restanteMs = auth.expiresAt - Date.now()
    if (restanteMs <= 0) {
      efetuarLogout(true)
      return undefined
    }

    logoutTimerRef.current = setTimeout(() => efetuarLogout(true), restanteMs)
    return () => clearTimeout(logoutTimerRef.current)
  }, [auth, efetuarLogout])

  const handleLogin = async ({ usuario, senha }) => {
    setLoginLoading(true)
    setLoginError(null)
    try {
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usuario, senha }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.detail || 'Usuário ou senha inválidos.')

      const novaAuth = {
        token: data.token,
        usuario,
        expiresAt: Date.now() + data.expires_in * 1000,
      }
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(novaAuth))
      setAuth(novaAuth)
      setSessaoExpirou(false)
    } catch (err) {
      setLoginError(err.message)
    } finally {
      setLoginLoading(false)
    }
  }

  const handleLogout = () => {
    if (auth?.token) {
      // Melhor esforço — revoga no backend, mas não bloqueia o logout local se falhar.
      fetch('/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.token}` },
      }).catch(() => {})
    }
    efetuarLogout(false)
  }

  const handleSubmit = async (formData) => {
    if (!auth?.token) {
      efetuarLogout(true)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/rotas/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${auth.token}`,
        },
        body: JSON.stringify(formData),
      })
      if (res.status === 401) {
        efetuarLogout(true)
        return
      }
      const data = await res.json()
      if (!res.ok) throw new Error(extractErrorMessage(data))
      setGeoJson(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setGeoJson(null)
    setError(null)
  }

  const handleNovaRota = () => {
    setGeoJson(null)
    setError(null)
    // Força o RouteForm a remontar do zero, resetando também seu estado interno
    // (campos digitados, erro de validação da mensagem etc.) — o Sidebar não tem
    // acesso direto a esse estado, então a troca de key é o jeito mais simples
    // de replicar o mesmo efeito do botão "Limpar" a partir daqui.
    setFormKey(k => k + 1)
  }

  if (!auth) {
    return (
      <LoginForm
        onLogin={handleLogin}
        loading={loginLoading}
        error={loginError}
        avisoSessaoExpirada={sessaoExpirou}
      />
    )
  }

  return (
    <div
      className="flex flex-col h-screen overflow-hidden bg-slate-100"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      {/* Top navigation bar */}
      <Sidebar
        usuario={auth.usuario}
        onNovaRota={handleNovaRota}
        onLogout={handleLogout}
        loading={loading}
      />

      {/* Main content row */}
      <div className="flex flex-1 overflow-hidden">

        {/* Form panel — fixed width, scrollable */}
        <div className="flex-shrink-0 overflow-y-auto border-r border-slate-200 bg-white shadow-sm" style={{ width: 460 }}>
          <RouteForm
            key={formKey}
            onSubmit={handleSubmit}
            onClear={handleClear}
            loading={loading}
            error={error}
          />
        </div>

        {/* Map / Illustration panel — takes all remaining space */}
        <div className="flex-1 relative overflow-hidden">
          {loading && (
            <div className="absolute inset-0 bg-blue-50/90 backdrop-blur-sm flex flex-col items-center justify-center z-20">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-blue-700 font-semibold text-sm">Calculando rota otimizada...</p>
              <p className="text-blue-400 text-xs mt-1">O algoritmo genético está em execução</p>
            </div>
          )}
          {geoJson ? <MapView geoJson={geoJson} /> : <MedicalIllustration />}
        </div>

        {/* Results panel — visible only when route is calculated */}
        {geoJson && <AnalysisPanel geoJson={geoJson} />}
      </div>
    </div>
  )
}
