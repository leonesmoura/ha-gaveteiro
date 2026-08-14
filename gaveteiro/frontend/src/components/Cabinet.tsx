import type { Drawer, Module } from '../types'

interface Props {
  modules: Module[]
  drawers: Drawer[]
  selectedId: number | null
  /** Ids destacados pela busca. null = sem busca ativa. */
  matchIds: Set<number> | null
  onSelect: (drawer: Drawer) => void
  /** No modo configuração as gavetas não abrem; os módulos é que se movem. */
  editing?: boolean
  onMoveModule?: (moduleId: number, dCol: number, dRow: number) => void
  onRenameModule?: (moduleId: number, name: string) => void
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
  onSelect,
  editing = false,
  onMoveModule,
  onRenameModule,
}: Props) {
  const cols = Math.max(...modules.map((m) => m.grid_col), 1)
  const rows = Math.max(...modules.map((m) => m.grid_row), 1)

  const byModule = new Map<number, Drawer[]>()
  for (const drawer of drawers) {
    const list = byModule.get(drawer.module_id) ?? []
    list.push(drawer)
    byModule.set(drawer.module_id, list)
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
            />
          ) : (
            <div className="module-name">{module.name}</div>
          )}
          <div
            className="module-grid"
            style={{ gridTemplateColumns: `repeat(${module.cols}, var(--drawer-w))` }}
          >
            {(byModule.get(module.id) ?? [])
              .slice()
              .sort((a, b) => a.row - b.row || a.col - b.col)
              .map((drawer) => (
                <DrawerCell
                  key={drawer.id}
                  drawer={drawer}
                  selected={drawer.id === selectedId}
                  match={matchIds?.has(drawer.id) ?? null}
                  onSelect={onSelect}
                />
              ))}
          </div>
        </div>
      ))}
    </div>
  )
}

/** Cabeçalho do módulo no modo configuração: renomear e mover pelo arranjo. */
function ModuleEditor({
  module,
  onMove,
  onRename,
}: {
  module: Module
  onMove: (dCol: number, dRow: number) => void
  onRename: (name: string) => void
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
      <div className="module-pos">
        col {module.grid_col} · lin {module.grid_row}
      </div>
    </div>
  )
}

function DrawerCell({
  drawer,
  selected,
  match,
  onSelect,
}: {
  drawer: Drawer
  selected: boolean
  /** true = bate com a busca, false = não bate, null = sem busca */
  match: boolean | null
  onSelect: (drawer: Drawer) => void
}) {
  const classes = ['drawer']
  if (drawer.part_count === 0) classes.push('empty')
  if (selected) classes.push('selected')
  if (match === true) classes.push('match')
  if (match === false) classes.push('dimmed')

  return (
    <button
      type="button"
      className={classes.join(' ')}
      onClick={() => onSelect(drawer)}
      title={`${drawer.label} — ${drawer.part_count === 0 ? 'vazia' : `${drawer.part_count} peça(s), ${drawer.total_quantity} un.`}`}
      aria-label={`Gaveta ${drawer.label}`}
    >
      {drawer.primary_color && (
        <span className="stripe" style={{ background: drawer.primary_color }} />
      )}
      {drawer.low_stock && <span className="low-dot" aria-hidden="true" />}
      <span className="qty">{drawer.part_count === 0 ? '·' : drawer.total_quantity}</span>
      <span className="name">{drawer.label}</span>
    </button>
  )
}
