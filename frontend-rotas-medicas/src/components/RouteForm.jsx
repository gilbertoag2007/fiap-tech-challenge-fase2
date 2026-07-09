import { useState } from 'react'

const DEFAULTS = {
  mensagem: '',
  epocas: 100,
  tamanho_populacao: 200,
  tamanho_elite: 20,
  grau_mutacao: 1.0,
  capacidade_veiculo_kg: '',
  elitismo: 1,
  populacao_apenas_aleatoria: 0,
  tipo_selecao: 'truncamento',
  tipo_crossover: 'ox',
  tipo_mutacao: 'ambos',
  usar_2opt: 0,
  tipo_inicializacao: 'aleatoria',
  usar_parada_antecipada: 0,
  paciencia_parada_antecipada: 30,
}

// --- Componentes auxiliares ---

function NumberInput({ label, field, form, onChange, min, max, step = 1, placeholder, disabled, hint, required = true }) {
  return (
    <div>
      <label
        className="block text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1 cursor-help"
        title={hint}
      >
        {label}
      </label>
      <input
        type="number"
        value={form[field]}
        onChange={e => onChange(field, e.target.value)}
        min={min}
        max={max}
        step={step}
        placeholder={placeholder}
        required={!disabled && required}
        disabled={disabled}
        title={hint}
        className={`w-full text-sm border rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all ${disabled ? 'border-slate-100 bg-slate-100 text-slate-400 cursor-not-allowed' : 'border-slate-200 bg-slate-50 text-slate-700'
          }`}
      />
    </div>
  )
}

