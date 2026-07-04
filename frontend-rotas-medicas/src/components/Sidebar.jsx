const NAV_ITEMS = [
  {
    id: 'nova-rota',
    label: 'Nova Rota',
    active: true,
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="16" /><line x1="8" y1="12" x2="16" y2="12" />
      </svg>
    ),
  },
]

export default function Sidebar({ onNovaRota, loading }) {
  return (
    <header
      className="flex-shrink-0 bg-[#0B1A30] text-white flex items-center px-5 gap-5 shadow-lg z-20 select-none"
      style={{ height: 52 }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 pr-5 border-r border-white/10 flex-shrink-0">
        <div className="w-8 h-8 rounded-xl bg-blue-500 flex items-center justify-center shadow-md flex-shrink-0">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
        </div>
        <div>
          <div className="text-blue-400 font-bold text-xs leading-none tracking-wider">ROTA</div>
          <div className="text-white font-bold text-xs leading-none tracking-wider mt-0.5">MÉDICA</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex items-center gap-1">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            type="button"
            onClick={item.id === 'nova-rota' ? onNovaRota : undefined}
            disabled={item.id === 'nova-rota' && loading}
            title={item.id === 'nova-rota' ? 'Limpa o formulário e o resultado atual, voltando à tela inicial.' : undefined}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed ${item.active
              ? 'bg-blue-600 text-white'
              : 'text-blue-200/60 hover:text-white hover:bg-white/5'
              }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Right actions */}
      <div className="flex items-center gap-3">
        <button className="text-[11px] text-blue-300/80 border border-blue-700/50 px-3 py-1 rounded-full hover:bg-blue-800/50 hover:text-blue-200 transition-colors whitespace-nowrap">
          💡FIAP Tech Challenge Fase 2 - 9IADT - Grupo 88
        </button>
        <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
          G
        </div>
      </div>
    </header>
  )
}
