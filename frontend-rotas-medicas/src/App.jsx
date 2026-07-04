import { useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import RouteForm from './components/RouteForm.jsx'
import MapView from './components/MapView.jsx'
import MedicalIllustration from './components/MedicalIllustration.jsx'
import AnalysisPanel from './components/AnalysisPanel.jsx'

function extractErrorMessage(data) {
  if (data?.erro) return data.erro
  if (Array.isArray(data?.detail)) return data.detail.map(e => e.msg).join('; ')
  if (typeof data?.detail === 'string') return data.detail
  return 'Erro ao calcular rota. Verifique os parâmetros e tente novamente.'
}

export default function App() {
  const [geoJson, setGeoJson] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [formKey, setFormKey] = useState(0)

  const handleSubmit = async (formData) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/rotas/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })
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

  return (
    <div
      className="flex flex-col h-screen overflow-hidden bg-slate-100"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      {/* Top navigation bar */}
      <Sidebar onNovaRota={handleNovaRota} loading={loading} />

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
