import { useEffect, useRef } from 'react'
import Chart from 'chart.js/auto'

function SummaryCard({ label, value, unit, accent, hint }) {
  return (
    <div className="bg-slate-50 rounded-lg p-2.5 text-center border border-slate-100" title={hint}>
      <div className={`text-base font-bold leading-none ${accent ? 'text-blue-600' : 'text-slate-800'}`}>
        {value}
        {unit && <span className="text-[10px] font-normal text-slate-400 ml-0.5">{unit}</span>}
      </div>
      <div className="text-[9px] text-slate-400 mt-1.5 uppercase tracking-wide font-medium">{label}</div>
    </div>
  )
}

function formatCompact(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}M`
  if (n >= 1_000) return `${(n / 1_000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}k`
  return String(n)
}

function PriorityPositionBar({ label, count, percentual, colorClass, dotClass }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-600">
          <span className={`w-2 h-2 rounded-full ${dotClass}`} />
          {label} <span className="text-slate-400 font-normal">({count}x)</span>
        </span>
        <span className="text-[10px] font-bold text-slate-700">
          {percentual === null ? '—' : `${percentual.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`}
        </span>
      </div>
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        {percentual !== null && (
          <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${percentual}%` }} />
        )}
      </div>
    </div>
  )
}

export default function AnalysisPanel({ geoJson }) {
  const chartRef = useRef(null)
  const instanceRef = useRef(null)
  const chartAptidaoRef = useRef(null)
  const instanceAptidaoRef = useRef(null)

  const {
    km_total = 0,
    aptidao_final = 0,
    total_cidades = 0,
    historico_evolucao = [],
    features = [],
    parou_antecipadamente = false,
    epocas_executadas = null,
    total_avaliacoes_aptidao = 0,
    rota_valida = true,
    cidades_prioridade_1 = 0,
    posicao_media_prioridade_1_percentual = null,
    cidades_prioridade_2 = 0,
    posicao_media_prioridade_2_percentual = null,
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

  useEffect(() => {
    if (!chartAptidaoRef.current) return

    instanceAptidaoRef.current?.destroy()

    const temDiversidade = historico_evolucao.some(h => h.diversidade !== undefined)

    instanceAptidaoRef.current = new Chart(chartAptidaoRef.current, {
      type: 'line',
      data: {
        labels: historico_evolucao.map(h => String(h.epoca)),
        datasets: [
          {
            label: 'Melhor',
            data: historico_evolucao.map(h => h.aptidao),
            borderColor: '#1d6ae8',
            backgroundColor: 'rgba(29, 106, 232, 0.08)',
            tension: 0.4,
            pointRadius: 0,
            borderWidth: 2,
            yAxisID: 'y',
          },
          {
            label: 'Média',
            data: historico_evolucao.map(h => h.aptidao_media ?? null),
            borderColor: '#94a3b8',
            borderDash: [4, 3],
            tension: 0.4,
            pointRadius: 0,
            borderWidth: 1.5,
            yAxisID: 'y',
          },
          {
            label: 'Pior',
            data: historico_evolucao.map(h => h.aptidao_pior ?? null),
            borderColor: '#f59e0b',
            borderDash: [2, 2],
            tension: 0.4,
            pointRadius: 0,
            borderWidth: 1.5,
            yAxisID: 'y',
          },
          ...(temDiversidade
            ? [{
                label: 'Diversidade',
                data: historico_evolucao.map(h => (h.diversidade !== undefined ? h.diversidade * 100 : null)),
                borderColor: '#16a34a',
                backgroundColor: 'rgba(22, 163, 74, 0.08)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                borderWidth: 2,
                yAxisID: 'y1',
              }]
            : []),
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            display: true,
            position: 'bottom',
            labels: { boxWidth: 8, font: { size: 9 }, color: '#64748b', padding: 8 },
          },
          tooltip: {
            callbacks: {
              title: ([ctx]) => `Época ${ctx.label}`,
              label: ctx =>
                ctx.dataset.label === 'Diversidade'
                  ? ` Diversidade: ${ctx.parsed.y.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`
                  : ` ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: '#f8fafc' },
            border: { color: '#e2e8f0' },
            ticks: { font: { size: 9 }, color: '#94a3b8', maxTicksLimit: 6 },
          },
          y: {
            grid: { color: '#f8fafc' },
            border: { color: '#e2e8f0' },
            title: { display: true, text: 'Aptidão', font: { size: 9 }, color: '#94a3b8' },
            ticks: {
              font: { size: 9 },
              color: '#94a3b8',
              callback: v =>
                v >= 1000
                  ? `${(v / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}k`
                  : String(v),
            },
          },
          y1: {
            position: 'right',
            min: 0,
            max: 100,
            grid: { display: false },
            border: { color: '#e2e8f0' },
            title: { display: true, text: 'Diversidade %', font: { size: 9 }, color: '#94a3b8' },
            ticks: { font: { size: 9 }, color: '#94a3b8', callback: v => `${v}%` },
          },
        },
      },
    })

    return () => instanceAptidaoRef.current?.destroy()
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
      <div className="bg-[#0B1A30] px-4 py-3 flex-shrink-0 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Análise da Rota</h2>
          <p className="text-[10px] text-blue-300/60 mt-0.5">Resultado da otimização genética</p>
        </div>
        <span
          className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full flex-shrink-0 ${
            rota_valida ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
          }`}
          title={
            rota_valida
              ? 'Rota passou na validação de integridade (sem duplicatas, começa/termina na partida)'
              : 'Rota reprovou na validação de integridade — resultado não confiável'
          }
        >
          {rota_valida ? '✓ Válida' : '⚠ Inválida'}
        </span>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-2 p-3 border-b border-slate-100 flex-shrink-0">
        <SummaryCard
          label="Cidades"
          value={total_cidades}
          hint="Número total de cidades incluídas na rota otimizada, contando a cidade de partida."
        />
        <SummaryCard
          label="Distância"
          value={km_total.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
          unit="km"
          accent
          hint="Distância total percorrida pela rota otimizada, em quilômetros — soma das distâncias entre cidades consecutivas (fórmula de Haversine)."
        />
        <SummaryCard
          label="Aptidão"
          value={aptidao_final.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
          hint="Valor usado pelo algoritmo genético para comparar rotas: distância total menos a bonificação por entregas de prioridade 1 antecipadas. Quanto menor, melhor — pode ficar negativo quando a bonificação supera a distância."
        />
        <SummaryCard
          label="Avaliações"
          value={formatCompact(total_avaliacoes_aptidao)}
          hint="Número total de novas rotas geradas e avaliadas ao longo de toda a execução do algoritmo genético — mede o esforço de busca realizado, de forma mais precisa do que contar só as épocas (populações maiores avaliam mais rotas por época)."
        />
      </div>

      {/* Priority positioning comparison */}
      <div className="px-3 pt-3 pb-3 flex-shrink-0 border-b border-slate-100 space-y-2.5">
        <div className="flex items-center justify-between">
          <p
            className="text-[10px] font-bold text-slate-500 uppercase tracking-widest"
            title="Compara em que ponto da rota (0% = início, 100% = fim) as cidades de cada prioridade tendem a ser visitadas. Prioridade 1 (vacinas) recebe bônus na aptidão por aparecer mais cedo na rota; prioridade 2 (insumos) é mostrada só como comparação, sem esse incentivo."
          >
            Posição Média por Prioridade
          </p>
          <span className="text-[9px] text-slate-400">0% início · 100% fim</span>
        </div>
        <PriorityPositionBar
          label="P1 · vacinas"
          count={cidades_prioridade_1}
          percentual={posicao_media_prioridade_1_percentual}
          colorClass="bg-red-500"
          dotClass="bg-red-500"
        />
        <PriorityPositionBar
          label="P2 · insumos"
          count={cidades_prioridade_2}
          percentual={posicao_media_prioridade_2_percentual}
          colorClass="bg-blue-600"
          dotClass="bg-blue-600"
        />
      </div>

      {/* Evolution chart */}
      <div className="px-3 pt-3 pb-3 flex-shrink-0 border-b border-slate-100">
        <div className="flex items-center justify-between mb-2">
          <p
            className="text-[10px] font-bold text-slate-500 uppercase tracking-widest"
            title="Distância (km) da melhor rota encontrada a cada época, amostrada a cada 10% do total de épocas configuradas. Com elitismo ativado, essa linha nunca deve subir — se ficar reta por muitas amostras seguidas, o algoritmo já convergiu para esse ponto."
          >
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

      {/* Fitness (best/mean/worst) + population diversity chart */}
      <div className="px-3 pt-3 pb-3 flex-shrink-0 border-b border-slate-100">
        <div className="flex items-center justify-between mb-2">
          <p
            className="text-[10px] font-bold text-slate-500 uppercase tracking-widest"
            title="Aptidão do melhor, da média e do pior indivíduo da população a cada época, mais a diversidade da população (% de arestas distintas em uso, eixo direito). Média se afastando da melhor e diversidade caindo rápido para perto de 0% indicam convergência prematura — a busca ficou presa girando em torno das mesmas rotas."
          >
            Aptidão e Diversidade
          </p>
          <span className="text-[9px] text-slate-400">por época</span>
        </div>
        {historico_evolucao.length > 0 ? (
          <div style={{ height: 165 }}>
            <canvas ref={chartAptidaoRef} />
          </div>
        ) : (
          <div className="h-[165px] flex items-center justify-center text-[11px] text-slate-400">
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
