import type { CSSProperties } from 'react'

import { imageUrl } from '../api'
import type { Drawer, Module } from '../types'

interface Props {
  modules: Module[]
  drawers: Drawer[]
  selectedId: number | null
  /** Ids destacados pela busca. null = sem busca ativa. */
  matchIds: Set<number> | null
  /** Resultado da busca em foco no momento, para navegar entre eles. */
  focusedId?: number | null
  onSelect: (drawer: Drawer) => void
  /** Miniaturas ligadas/desligadas — preferência de quem está olhando. */
  showThumbs?: boolean
  /** No modo configuração as gavetas não abrem; os módulos é que se movem. */
  editing?: boolean
  onMoveModule?: (moduleId: number, dCol: number, dRow: number) => void
  onRenameModule?: (moduleId: number, name: string) => void
  /** Grade e aparência vão direto para a API: mexem em gavetas, não no rascunho. */
  onResizeModule?: (moduleId: number, campo: 'rows' | 'cols', valor: number) => void
  onStyleModule?: (moduleId: number, campo: 'drawer_ratio' | 'drawer_scale', valor: number) => void
  onDeleteModule?: (moduleId: number) => void
}

/**
 * Desenha o gaveteiro: cada módulo na sua posição do arranjo, cada gaveta
 * na sua posição dentro do módulo. Clicar numa gaveta abre o painel.
 */
export function Cabinet({
  modules,
  drawers,
  selectedId,
  matchIds,
  focusedId = null,
  onSelect,
  showThumbs = true,
  editing = false,
  onMoveModule,
  onRenameModule,
  onResizeModule,
  onStyleModule,
  onDeleteModule,
}: Props) {
  const cols = Math.max(...modules.map((m) => m.grid_col), 1)
  const rows = Math.max(...modules.map((m) => m.grid_row), 1)

  const byModule = new Map<number, Drawer[]>()
  for (const drawer of drawers) {
    const list = byModule.get(drawer.module_id) ?? []
    list.push(drawer)
    byModule.set(drawer.module_id, list)
  }

  // A barra de ocupação é relativa à gaveta mais cheia — não existe uma
  // capacidade real, então o que importa é a comparação entre gavetas.
  const maiorQuantidade = Math.max(1, ...drawers.map((d) => d.total_quantity))

  // Ordem do destaque da busca, para as gavetas pulsarem em sequência.
  const ordemMatch = new Map<number, number>()
  if (matchIds) {
    drawers
      .filter((d) => matchIds.has(d.id))
      .forEach((d, i) => ordemMatch.set(d.id, i))
  }

  return (
    <div
      className={`cabinet${editing ? ' editing' : ''}`}
      style={{
        gridTemplateColumns: `repeat(${cols}, max-content)`,
        gridTemplateRows: `repeat(${rows}, max-content)`,
      }}
    >
      {modules.map((module) => (
        <div
          key={module.id}
          className="module"
          style={{ gridColumn: module.grid_col, gridRow: module.grid_row }}
        >
          {editing ? (
            <ModuleEditor
              module={module}
              onMove={(dCol, dRow) => onMoveModule?.(module.id, dCol, dRow)}
              onRename={(name) => onRenameModule?.(module.id, name)}
              onResize={(campo, valor) => onResizeModule?.(module.id, campo, valor)}
              onStyle={(campo, valor) => onStyleModule?.(module.id, campo, valor)}
              onDelete={() => onDeleteModule?.(module.id)}
            />
          ) : (
            <div className="module-name">{module.name}</div>
          )}
          <div
            className="module-grid"
            style={
              {
                gridTemplateColumns: `repeat(${module.cols}, calc(var(--drawer-w) * ${module.drawer_scale}))`,
                '--ratio': module.drawer_ratio,
              } as CSSProperties
            }
          >
            {(byModule.get(module.id) ?? [])
              .slice()
              .sort((a, b) => a.row - b.row || a.col - b.col)
              .map((drawer) => (
                <DrawerCell
                  key={drawer.id}
                  drawer={drawer}
                  selected={drawer.id === selectedId}
                  focused={drawer.id === focusedId}
                  match={matchIds?.has(drawer.id) ?? null}
                  ordem={ordemMatch.get(drawer.id) ?? 0}
                  maiorQuantidade={maiorQuantidade}
                  showThumb={showThumbs}
                  onSelect={onSelect}
                />
              ))}
          </div>
        </div>
      ))}
    </div>
  )
}