/** Controle segmentado para 2 opções (ex.: Truncamento / Torneio) */
function PillRadio({ label, field, form, onChange, options }) {
  return (
    <div>
      <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1">
        {label}
      </label>
      <div className="flex rounded-lg border border-slate-200 overflow-hidden bg-slate-50 text-[11px] font-medium">
        {options.map((opt, i) => {
          const selected = form[field] === opt.value
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange(field, opt.value)}
              title={opt.desc}
              className={`flex-1 py-1.5 px-1 transition-all truncate ${i > 0 ? 'border-l border-slate-200' : ''
                } ${selected ? 'bg-blue-600 text-white' : 'text-slate-500 hover:bg-slate-100'}`}
            >
              {opt.label}
              {opt.badge && (
                <span className={`ml-1 text-[9px] ${selected ? 'opacity-80' : 'text-emerald-600'}`}>
                  ★
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}

/** Cards 2×2 para mutação (4 opções) */
function MutacaoCards({ form, onChange }) {
  const options = [
    {
      value: 'ambos', label: 'Swap + Inversão', badge: true,
      desc: 'Aplica troca de vizinhos e inversão de segmento em sequência a cada mutação.',
      hint: 'Combina uma exploração leve (swap) com uma mais ampla (inversão) a cada mutação. É a opção mais equilibrada e recomendada para a maioria dos casos.',
    },
    {
      value: 'or_opt', label: 'Or-opt',
      desc: 'Remove um segmento de 1–3 cidades e o reinsere em outra posição.',
      hint: 'Consegue realocar cidades a longas distâncias na rota, sendo mais eficaz que o swap simples para escapar de ótimos locais — mas o resultado é menos previsível.',
    },
    {
      value: 'swap', label: 'Swap adjacente',
      desc: 'Troca a posição de duas cidades vizinhas na rota.',
      hint: 'É a mutação mais sutil e barata: bom para pequenos ajustes finos, mas mais lenta para escapar de ótimos locais distantes.',
    },
    {
      value: 'inversao', label: 'Inversão',
      desc: 'Inverte a ordem de um segmento inteiro da rota.',
      hint: 'Gera uma exploração mais ampla que o swap simples e ajuda a desfazer cruzamentos de trajeto (rotas com auto-interseção).',
    },
  ]
  return (
    <div>
      <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1">
        Operador de Mutação
      </label>
      <div className="grid grid-cols-2 gap-1.5">
        {options.map(opt => {
          const selected = form.tipo_mutacao === opt.value
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange('tipo_mutacao', opt.value)}
              title={opt.hint}
              className={`text-left p-2 rounded-lg border-2 transition-all ${selected ? 'border-blue-500 bg-blue-50' : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <div className={`w-2.5 h-2.5 rounded-full border-2 flex-shrink-0 transition-colors ${selected ? 'border-blue-500 bg-blue-500' : 'border-slate-300'
                  }`} />
                <span className="text-[10px] font-semibold text-slate-700 leading-tight truncate">
                  {opt.label}
                </span>
                {opt.badge && (
                  <span className="text-[9px] bg-emerald-100 text-emerald-700 px-1 rounded font-semibold ml-auto flex-shrink-0">
                    Padrão
                  </span>
                )}
              </div>
              <p className="text-[9px] text-slate-400 pl-4 leading-tight">{opt.desc}</p>
            </button>
          )
        })}
      </div>
    </div>
  )
}

/** Ícone + popover com as restrições que o AG sempre respeita ao montar a rota */
function RestricoesInfo() {
  return (
    <div className="relative group ml-auto">
      <button
        type="button"
        className="w-5 h-5 rounded-full bg-white/70 hover:bg-white flex items-center justify-center transition-colors flex-shrink-0"
        aria-label="Restrições respeitadas pelo algoritmo ao gerar a rota"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#1D6AE8" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
      </button>

      <div className="invisible opacity-0 group-hover:visible group-hover:opacity-100 transition-opacity duration-150 absolute right-0 top-full mt-2 w-64 bg-white border border-slate-200 rounded-xl shadow-lg p-3 z-20 text-left">
        <p className="text-[10px] font-bold text-slate-600 uppercase tracking-wide mb-1.5">
          Regras rígidas (sempre garantidas)
        </p>
        <ul className="space-y-1 mb-2.5">
          <li className="text-[10px] text-slate-600 leading-snug flex gap-1.5">
            <span className="text-emerald-500 font-bold flex-shrink-0">✓</span>
            Todas as cidades da mensagem são visitadas.
          </li>
          <li className="text-[10px] text-slate-600 leading-snug flex gap-1.5">
            <span className="text-emerald-500 font-bold flex-shrink-0">✓</span>
            Nenhuma cidade é visitada mais de uma vez.
          </li>
          <li className="text-[10px] text-slate-600 leading-snug flex gap-1.5">
            <span className="text-emerald-500 font-bold flex-shrink-0">✓</span>
            Rota circular: a cidade de partida também é o destino final.
          </li>
        </ul>
        <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wide mb-1">
          Critério de otimização (não é uma regra rígida)
        </p>
        <p className="text-[10px] text-slate-500 leading-snug flex gap-1.5">
          <span className="text-blue-500 font-bold flex-shrink-0">~</span>
          Cidades com produtos de maior prioridade (vacinas) recebem bônus na aptidão por
          aparecerem mais cedo na rota — tendem a ser visitadas primeiro, mas isso pode ceder
          espaço a uma rota com economia de distância maior.
        </p>
      </div>
    </div>
  )
}

/** Toggle switch para o 2-opt e parada antecipada */
function Toggle({ label, desc, field, form, onChange, warn, disabled, disabledReason, hint }) {
  const checked = form[field] === 1
  return (
    <div
      title={disabled ? disabledReason : hint}
      className={`flex items-center gap-3 p-2.5 rounded-lg border transition-all ${disabled ? 'border-slate-100 bg-slate-50/60 opacity-60' : checked ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-slate-50'
      }`}>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-semibold text-slate-700">{label}</div>
        <div className="text-[9px] text-slate-400 leading-tight mt-0.5">
          {disabled && disabledReason ? disabledReason : desc}
        </div>
        {checked && warn && !disabled && (
          <div className="text-[9px] text-amber-600 font-semibold mt-1">⚠️ {warn}</div>
        )}
      </div>
      <button
        type="button"
        disabled={disabled}
        onClick={() => onChange(field, checked ? 0 : 1)}
        className={`relative inline-flex h-5 w-9 flex-shrink-0 rounded-full border-2 border-transparent transition-colors ${disabled ? 'bg-slate-200 cursor-not-allowed' : checked ? 'bg-blue-600' : 'bg-slate-300'
          }`}
      >
        <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-4' : 'translate-x-0'
          }`} />
      </button>
    </div>
  )
}

// --- Formulário principal ---

const MENSAGEM_MAX_LENGTH = 500
const MENSAGEM_MIN_LENGTH = 20

export default function RouteForm({ onSubmit, onClear, loading, error }) {
  const [form, setForm] = useState(DEFAULTS)
  const [mensagemErro, setMensagemErro] = useState(null)

  const handleChange = (field, value) => {
    if (field === 'mensagem') {
      if (value.length > MENSAGEM_MAX_LENGTH) {
        value = value.slice(0, MENSAGEM_MAX_LENGTH)
        setMensagemErro(`Limite de ${MENSAGEM_MAX_LENGTH} caracteres atingido.`)
      } else if (value.length > 0 && value.length < MENSAGEM_MIN_LENGTH) {
        setMensagemErro(`Digite ao menos ${MENSAGEM_MIN_LENGTH} caracteres (faltam ${MENSAGEM_MIN_LENGTH - value.length}).`)
      } else {
        setMensagemErro(null)
      }
    }
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const handleMethodChange = (isElitismo) => {
    setForm(prev => ({
      ...prev,
      elitismo: isElitismo ? 1 : 0,
      populacao_apenas_aleatoria: isElitismo ? 0 : 1,
      // Parada antecipada só é confiável com elitismo ativo — desliga ao sair dele.
      usar_parada_antecipada: isElitismo ? prev.usar_parada_antecipada : 0,
    }))
  }

  const handleClear = () => {
    setForm(DEFAULTS)
    setMensagemErro(null)
    onClear()
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (form.mensagem.length > MENSAGEM_MAX_LENGTH) {
      setMensagemErro(`A mensagem excede o limite de ${MENSAGEM_MAX_LENGTH} caracteres.`)
      return
    }
    if (form.mensagem.length < MENSAGEM_MIN_LENGTH) {
      setMensagemErro(`Digite ao menos ${MENSAGEM_MIN_LENGTH} caracteres (faltam ${MENSAGEM_MIN_LENGTH - form.mensagem.length}).`)
      return
    }

    onSubmit({
      mensagem: form.mensagem,
      epocas: parseInt(form.epocas),
      tamanho_populacao: parseInt(form.tamanho_populacao),
      tamanho_elite: parseInt(form.tamanho_elite),
      grau_mutacao: parseFloat(form.grau_mutacao),
      capacidade_veiculo_kg: form.capacidade_veiculo_kg === '' ? null : parseFloat(form.capacidade_veiculo_kg),
      elitismo: form.elitismo,
      populacao_apenas_aleatoria: form.populacao_apenas_aleatoria,
      tipo_selecao: form.tipo_selecao,
      tipo_crossover: form.tipo_crossover,
      tipo_mutacao: form.tipo_mutacao,
      usar_2opt: form.usar_2opt,
      tipo_inicializacao: form.tipo_inicializacao,
      usar_parada_antecipada: form.elitismo === 1 ? form.usar_parada_antecipada : 0,
      paciencia_parada_antecipada: parseInt(form.paciencia_parada_antecipada),
    })
  }

  const charCount = form.mensagem.length

  return (
    <form onSubmit={handleSubmit} className="p-4 flex flex-col gap-4">

      {/* Header */}
      <div className="pb-3 border-b border-slate-100">
        <h1 className="text-lg font-bold text-slate-800">Criar Nova Rota</h1>
        <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
          Informe em linguagem natural quais cidades e produtos devem fazer parte da rota.
        </p>
      </div>

      {/* Mensagem */}
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#1D6AE8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-slate-700">Descreva sua rota</span>
        </div>
        <textarea
          value={form.mensagem}
          onChange={e => handleChange('mensagem', e.target.value)}
          placeholder="Ex.: Monte uma rota saindo do Rio de Janeiro para entregar vacinas da Covid 19 nas cidades da baixada fluminense e região serrana do RJ."
          rows={3}
          minLength={MENSAGEM_MIN_LENGTH}
          maxLength={MENSAGEM_MAX_LENGTH}
          required
          aria-invalid={Boolean(mensagemErro)}
          className={`w-full text-sm border rounded-xl p-3 resize-none focus:outline-none focus:ring-2 focus:border-transparent text-slate-700 placeholder-slate-300 bg-slate-50 transition-all leading-relaxed ${mensagemErro ? 'border-red-300 focus:ring-red-400' : 'border-slate-200 focus:ring-blue-400'
            }`}
        />
        <div className="flex items-center justify-between mt-0.5">
          <span className="text-[10px] text-red-500">{mensagemErro || ''}</span>
          <span className={`text-[10px] flex-shrink-0 ${charCount >= MENSAGEM_MAX_LENGTH ? 'text-red-500 font-semibold' : charCount > 450 ? 'text-orange-500' : 'text-slate-300'
            }`}>
            {charCount} / {MENSAGEM_MAX_LENGTH}
          </span>
        </div>
      </div>

      {/* Algoritmos Genéticos */}
      <div className="border border-slate-200 rounded-xl">
        <div className="bg-gradient-to-r from-slate-50 to-blue-50 rounded-t-xl px-3 py-2 border-b border-slate-200 flex items-center gap-2">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#1D6AE8" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" /><circle cx="12" cy="12" r="3" />
          </svg>
          <span className="text-xs font-bold text-slate-700 tracking-wide">ALGORITMOS GENÉTICOS</span>
          <RestricoesInfo />
        </div>

        <div className="p-3 flex flex-col gap-3">

          {/* Parâmetros numéricos */}
          <div className="grid grid-cols-3 gap-2">
            <NumberInput
              label="Épocas" field="epocas" form={form} onChange={handleChange} min={1} max={100000} placeholder="100"
              hint="Número de gerações que o algoritmo vai evoluir. Mais épocas tendem a melhorar a rota, mas o ganho costuma estagnar depois de um certo ponto (especialmente com o 2-opt ativado) — épocas extras além da convergência só consomem tempo à toa."
            />
            <NumberInput
              label="População" field="tamanho_populacao" form={form} onChange={handleChange} min={2} max={10000} placeholder="200"
              hint="Quantidade de rotas candidatas mantidas em cada geração. Populações maiores exploram mais alternativas e reduzem o risco de convergência prematura, mas deixam cada época mais lenta para processar."
            />
            <NumberInput
              label="Melhores" field="tamanho_elite" form={form} onChange={handleChange} min={1} max={9999} placeholder="20"
              hint="Quantos indivíduos são usados como pais da próxima geração (e, com elitismo ativo, preservados sem alteração). Um valor muito baixo reduz a diversidade genética e favorece a convergência prematura; um valor muito alto aproxima o comportamento de uma busca aleatória."
            />
          </div>

          {/* Restrição logística */}
          <NumberInput
            label="Capacidade do Veículo (kg)"
            field="capacidade_veiculo_kg"
            form={form}
            onChange={handleChange}
            min={0.1}
            max={100000}
            step={0.01}
            placeholder="Ex.: 50"
            required={false}
            hint="Capacidade máxima do veículo em kg. Se a carga total dos produtos passar desse valor, a rota continua sendo calculada, mas recebe uma penalidade na aptidão e o painel mostra o excesso."
          />

          {/* Grau de mutação */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label
                className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest cursor-help"
                title="Probabilidade de cada rota sofrer uma mutação aleatória a cada geração. Valores baixos preservam as boas soluções já encontradas; valores altos aumentam a exploração e ajudam a escapar de mínimos locais, mas atrapalham a convergência se forem altos demais."
              >
                Grau de Mutação
              </label>
              <span className="text-xs font-bold text-blue-600 tabular-nums">
                {parseFloat(form.grau_mutacao).toFixed(1)}%
              </span>
            </div>
            <input
              type="range" min={0} max={10} step={0.1}
              value={form.grau_mutacao}
              onChange={e => handleChange('grau_mutacao', e.target.value)}
              title="Probabilidade de mutação a cada geração. Baixo = preserva boas soluções; alto = mais exploração, mas pode atrapalhar a convergência."
              className="w-full h-1.5 accent-blue-600 cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-slate-300 mt-0.5">
              <span>0%</span><span>5%</span><span>10%</span>
            </div>
          </div>

          {/* Divisor — Operadores */}
          <div className="flex items-center gap-2 pt-1">
            <div className="flex-1 h-px bg-slate-100" />
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Operadores</span>
            <div className="flex-1 h-px bg-slate-100" />
          </div>

          {/* Seleção + Crossover em 2 colunas */}
          <div className="grid grid-cols-2 gap-2">
            <PillRadio
              label="Seleção"
              field="tipo_selecao"
              form={form}
              onChange={handleChange}
              options={[
                {
                  value: 'truncamento', label: 'Truncamento', badge: true,
                  desc: 'Seleciona sempre os N indivíduos com menor distância da população atual. Convergência rápida e previsível, mas mais suscetível a ficar preso em ótimos locais por perder diversidade genética rapidamente.',
                },
                {
                  value: 'torneio', label: 'Torneio',
                  desc: 'Sorteia pequenos grupos aleatórios e escolhe o melhor de cada grupo. Dá chance a soluções medianas de serem escolhidas, mantendo mais diversidade genética — mas a evolução fica mais lenta e menos previsível.',
                },
              ]}
            />
            <PillRadio
              label="Crossover"
              field="tipo_crossover"
              form={form}
              onChange={handleChange}
              options={[
                {
                  value: 'ox', label: 'OX', badge: true,
                  desc: 'Order Crossover: preserva a ordem relativa das cidades de um pai e completa com a ordem do outro. Bom equilíbrio entre manter boas sub-rotas e gerar diversidade — o operador clássico para o TSP.',
                },
                {
                  value: 'erx', label: 'ERX',
                  desc: 'Edge Recombination: reconstrói o filho priorizando reaproveitar as conexões entre cidades já presentes em ambos os pais. Tende a produzir rotas melhores que o OX para o TSP puro, ao custo de mais processamento.',
                },
              ]}
            />
          </div>

          {/* Inicialização */}
          <PillRadio
            label="Inicialização da População"
            field="tipo_inicializacao"
            form={form}
            onChange={handleChange}
            options={[
              {
                value: 'aleatoria', label: 'Aleatória', badge: true,
                desc: 'Todas as rotas da população inicial são embaralhadas aleatoriamente. Garante diversidade máxima no início, mas a rota de partida costuma ser ineficiente, exigindo mais épocas até melhorar.',
              },
              {
                value: 'vizinho_mais_proximo', label: 'Vizinho mais próximo',
                desc: 'Inclui uma rota inicial construída pela heurística gulosa do vizinho mais próximo. Acelera a convergência ao já começar de uma solução razoável, mas reduz um pouco a diversidade genética inicial.',
              },
            ]}
          />

          {/* Mutação — 4 opções */}
          <MutacaoCards form={form} onChange={handleChange} />

          {/* 2-opt */}
          <Toggle
            label="Busca local 2-opt"
            desc="Testa inversões de arestas para reduzir a distância total."
            hint="Depois de cada cruzamento/mutação, testa todos os pares de arestas da rota e desfaz cruzamentos que aumentam a distância. Costuma melhorar muito a qualidade da rota final — para poucas cidades pode até convergir para a rota ótima em poucas épocas — mas o custo cresce rapidamente com o número de cidades."
            warn="Custo computacional alto (cresce com o quadrado do nº de cidades). Reduza épocas e população ao ativar — a convergência costuma ser bem mais rápida com esse operador ligado."
            field="usar_2opt"
            form={form}
            onChange={handleChange}
          />

          {/* Divisor — Elitismo */}
          <div className="flex items-center gap-2">
            <div className="flex-1 h-px bg-slate-100" />
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Elitismo</span>
            <div className="flex-1 h-px bg-slate-100" />
          </div>

          {/* Método de otimização */}
          <div className="grid grid-cols-2 gap-2">
            {[
              {
                isElitismo: true, label: 'Usar Elitismo', badge: 'Recomendado',
                desc: 'Preserva os melhores entre gerações.',
                hint: 'Garante que os melhores indivíduos de cada geração nunca sejam perdidos, preservando-os inalterados na próxima. A aptidão da melhor rota encontrada nunca piora ao longo da execução — recomendado na maioria dos casos.',
              },
              {
                isElitismo: false, label: 'Apenas Aleatório',
                desc: 'Sem preservação entre gerações.',
                hint: 'Nenhum indivíduo é preservado entre gerações — mesmo a melhor rota encontrada pode ser descartada na geração seguinte. Aumenta a exploração/diversidade, mas a qualidade da rota pode oscilar (e até piorar) entre épocas.',
              },
            ].map(opt => {
              const selected = opt.isElitismo ? form.elitismo === 1 : form.elitismo === 0
              return (
                <button
                  key={String(opt.isElitismo)}
                  type="button"
                  onClick={() => handleMethodChange(opt.isElitismo)}
                  title={opt.hint}
                  className={`text-left p-2.5 rounded-xl border-2 transition-all ${selected ? 'border-blue-500 bg-blue-50' : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                >
                  <div className="flex items-start gap-1.5 mb-1">
                    <div className={`w-3 h-3 rounded-full border-2 flex-shrink-0 mt-0.5 transition-colors ${selected ? 'border-blue-500 bg-blue-500' : 'border-slate-300'
                      }`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1 flex-wrap">
                        <span className="text-[11px] font-semibold text-slate-700 leading-tight">{opt.label}</span>
                        {opt.badge && (
                          <span className="text-[9px] bg-emerald-100 text-emerald-700 px-1 py-0.5 rounded font-semibold">
                            {opt.badge}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <p className="text-[10px] text-slate-400 leading-relaxed pl-4">{opt.desc}</p>
                </button>
              )
            })}
          </div>

          {/* Parada antecipada — só disponível com elitismo ativado */}
          <Toggle
            label="Parada Antecipada (apenas com Elitismo ativado)"
            desc="Encerra o algoritmo se a aptidão não melhorar por várias épocas seguidas."
            hint="Interrompe a execução antes de completar todas as épocas configuradas se a aptidão não melhorar por várias gerações seguidas, economizando tempo de processamento quando o algoritmo já convergiu."
            disabledReason="Disponível apenas com Elitismo ativado (depende da garantia de que a aptidão nunca piora)."
            field="usar_parada_antecipada"
            form={form}
            onChange={handleChange}
            disabled={form.elitismo !== 1}
          />
          {form.elitismo === 1 && form.usar_parada_antecipada === 1 && (
            <NumberInput
              label="Paciência (épocas sem melhora)"
              field="paciencia_parada_antecipada"
              form={form}
              onChange={handleChange}
              min={1}
              max={100000}
              placeholder="30"
              hint="Número de épocas consecutivas sem qualquer melhora na aptidão que o algoritmo tolera antes de encerrar. Valores baixos economizam mais tempo, mas arriscam parar antes de escapar de um platô temporário; valores altos dão mais chances de melhora, mas encerram mais tarde."
            />
          )}

        </div>
      </div>

      {/* Erro */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 flex items-start gap-2">
          <svg className="text-red-500 flex-shrink-0 mt-0.5" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <p className="text-sm text-red-700 leading-snug">{error}</p>
        </div>
      )}

      {/* Botões */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleClear}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-2 border border-slate-200 rounded-xl text-sm text-slate-500 hover:bg-slate-50 hover:text-slate-700 transition-colors disabled:opacity-40"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
          </svg>
          Limpar
        </button>
        <button
          type="submit"
          disabled={loading || Boolean(mensagemErro)}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold text-sm rounded-xl transition-colors shadow-md shadow-blue-200"
        >
          {loading ? (
            <>
              <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Calculando...
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="3 11 22 2 13 21 11 13 3 11" />
              </svg>
              Gerar Rota
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </>
          )}
        </button>
      </div>

    </form>
  )
}
