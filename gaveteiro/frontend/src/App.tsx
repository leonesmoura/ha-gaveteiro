import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'

import { api } from './api'
import { Cabinet } from './components/Cabinet'
import { DrawerPanel } from './components/DrawerPanel'
import { Login } from './components/Login'
import { NumberingPanel } from './components/NumberingPanel'
import { PartList } from './components/SearchPanel'
import { observarTema } from './theme'
import type { Category, Drawer, Module, Part } from './types'

type PanelTab = 'drawer' | 'search' | 'low' | 'config'

export function App() {
  const [authed, setAuthed] = useState<boolean | null>(null)
  const [versao, setVersao] = useState('')
  const [modules, setModules] = useState<Module[]>([])
  const [drawers, setDrawers] = useState<Drawer[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [parts, setParts] = useState<Part[]>([])

  const [selected, setSelected] = useState<Drawer | null>(null)
  const [tab, setTab] = useState<PanelTab>('drawer')
  // No celular o painel vira uma folha sobre o gaveteiro; no desktop o CSS
  // ignora este estado e o painel fica sempre visível ao lado.
  const [panelOpen, setPanelOpen] = useState(false)

  const abrirPainel = (proximaAba: PanelTab) => {
    setTab(proximaAba)
    setPanelOpen(true)
  }

  // Modo configuração: mexe num rascunho local e só grava ao salvar, para
  // não deixar o arranjo meio aplicado se o usuário desistir no meio.
  const [rascunho, setRascunho] = useState<Module[] | null>(null)
  const editando = rascunho !== null

  const moverModulo = (moduleId: number, dCol: number, dRow: number) => {
    setRascunho((atual) => {
      if (!atual) return atual
      const alvo = atual.find((m) => m.id === moduleId)
      if (!alvo) return atual

      const col = alvo.grid_col + dCol
      const row = alvo.grid_row + dRow
      if (col < 1 || row < 1) return atual

      // Célula ocupada: troca os dois de lugar em vez de recusar o movimento.
      const ocupante = atual.find((m) => m.grid_col === col && m.grid_row === row)
      return atual.map((m) => {
        if (m.id === alvo.id) return { ...m, grid_col: col, grid_row: row }
        if (ocupante && m.id === ocupante.id)
          return { ...m, grid_col: alvo.grid_col, grid_row: alvo.grid_row }
        return m
      })
    })
  }

  // Grade e aparência mexem em gavetas reais, então vão direto para a API em
  // vez de esperar o "Salvar arranjo" — que só carrega posições e nomes.
  const ajustarModulo = async (
    moduleId: number,
    campo: 'rows' | 'cols' | 'drawer_ratio' | 'drawer_scale',
    valor: number,
  ) => {
    if (!Number.isFinite(valor) || valor < 0) return
    try {
      await api.updateModule(moduleId, { [campo]: valor })
      const frescos = await api.modules()
      setModules(frescos)
      // O rascunho carrega só posição e nome (as edições ainda não salvas).
      // Espalhar o rascunho inteiro por cima desfaria o que a API acabou de
      // gravar — grade, proporção e escala têm que vir do servidor.
      setRascunho((atual) => {
        if (!atual) return atual
        const local = new Map(atual.map((m) => [m.id, m]))
        return frescos.map((f) => {
          const r = local.get(f.id)
          return r ? { ...f, name: r.name, grid_col: r.grid_col, grid_row: r.grid_row } : f
        })
      })
      setDrawers(await api.drawers())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao ajustar o módulo')
    }
  }

  const apagarModulo = async (moduleId: number) => {
    const alvo = (rascunho ?? modules).find((m) => m.id === moduleId)
    if (!alvo) return
    if (!window.confirm(`Apagar o módulo ${alvo.name} e as gavetas dele?`)) return
    try {
      await api.deleteModule(moduleId)
      setRascunho((atual) => atual?.filter((m) => m.id !== moduleId) ?? atual)
      await loadAll()
      setToast('Módulo apagado')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao apagar o módulo')
    }
  }

  const novoModulo = async () => {
    const usadas = new Set((rascunho ?? modules).map((m) => `${m.grid_col}:${m.grid_row}`))
    let posicao = { grid_col: 1, grid_row: 1 }
    busca: for (let r = 1; r < 40; r++)
      for (let c = 1; c < 40; c++)
        if (!usadas.has(`${c}:${r}`)) {
          posicao = { grid_col: c, grid_row: r }
          break busca
        }

    const nome = window.prompt('Nome do novo módulo:', `M${(rascunho ?? modules).length + 1}`)
    if (!nome?.trim()) return
    try {
      await api.createModule({ name: nome.trim(), rows: 4, cols: 4, ...posicao })
      await loadAll()
      setRascunho(null)
      setToast('Módulo criado')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar o módulo')
    }
  }

  const salvarArranjo = async () => {
    if (!rascunho) return
    try {
      await api.setLayout(
        rascunho.map((m) => ({
          id: m.id,
          grid_col: m.grid_col,
          grid_row: m.grid_row,
          name: m.name,
        })),
      )
      setRascunho(null)
      await loadAll()
      setToast('Arranjo salvo')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao salvar o arranjo')
    }
  }

  // "Ver tudo": encolhe as gavetas até o gaveteiro inteiro caber na largura
  // disponível, para dar a visão geral sem rolagem horizontal.
  const [fit, setFit] = useState(false)
  const canvasRef = useRef<HTMLDivElement>(null)
  const scalerRef = useRef<HTMLDivElement>(null)

  useLayoutEffect(() => {
    const scaler = scalerRef.current
    const cabinet = scaler?.firstElementChild

    if (!fit) {
      if (cabinet instanceof HTMLElement) {
        cabinet.style.transform = ''
        cabinet.style.width = ''
      }
      if (scaler) {
        scaler.style.width = ''
        scaler.style.height = ''
      }
      return
    }

    const ajustar = () => {
      const wrap = canvasRef.current
      const scaler = scalerRef.current
      const cabinet = scaler?.firstElementChild
      if (!wrap || !scaler || !(cabinet instanceof HTMLElement)) return

      // Escala o gaveteiro inteiro em vez de encolher as colunas: assim o
      // texto reduz junto e as proporções físicas continuam corretas.
      cabinet.style.transform = ''
      cabinet.style.width = ''
      const natural = { w: cabinet.offsetWidth, h: cabinet.offsetHeight }
      const escala = Math.min(1, (wrap.clientWidth - 24) / natural.w)

      // Sem largura fixa, o wrapper encolhido reconstrange o grid e ele
      // reflui — a escala passaria a ser calculada sobre um tamanho errado.
      cabinet.style.width = `${natural.w}px`
      cabinet.style.transformOrigin = 'top left'
      cabinet.style.transform = `scale(${escala})`
      // O transform não afeta o layout, então o wrapper carrega o tamanho
      // final para o container não continuar rolando.
      scaler.style.width = `${natural.w * escala}px`
      scaler.style.height = `${natural.h * escala}px`
    }

    ajustar()
    window.addEventListener('resize', ajustar)
    return () => window.removeEventListener('resize', ajustar)
  }, [fit, modules, drawers])

  const [query, setQuery] = useState('')
  const [matchIds, setMatchIds] = useState<Set<number> | null>(null)
  const [results, setResults] = useState<Part[]>([])
  const [lowStock, setLowStock] = useState<Part[]>([])
  const [error, setError] = useState('')

  // Confirmação passageira das ações que não têm efeito visível imediato.
  const [toast, setToast] = useState('')
  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(''), 2200)
    return () => clearTimeout(timer)
  }, [toast])

  // Sob o Ingress herda o tema do HA; fora dele usa as cores próprias.
  useEffect(() => observarTema(), [])

  useEffect(() => {
    api
      .authStatus()
      .then((status) => {
        setAuthed(status.authenticated)
        setVersao(status.version)
      })
      .catch(() => setAuthed(false))
  }, [])

  const loadAll = useCallback(async () => {
    try {
      const [m, d, c, p, low] = await Promise.all([
        api.modules(),
        api.drawers(),
        api.categories(),
        api.parts(),
        api.lowStock(),
      ])
      setModules(m)
      setDrawers(d)
      setCategories(c)
      setParts(p)
      setLowStock(low)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    }
  }, [])

  useEffect(() => {
    if (authed) loadAll()
  }, [authed, loadAll])

  // Busca com debounce: digitar não dispara uma requisição por tecla.
  useEffect(() => {
    if (!authed) return
    const term = query.trim()
    if (!term) {
      setMatchIds(null)
      setResults([])
      return
    }
    const timer = setTimeout(() => {
      api
        .search(term)
        .then((result) => {
          setResults(result.parts)
          setMatchIds(new Set(result.drawer_ids))
          setTab('search')
          setPanelOpen(true)
        })
        .catch((err) => setError(err.message))
    }, 250)
    return () => clearTimeout(timer)
  }, [query, authed])

  const goToDrawerLabel = (label: string) => {
    const drawer = drawers.find((d) => d.label === label)
    if (drawer) {
      setSelected(drawer)
      abrirPainel('drawer')
    }
  }

  // Navegação entre os resultados da busca, para não caçar a gaveta no grid.
  const [indiceFoco, setIndiceFoco] = useState(0)

  const gavetasEncontradas = useMemo(
    () => (matchIds ? drawers.filter((d) => matchIds.has(d.id)) : []),
    [matchIds, drawers],
  )

  useEffect(() => setIndiceFoco(0), [matchIds])

  const irPara = (passo: number) => {
    if (gavetasEncontradas.length === 0) return
    const proximo =
      (indiceFoco + passo + gavetasEncontradas.length) % gavetasEncontradas.length
    setIndiceFoco(proximo)
    const alvo = gavetasEncontradas[proximo]
    setSelected(alvo)
    document
      .querySelector(`[data-drawer="${alvo.id}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' })
  }

  const totals = useMemo(
    () => ({
      ocupadas: drawers.filter((d) => d.part_count > 0).length,
      pecas: parts.length,
    }),
    [drawers, parts],
  )

  if (authed === null) return <div className="empty-state">Carregando…</div>
  if (!authed) return <Login onSuccess={() => setAuthed(true)} />

  return (
    <div className="app">
      <header className="topbar">
        <div className="titulo">
          <h1>Gaveteiro, Estoque</h1>
          {versao && <span className="versao">v{versao}</span>}
        </div>
        <span className="muted hide-mobile">
          {totals.ocupadas}/{drawers.length} gavetas · {totals.pecas} peças
        </span>
        <div className="grow">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar peça (nome, valor, encapsulamento, código)…"
            aria-label="Buscar peça"
          />
        </div>

        {matchIds && (
          <div className="busca-nav">
            <span className={gavetasEncontradas.length ? 'ok-msg' : 'muted'}>
              {gavetasEncontradas.length === 0
                ? 'nenhuma gaveta'
                : `${indiceFoco + 1} de ${gavetasEncontradas.length}`}
            </span>
            <button onClick={() => irPara(-1)} disabled={!gavetasEncontradas.length} aria-label="Resultado anterior">
              ‹
            </button>
            <button onClick={() => irPara(1)} disabled={!gavetasEncontradas.length} aria-label="Próximo resultado">
              ›
            </button>
            <button onClick={() => setQuery('')} aria-label="Limpar busca">
              ✕
            </button>
          </div>
        )}
        {lowStock.length > 0 && (
          <button className="danger" onClick={() => abrirPainel('low')}>
            {lowStock.length} p/ repor
          </button>
        )}
        <button onClick={() => setFit(!fit)} title="Ver o gaveteiro inteiro na tela">
          {fit ? 'Ampliar' : 'Ver tudo'}
        </button>
        <button onClick={() => abrirPainel('config')} title="Numeração das gavetas">
          Numeração
        </button>
        <button
          onClick={() => {
            setRascunho(modules.map((m) => ({ ...m })))
            setPanelOpen(false)
          }}
          title="Mover e renomear os módulos"
        >
          Configurar
        </button>
        <button
          className="hide-mobile"
          onClick={() =>
            api.logout().then(() => {
              setAuthed(false)
            })
          }
        >
          Sair
        </button>
      </header>

      {error && (
        <div className="error" style={{ padding: '6px 16px' }}>
          {error}
        </div>
      )}

      {editando && (
        <div className="config-bar">
          <span>
            Modo configuração — setas movem o módulo (célula ocupada troca de lugar).
            Grade, proporção e escala da gaveta são aplicadas na hora; posição e nome
            só ao salvar.
          </span>
          <div className="row">
            <button onClick={novoModulo}>+ Módulo</button>
            <button onClick={() => setRascunho(null)}>Cancelar</button>
            <button className="primary" onClick={salvarArranjo}>
              Salvar arranjo
            </button>
          </div>
        </div>
      )}

      <div className="main">
        <div className="canvas-wrap" ref={canvasRef}>
          <div ref={scalerRef}>
          <Cabinet
            modules={rascunho ?? modules}
            editing={editando}
            onMoveModule={moverModulo}
            onRenameModule={(id, name) =>
              setRascunho((atual) => atual?.map((m) => (m.id === id ? { ...m, name } : m)) ?? atual)
            }
            onResizeModule={ajustarModulo}
            onStyleModule={ajustarModulo}
            onDeleteModule={apagarModulo}
            drawers={drawers}
            selectedId={selected?.id ?? null}
            matchIds={matchIds}
            focusedId={gavetasEncontradas[indiceFoco]?.id ?? null}
            onSelect={(drawer) => {
              setSelected(drawer)
              abrirPainel('drawer')
            }}
          />
          </div>
        </div>

        <div
          className={`panel-backdrop${panelOpen ? ' open' : ''}`}
          onClick={() => setPanelOpen(false)}
          aria-hidden="true"
        />

        <aside className={`sidepanel${panelOpen ? ' open' : ''}`}>
          <button className="panel-close" onClick={() => setPanelOpen(false)}>
            ← Voltar ao gaveteiro
          </button>

          <div className="tabs">
            <button className={tab === 'drawer' ? 'active' : ''} onClick={() => setTab('drawer')}>
              Gaveta
            </button>
            <button className={tab === 'search' ? 'active' : ''} onClick={() => setTab('search')}>
              Busca
            </button>
            <button className={tab === 'low' ? 'active' : ''} onClick={() => setTab('low')}>
              Repor
            </button>
            <button className={tab === 'config' ? 'active' : ''} onClick={() => setTab('config')}>
              Nº
            </button>
          </div>

          <div className="painel-conteudo" key={`${tab}-${selected?.id ?? 0}`}>
          {tab === 'drawer' &&
            (selected ? (
              <DrawerPanel
                key={selected.id}
                drawerId={selected.id}
                categories={categories}
                allParts={parts}
                onChanged={loadAll}
              />
            ) : (
              <div className="empty-state">Clique numa gaveta para ver o conteúdo.</div>
            ))}

          {tab === 'search' && (
            <PartList
              title="Busca"
              parts={results}
              emptyMessage={query.trim() ? 'Nada encontrado.' : 'Digite algo para buscar.'}
              onGoToDrawer={goToDrawerLabel}
            />
          )}

          {tab === 'low' && (
            <PartList
              title="Repor"
              parts={lowStock}
              emptyMessage="Nenhuma peça abaixo do mínimo."
              onGoToDrawer={goToDrawerLabel}
            />
          )}

          {tab === 'config' && (
            <NumberingPanel
              modules={modules}
              drawers={drawers}
              onChanged={() => {
                loadAll()
                setToast('Numeração aplicada')
              }}
            />
          )}
          </div>
        </aside>
      </div>

      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
    </div>
  )
}
