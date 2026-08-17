import { useEffect, useState } from 'react'

import { api, imageUrl } from '../api'
import type { Category, DrawerDetail, Movement, Part, StockEntry } from '../types'
import { NumeroAnimado } from './NumeroAnimado'
import { PartForm } from './PartForm'

interface Props {
  drawerId: number
  categories: Category[]
  allParts: Part[]
  /** Avisa o App para recarregar o grid quando as quantidades mudam. */
  onChanged: () => void
}

export function DrawerPanel({ drawerId, categories, allParts, onChanged }: Props) {
  const [detail, setDetail] = useState<DrawerDetail | null>(null)
  const [movements, setMovements] = useState<Movement[]>([])
  const [mode, setMode] = useState<'view' | 'new-part' | 'existing-part'>('view')
  const [renaming, setRenaming] = useState(false)
  const [novoRotulo, setNovoRotulo] = useState('')
  const [error, setError] = useState('')

  async function reload() {
    const [fresh, history] = await Promise.all([
      api.drawer(drawerId),
      api.movements({ drawer_id: drawerId, limit: 15 }),
    ])
    setDetail(fresh)
    setMovements(history)
  }

  useEffect(() => {
    setMode('view')
    setRenaming(false)
    setError('')
    reload().catch((err) => setError(err.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drawerId])

  async function run(action: () => Promise<unknown>) {
    setError('')
    try {
      await action()
      await reload()
      onChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro')
    }
  }

  if (!detail) return <div className="empty-state">Carregando…</div>

  return (
    <div>
      <div className="panel-header">
        {renaming ? (
          <form
            className="row"
            style={{ flex: 1 }}
            onSubmit={(e) => {
              e.preventDefault()
              const label = novoRotulo.trim()
              if (!label || label === detail.label) return setRenaming(false)
              run(() => api.renameDrawer(drawerId, label)).then(() => setRenaming(false))
            }}
          >
            <input
              value={novoRotulo}
              onChange={(e) => setNovoRotulo(e.target.value)}
              aria-label="Rótulo da gaveta"
              autoFocus
            />
            <button className="primary" type="submit">
              OK
            </button>
            <button type="button" onClick={() => setRenaming(false)}>
              Cancelar
            </button>
          </form>
        ) : (
          <>
            <h2>
              {detail.label}{' '}
              <button
                className="link"
                onClick={() => {
                  setNovoRotulo(detail.label)
                  setRenaming(true)
                }}
                title="Renomear esta gaveta"
              >
                renomear
              </button>
            </h2>
            <span className="muted">
              {detail.part_count === 0
                ? 'vazia'
                : `${detail.part_count} peça(s) · `}
            {detail.part_count > 0 && (
              <>
                <NumeroAnimado valor={detail.total_quantity} /> un.
              </>
            )}
            </span>
          </>
        )}
      </div>

      {!renaming && (
        <input
          className="drawer-description"
          defaultValue={detail.description}
          placeholder="Para que serve esta gaveta? (ex.: Cap. Poliester)"
          aria-label="Descrição da gaveta"
          onBlur={(e) => {
            const texto = e.target.value.trim()
            if (texto !== detail.description) run(() => api.describeDrawer(drawerId, texto))
          }}
        />
      )}

      {error && <div className="error">{error}</div>}

      {mode === 'view' && (
        <>
          {detail.entries.length === 0 && (
            <div className="empty-state">Nenhuma peça aqui ainda.</div>
          )}

          {detail.entries.map((entry) => (
            <StockCard
              key={entry.part.id}
              entry={entry}
              onAdjust={(delta) => run(() => api.adjustStock(drawerId, entry.part.id, { delta }))}
              onSet={(setTo) => run(() => api.adjustStock(drawerId, entry.part.id, { set_to: setTo }))}
              onRemove={() => run(() => api.removeFromDrawer(drawerId, entry.part.id))}
            />
          ))}

          <div className="row" style={{ marginTop: 12 }}>
            <button className="primary" onClick={() => setMode('new-part')}>
              + Nova peça
            </button>
            <button onClick={() => setMode('existing-part')}>Peça existente</button>
          </div>

          <h3 style={{ fontSize: 14, marginTop: 20, marginBottom: 4 }}>Histórico</h3>
          {movements.length === 0 ? (
            <div className="muted">Sem movimentos.</div>
          ) : (
            movements.map((movement) => <MovementRow key={movement.id} movement={movement} />)
          )}
        </>
      )}

      {mode === 'new-part' && (
        <PartForm
          categories={categories}
          onCancel={() => setMode('view')}
          onSaved={(part) =>
            run(async () => {
              await api.assignPart(drawerId, part.id, 0)
              setMode('view')
            })
          }
        />
      )}

      {mode === 'existing-part' && (
        <ExistingPartPicker
          parts={allParts.filter((p) => !detail.entries.some((e) => e.part.id === p.id))}
          onCancel={() => setMode('view')}
          onPick={(partId, quantity) =>
            run(async () => {
              await api.assignPart(drawerId, partId, quantity)
              setMode('view')
            })
          }
        />
      )}
    </div>
  )
}

function StockCard({
  entry,
  onAdjust,
  onSet,
  onRemove,
}: {
  entry: StockEntry
  onAdjust: (delta: number) => void
  onSet: (setTo: number) => void
  onRemove: () => void
}) {
  const [draft, setDraft] = useState(String(entry.quantity))

  useEffect(() => setDraft(String(entry.quantity)), [entry.quantity])

  const commit = () => {
    const parsed = Number(draft)
    if (Number.isFinite(parsed) && parsed >= 0 && parsed !== entry.quantity) onSet(parsed)
    else setDraft(String(entry.quantity))
  }

  const { part } = entry
  const low = part.min_qty > 0 && entry.quantity < part.min_qty

  return (
    <div className="card">
      <div className="entry">
        {part.image_path ? (
          <img className="thumb" src={imageUrl(part.image_path)} alt={part.name} />
        ) : (
          <div className="thumb placeholder">◧</div>
        )}
        <div className="entry-body">
          <div className="entry-title">
            <span>{part.name}</span>
            {part.category_name && (
              <span className="chip" style={{ borderColor: part.category_color ?? undefined }}>
                {part.category_name}
              </span>
            )}
          </div>
          <div className="muted">
            {[part.value, part.package, part.manufacturer_code].filter(Boolean).join(' · ') || '—'}
          </div>
          {low && <div className="badge-low">Abaixo do mínimo ({part.min_qty})</div>}
        </div>
      </div>

      <div className="qty-row">
        <button onClick={() => onAdjust(-10)} disabled={entry.quantity < 10}>
          −10
        </button>
        <button onClick={() => onAdjust(-1)} disabled={entry.quantity < 1}>
          −
        </button>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
          inputMode="numeric"
          aria-label={`Quantidade de ${part.name}`}
        />
        <button onClick={() => onAdjust(1)}>+</button>
        <button onClick={() => onAdjust(10)}>+10</button>
        <button className="danger" onClick={onRemove} title="Tirar da gaveta">
          ✕
        </button>
      </div>

      {part.datasheet_url && (
        <a className="muted" href={part.datasheet_url} target="_blank" rel="noreferrer">
          Datasheet ↗
        </a>
      )}
    </div>
  )
}

function ExistingPartPicker({
  parts,
  onPick,
  onCancel,
}: {
  parts: Part[]
  onPick: (partId: number, quantity: number) => void
  onCancel: () => void
}) {
  const [partId, setPartId] = useState<number | ''>('')
  const [quantity, setQuantity] = useState(0)

  return (
    <div className="stack">
      <div className="field">
        <label htmlFor="pick-part">Peça</label>
        <select
          id="pick-part"
          value={partId}
          onChange={(e) => setPartId(e.target.value ? Number(e.target.value) : '')}
        >
          <option value="">Selecione…</option>
          {parts.map((part) => (
            <option key={part.id} value={part.id}>
              {[part.name, part.value, part.package].filter(Boolean).join(' · ')}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="pick-qty">Quantidade</label>
        <input
          id="pick-qty"
          type="number"
          min={0}
          value={quantity}
          onChange={(e) => setQuantity(Number(e.target.value))}
        />
      </div>
      <div className="row">
        <button className="primary" disabled={partId === ''} onClick={() => onPick(Number(partId), quantity)}>
          Adicionar
        </button>
        <button onClick={onCancel}>Cancelar</button>
      </div>
    </div>
  )
}

function MovementRow({ movement }: { movement: Movement }) {
  const when = new Date(movement.created_at).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  return (
    <div className="movement">
      <span>
        <span className={movement.delta >= 0 ? 'delta-pos' : 'delta-neg'}>
          {movement.delta >= 0 ? '+' : ''}
          {movement.delta}
        </span>{' '}
        {movement.part_name}
        {movement.reason && <span className="muted"> · {movement.reason}</span>}
      </span>
      <span className="muted">{when}</span>
    </div>
  )
}
