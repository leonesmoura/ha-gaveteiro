import { imageUrl } from '../api'
import type { Part } from '../types'

interface Props {
  title: string
  parts: Part[]
  emptyMessage: string
  /** Clicar num resultado leva para a gaveta onde a peça está. */
  onGoToDrawer: (label: string) => void
}

export function PartList({ title, parts, emptyMessage, onGoToDrawer }: Props) {
  return (
    <div>
      <div className="panel-header">
        <h2>{title}</h2>
        <span className="muted">{parts.length} resultado(s)</span>
      </div>

      {parts.length === 0 && <div className="empty-state">{emptyMessage}</div>}

      {parts.map((part) => (
        <div className="card" key={part.id}>
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
                {[part.value, part.package].filter(Boolean).join(' · ') || '—'} ·{' '}
                {part.total_quantity} un.
              </div>
              {part.low_stock && (
                <div className="badge-low">Abaixo do mínimo ({part.min_qty})</div>
              )}
              <div className="row" style={{ flexWrap: 'wrap', marginTop: 6 }}>
                {part.drawer_labels.length === 0 ? (
                  <span className="muted">Sem gaveta atribuída</span>
                ) : (
                  part.drawer_labels.map((label) => (
                    <button key={label} onClick={() => onGoToDrawer(label)}>
                      {label}
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
