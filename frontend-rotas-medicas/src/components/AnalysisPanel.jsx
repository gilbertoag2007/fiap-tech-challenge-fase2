import { useEffect, useRef } from 'react'
import Chart from 'chart.js/auto'

function SummaryCard({ label, value, unit, accent }) {
  return (
    <div className="bg-slate-50 rounded-lg p-2.5 text-center border border-slate-100">
      <div className={`text-base font-bold leading-none ${accent ? 'text-blue-600' : 'text-slate-800'}`}>
        {value}
        {unit && <span className="text-[10px] font-normal text-slate-400 ml-0.5">{unit}</span>}
      </div>
      <div className="text-[9px] text-slate-400 mt-1.5 uppercase tracking-wide font-medium">{label}</div>
    </div>
  )
}

export default function AnalysisPanel({ geoJson }) {
  const chartRef = useRef(null)
  const instanceRef = useRef(null)

  const {
    km_total = 0,
    aptidao_final = 0,
    total_cidades = 0,
    historico_evolucao = [],
    features = [],
    parou_antecipadamente = false,
    epocas_executadas = null,
  } = geoJson

  useEffect(() => {
    if (!chartRef.current) return

    instanceRef.current?.destroy()

    instanceRef.current = new Chart(chartRef.current, {
      type: 'line',
      data: {
        labels: historico_evolucao.map(h => String(h.epoca)),
        datasets: [
          {
            data: historico_evolucao.map(h => h.distancia_km),
            borderColor: '#1d6ae8',
            backgroundColor: 'rgba(29, 106, 232, 0.08)',
            fill: true,
            tension: 0.4,
            pointRadius: 3,
            pointBackgroundColor: '#1d6ae8',
            pointBorderColor: '#fff',
            pointBorderWidth: 1.5,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: ([ctx]) => `Época ${ctx.label}`,
              label: ctx =>
                ` ${ctx.parsed.y.toLocaleString('pt-BR', { maximumFractionDigits: 1 })} km`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: '#f8fafc' },
            border: { color: '#e2e8f0' },
            ticks: {
              font: { size: 9 },
              color: '#94a3b8',
              maxTicksLimit: 6,
            },
          },
          y: {
            grid: { color: '#f8fafc' },
            border: { color: '#e2e8f0' },
            ticks: {
              font: { size: 9 },
              color: '#94a3b8',
              callback: v =>
                v >= 1000
                  ? `${(v / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}k`
                  : String(v),
            },
          },
        },
      },
    })

    return () => instanceRef.current?.destroy()
  }, [historico_evolucao])

  const orderedCities = [...features].sort(
    (a, b) =>
      parseInt(a.properties.ordem_visita) - parseInt(b.properties.ordem_visita)
  )

  return (
    <div
      className="flex-shrink-0 flex flex-col overflow-hidden border-l border-slate-200 bg-white"
      style={{ width: 340 }}
    >
      {/* Header */}
      <div className="bg-[#0B1A30] px-4 py-3 flex-shrink-0">
        <h2 className="text-sm font-bold text-white">Análise da Rota</h2>
        <p className="text-[10px] text-blue-300/60 mt-0.5">Resultado da otimização genética</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-2 p-3 border-b border-slate-100 flex-shrink-0">
        <SummaryCard label="Cidades" value={total_cidades} />
        <SummaryCard
          label="Distância"
          value={km_total.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
          unit="km"
          accent
        />
        <SummaryCard
          label="Aptidão"
          value={aptidao_final.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
        />
      </div>

      {/* Evolution chart */}
      <div className="px-3 pt-3 pb-3 flex-shrink-0 border-b border-slate-100">
        <div className="flex items-center justify-between mb-2">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            Evolução da Distância
          </p>
          <span className="text-[9px] text-slate-400">por época</span>
        </div>
        {parou_antecipadamente && (
          <div className="mb-2 flex items-center gap-1.5 bg-amber-50 border border-amber-200 rounded-md px-2 py-1">
            <span className="text-[9px] text-amber-700 font-medium">
              ⏹ Parada antecipada na época {epocas_executadas} — sem melhora na aptidão.
            </span>
          </div>
        )}
        {historico_evolucao.length > 0 ? (
          <div style={{ height: 150 }}>
            <canvas ref={chartRef} />
          </div>
        ) : (
          <div className="h-[150px] flex items-center justify-center text-[11px] text-slate-400">
            Sem dados de histórico
          </div>
        )}
      </div>

      {/* City list — scrollable */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-3 pt-3 pb-2 flex-shrink-0 flex items-center justify-between">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            Cidades da Rota
          </p>
          <span className="text-[9px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded-full font-semibold">
            {orderedCities.length} cidades
          </span>
        </div>

        <div className="flex-1 overflow-y-auto">
          {orderedCities.map((f, i) => {
            const { ordem_visita, cidade, uf, produto, prioridade } = f.properties
            const isHigh = prioridade === '1'
            const num = parseInt(ordem_visita)
            return (
              <div
                key={i}
                className="flex items-start gap-2.5 px-3 py-2.5 border-b border-slate-50 hover:bg-slate-50 transition-colors"
              >
                {/* Numbered badge */}
                <div
                  className={`flex items-center justify-center rounded-full text-white font-bold flex-shrink-0 mt-0.5 ${
                    isHigh ? 'bg-red-500' : 'bg-blue-600'
                  }`}
                  style={{
                    minWidth: 22,
                    height: 22,
                    fontSize: num > 9 ? 9 : 10,
                    paddingLeft: 3,
                    paddingRight: 3,
                  }}
                >
                  {ordem_visita}
                </div>

                {/* City info */}
                <div className="flex-1 min-w-0">
                  <div className="text-[11px] font-semibold text-slate-700 truncate">
                    {cidade}
                    <span className="text-slate-400 font-normal"> / {uf}</span>
                  </div>
                  {produto && (
                    <div className="text-[10px] text-slate-400 truncate mt-0.5">
                      📦 {produto}
                    </div>
                  )}
                </div>

                {/* Priority badge */}
                <span
                  className={`text-[9px] font-bold px-1.5 py-0.5 rounded-md flex-shrink-0 mt-0.5 ${
                    isHigh ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'
                  }`}
                >
                  P{prioridade}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
