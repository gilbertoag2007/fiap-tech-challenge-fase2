export default function MedicalIllustration() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 px-8 bg-gradient-to-br from-slate-50 to-blue-50 animate-fade-in-up">
      {/* SVG ilustração */}
      <div className="flex flex-col items-center gap-2">
        <svg
          width="260"
          height="210"
          viewBox="0 0 260 210"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="drop-shadow-sm"
        >
          <defs>
            <filter id="softGlow" x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="14" />
            </filter>
          </defs>

          {/* Glows de fundo (profundidade) */}
          <circle cx="55" cy="45" r="55" fill="#BFDBFE" opacity="0.35" filter="url(#softGlow)" />
          <circle cx="215" cy="150" r="60" fill="#C7D8F7" opacity="0.3" filter="url(#softGlow)" />

          {/* Grid do "mapa" */}
          {[40, 80, 120, 160].map(y => (
            <line key={`h${y}`} x1="15" y1={y} x2="245" y2={y}
              stroke="#C7D8F7" strokeWidth="0.8" strokeDasharray="4 4" />
          ))}
          {[70, 130, 190].map(x => (
            <line key={`v${x}`} x1={x} y1="15" x2={x} y2="195"
              stroke="#C7D8F7" strokeWidth="0.8" strokeDasharray="4 4" />
          ))}

          {/* Rota otimizada (curva suave) */}
          <path
            d="M60,170 C40,140 35,120 50,100 C60,80 75,65 100,55 C125,45 145,45 165,50 C190,57 210,80 205,105 C200,130 175,150 150,165 C120,180 85,180 60,170 Z"
            fill="none"
            stroke="#1D6AE8"
            strokeWidth="2.4"
            strokeDasharray="7 4"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.8"
          />
          <polygon points="46,118 38,131 51,132" fill="#1D6AE8" opacity="0.65" />
          <polygon points="185,60 195,64 190,73" fill="#1D6AE8" opacity="0.65" />

          {/* Cidade de partida (marcador distinto) */}
          <circle cx="60" cy="170" r="21" fill="white" stroke="#1D6AE8" strokeWidth="2.5" />
          <circle cx="60" cy="170" r="16" fill="#1D6AE8" />
          <path d="M60 163v11M55 168l5-5 5 5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

          {/* Cidades prioridade 1 (vacina) */}
          <circle cx="50" cy="100" r="17" fill="white" stroke="#EF4444" strokeWidth="2" />
          <circle cx="50" cy="100" r="13" fill="#EF4444" />
          <text x="50" y="105" textAnchor="middle" fill="white" fontSize="11" fontWeight="700" fontFamily="Inter, sans-serif">1</text>

          <circle cx="100" cy="55" r="17" fill="white" stroke="#EF4444" strokeWidth="2" />
          <circle cx="100" cy="55" r="13" fill="#EF4444" />
          <text x="100" y="60" textAnchor="middle" fill="white" fontSize="11" fontWeight="700" fontFamily="Inter, sans-serif">2</text>

          {/* Cidades prioridade 2 (insumo) */}
          <circle cx="165" cy="50" r="17" fill="white" stroke="#1D6AE8" strokeWidth="2" />
          <circle cx="165" cy="50" r="13" fill="#1D6AE8" />
          <text x="165" y="55" textAnchor="middle" fill="white" fontSize="11" fontWeight="700" fontFamily="Inter, sans-serif">3</text>

          <circle cx="205" cy="105" r="17" fill="white" stroke="#1D6AE8" strokeWidth="2" />
          <circle cx="205" cy="105" r="13" fill="#1D6AE8" />
          <text x="205" y="110" textAnchor="middle" fill="white" fontSize="11" fontWeight="700" fontFamily="Inter, sans-serif">4</text>

          <circle cx="150" cy="165" r="17" fill="white" stroke="#1D6AE8" strokeWidth="2" />
          <circle cx="150" cy="165" r="13" fill="#1D6AE8" />
          <text x="150" y="170" textAnchor="middle" fill="white" fontSize="11" fontWeight="700" fontFamily="Inter, sans-serif">5</text>

          {/* Cruz médica (tema) */}
          <rect x="119" y="103" width="22" height="7" rx="2.5" fill="#10B981" />
          <rect x="126" y="96" width="7" height="22" rx="2.5" fill="#10B981" />

          {/* Chip: rota validada */}
          <g transform="translate(15, 16)">
            <rect x="0" y="0" width="70" height="20" rx="10" fill="white" opacity="0.9" stroke="#D1FAE5" strokeWidth="1" />
            <path d="M10 10l2.5 2.5L16 8" stroke="#059669" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <text x="38" y="14" textAnchor="middle" fill="#059669" fontSize="9" fontWeight="700" fontFamily="Inter, sans-serif">Válida</text>
          </g>

          {/* Chip: mini gráfico de evolução (aptidão + diversidade) */}
          <g transform="translate(178, 14)">
            <rect x="0" y="0" width="66" height="34" rx="8" fill="white" opacity="0.92" stroke="#E2E8F0" strokeWidth="1" />
            <polyline points="6,26 18,20 30,22 42,10 58,8" fill="none" stroke="#1D6AE8" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            <polyline points="6,28 18,27 30,26 42,25 58,24" fill="none" stroke="#16A34A" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
          </g>
        </svg>

        {/* Caption */}
        <div className="text-center max-w-xs">
          <h3 className="text-base font-semibold text-slate-600">Pronto para otimizar</h3>
          <p className="text-sm text-slate-400 mt-1 leading-relaxed">
            Descreva a rota no formulário ao lado e clique em <strong className="text-blue-500">Gerar Rota</strong>.
          </p>
        </div>
      </div>

      {/* Feature cards — refletem as funcionalidades implementadas */}
      <div className="grid grid-cols-3 gap-3 w-full max-w-lg">
        {[
          {
            icon: (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1D6AE8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M9 12l2 2 4-4" />
              </svg>
            ),
            title: 'Priorização inteligente',
            desc: 'Entregas urgentes são antecipadas sem ignorar a distância total.',
          },
          {
            icon: (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1D6AE8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" /><circle cx="12" cy="12" r="3" />
              </svg>
            ),
            title: 'AG configurável',
            desc: 'Seleção, crossover, mutação, 2-opt e parada antecipada ajustáveis.',
          },
          {
            icon: (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1D6AE8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 3v18h18" /><path d="M18 17V9" /><path d="M13 17V5" /><path d="M8 17v-3" />
              </svg>
            ),
            title: 'Diagnóstico completo',
            desc: 'Evolução, diversidade da população e validação a cada execução.',
          },
        ].map(item => (
          <div
            key={item.title}
            className="bg-white rounded-2xl p-3.5 shadow-sm border border-slate-100 text-center"
          >
            <div className="flex justify-center mb-2">{item.icon}</div>
            <div className="text-[11px] font-semibold text-slate-700">{item.title}</div>
            <div className="text-[10px] text-slate-400 mt-1 leading-relaxed">{item.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