/** Cabeçalho do módulo no modo configuração. */
function ModuleEditor({
  module,
  onMove,
  onRename,
  onResize,
  onStyle,
  onDelete,
}: {
  module: Module
  onMove: (dCol: number, dRow: number) => void
  onRename: (name: string) => void
  onResize: (campo: 'rows' | 'cols', valor: number) => void
  onStyle: (campo: 'drawer_ratio' | 'drawer_scale', valor: number) => void
  onDelete: () => void
}) {
  return (
    <div className="module-editor">
      <input
        value={module.name}
        onChange={(e) => onRename(e.target.value)}
        aria-label={`Nome do módulo ${module.name}`}
      />

      <div className="module-arrows">
        <button onClick={() => onMove(0, -1)} title="Mover para cima" aria-label="Mover para cima">
          ↑
        </button>
        <button onClick={() => onMove(-1, 0)} title="Mover para a esquerda" aria-label="Mover para a esquerda">
          ←
        </button>
        <button onClick={() => onMove(1, 0)} title="Mover para a direita" aria-label="Mover para a direita">
          →
        </button>
        <button onClick={() => onMove(0, 1)} title="Mover para baixo" aria-label="Mover para baixo">
          ↓
        </button>
      </div>

      {/* Grade: aplica na hora, porque cria ou remove gavetas de verdade. */}
      <div className="module-campo">
        <span>grade</span>
        <input
          type="number"
          min={1}
          value={module.rows}
          onChange={(e) => onResize('rows', Number(e.target.value))}
          aria-label={`Linhas do módulo ${module.name}`}
        />
        <span>×</span>
        <input
          type="number"
          min={1}
          value={module.cols}
          onChange={(e) => onResize('cols', Number(e.target.value))}
          aria-label={`Colunas do módulo ${module.name}`}
        />
      </div>

      <div className="module-campo">
        <span>gaveta</span>
        <input
          type="range"
          min={0.5}
          max={3}
          step={0.1}
          value={module.drawer_ratio}
          onChange={(e) => onStyle('drawer_ratio', Number(e.target.value))}
          title="Proporção largura/altura da gaveta"
          aria-label={`Proporção da gaveta do módulo ${module.name}`}
        />
      </div>

      <div className="module-campo">
        <span>escala</span>
        <input
          type="range"
          min={0.5}
          max={2.5}
          step={0.1}
          value={module.drawer_scale}
          onChange={(e) => onStyle('drawer_scale', Number(e.target.value))}
          title="Tamanho da gaveta em relação aos outros módulos"
          aria-label={`Escala da gaveta do módulo ${module.name}`}
        />
      </div>

      <div className="module-pos">
        col {module.grid_col} · lin {module.grid_row}
        <button className="link danger" onClick={onDelete} title="Apagar este módulo">
          apagar
        </button>
      </div>
    </div>
  )
}

function DrawerCell({
  drawer,
  selected,
  focused,
  match,
  ordem,
  maiorQuantidade,
  showThumb,
  onSelect,
}: {
  drawer: Drawer
  selected: boolean
  focused: boolean
  /** true = bate com a busca, false = não bate, null = sem busca */
  match: boolean | null
  ordem: number
  maiorQuantidade: number
  showThumb: boolean
  onSelect: (drawer: Drawer) => void
}) {
  const miniatura = showThumb ? drawer.image_path : null

  const classes = ['drawer']
  if (miniatura) classes.push('com-foto')
  if (drawer.part_count === 0) classes.push('empty')
  if (selected) classes.push('selected')
  if (focused) classes.push('atual')
  if (match === true) classes.push('match')
  if (match === false) classes.push('dimmed')

  // Raiz quadrada porque as quantidades variam muito (1 a centenas): sem
  // isso quase todas as barras ficariam invisíveis perto da maior.
  const ocupacao = drawer.total_quantity
    ? Math.max(0.12, Math.sqrt(drawer.total_quantity / maiorQuantidade))
    : 0

  return (
    <button
      type="button"
      className={classes.join(' ')}
      data-drawer={drawer.id}
      onClick={() => onSelect(drawer)}
      title={[
        drawer.label,
        drawer.description,
        drawer.part_count === 0
          ? 'vazia'
          : `${drawer.part_count} peça(s), ${drawer.total_quantity} un.`,
      ]
        .filter(Boolean)
        .join(' — ')}
      aria-label={`Gaveta ${drawer.label}${drawer.description ? `, ${drawer.description}` : ''}`}
      style={{ '--atraso': `${(ordem % 12) * 0.06}s` } as CSSProperties}
    >
      {drawer.primary_color && (
        <span className="stripe" style={{ background: drawer.primary_color }} />
      )}
      {drawer.low_stock && <span className="low-dot" aria-hidden="true" />}

      {miniatura && (
        <img className="thumb-gaveta" src={imageUrl(miniatura)} alt="" loading="lazy" />
      )}
      <span className="rotulo">{drawer.label}</span>
      {drawer.description && <span className="name">{drawer.description}</span>}
      {drawer.part_count > 0 && (
        <span className="qty">
          {drawer.part_count > 1 && `${drawer.part_count}× · `}
          {drawer.total_quantity}
        </span>
      )}

      {ocupacao > 0 && (
        <span
          className="fill"
          style={{
            transform: `scaleX(${ocupacao})`,
            background: drawer.primary_color ?? 'var(--accent)',
          }}
          aria-hidden="true"
        />
      )}
    </button>
  )
}
