import { useState } from 'react'

export default function LoginForm({ onLogin, loading, error, avisoSessaoExpirada }) {
  const [usuario, setUsuario] = useState('')
  const [senha, setSenha] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!usuario.trim() || !senha.trim() || loading) return
    onLogin({ usuario: usuario.trim(), senha })
  }

  return (
    <div className="relative flex items-center justify-center h-screen overflow-hidden bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Glows de fundo — mesma linguagem visual da ilustração inicial */}
      <div className="absolute -top-24 -left-24 w-80 h-80 bg-blue-200 rounded-full opacity-30 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-28 -right-20 w-96 h-96 bg-blue-300 rounded-full opacity-20 blur-3xl pointer-events-none" />

      <form
        onSubmit={handleSubmit}
        className="relative bg-white rounded-2xl shadow-xl border border-slate-100 p-8 w-full max-w-sm mx-4 animate-fade-in-up"
      >
        {/* Logo */}
        <div className="flex flex-col items-center gap-3 mb-6">
          <div className="w-14 h-14 rounded-2xl bg-blue-500 flex items-center justify-center shadow-lg shadow-blue-200">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
          </div>
          <div className="text-center leading-none">
            <div className="text-blue-600 font-bold text-sm tracking-wider">ROTA</div>
            <div className="text-slate-800 font-bold text-sm tracking-wider mt-1">MÉDICA</div>
          </div>
        </div>

        <h1 className="text-base font-bold text-slate-800 text-center">Acesso restrito</h1>
        <p className="text-xs text-slate-400 text-center mt-1 mb-5 leading-relaxed">
          Faça login para gerar rotas otimizadas.
        </p>

        {avisoSessaoExpirada && !error && (
          <div className="mb-4 flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            <span className="text-[11px] text-amber-700 leading-snug">
              ⏹ Sua sessão expirou. Faça login novamente para continuar.
            </span>
          </div>
        )}

        {error && (
          <div className="mb-4 flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            <span className="text-[11px] text-red-700 leading-snug">{error}</span>
          </div>
        )}

        <div className="mb-3">
          <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1">
            Usuário
          </label>
          <input
            type="text"
            value={usuario}
            onChange={e => setUsuario(e.target.value)}
            autoComplete="username"
            autoFocus
            required
            disabled={loading}
            className="w-full text-sm border border-slate-200 bg-slate-50 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all disabled:opacity-60"
          />
        </div>

        <div className="mb-5">
          <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1">
            Senha
          </label>
          <input
            type="password"
            value={senha}
            onChange={e => setSenha(e.target.value)}
            autoComplete="current-password"
            required
            disabled={loading}
            className="w-full text-sm border border-slate-200 bg-slate-50 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all disabled:opacity-60"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold text-sm rounded-xl transition-colors shadow-md shadow-blue-200"
        >
          {loading ? (
            <>
              <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Entrando...
            </>
          ) : (
            <>
              Entrar
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </>
          )}
        </button>
      </form>
    </div>
  )
}
