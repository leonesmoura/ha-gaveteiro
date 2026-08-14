import { useState } from 'react'

import { api } from '../api'
import type { Category, Part, PartInput } from '../types'

interface Props {
  categories: Category[]
  /** Peça existente para editar; ausente = cadastro novo. */
  part?: Part
  onSaved: (part: Part) => void
  onCancel: () => void
}

export function PartForm({ categories, part, onSaved, onCancel }: Props) {
  const [form, setForm] = useState<PartInput>({
    name: part?.name ?? '',
    description: part?.description ?? '',
    category_id: part?.category_id ?? null,
    package: part?.package ?? '',
    value: part?.value ?? '',
    manufacturer_code: part?.manufacturer_code ?? '',
    datasheet_url: part?.datasheet_url ?? '',
    min_qty: part?.min_qty ?? 0,
    notes: part?.notes ?? '',
  })
  const [file, setFile] = useState<File | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const set = <K extends keyof PartInput>(key: K, value: PartInput[K]) =>
    setForm((current) => ({ ...current, [key]: value }))

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!form.name.trim()) {
      setError('O nome é obrigatório')
      return
    }
    setSaving(true)
    setError('')
    try {
      let saved = part ? await api.updatePart(part.id, form) : await api.createPart(form)
      if (file) saved = await api.uploadImage(saved.id, file)
      onSaved(saved)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="stack" onSubmit={submit}>
      <div className="field">
        <label htmlFor="part-name">Nome</label>
        <input
          id="part-name"
          value={form.name}
          onChange={(e) => set('name', e.target.value)}
          placeholder="Resistor 10k"
          autoFocus
        />
      </div>

      <div className="row">
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="part-value">Valor</label>
          <input
            id="part-value"
            value={form.value}
            onChange={(e) => set('value', e.target.value)}
            placeholder="10k"
          />
        </div>
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="part-package">Encapsulamento</label>
          <input
            id="part-package"
            value={form.package}
            onChange={(e) => set('package', e.target.value)}
            placeholder="0805"
          />
        </div>
      </div>

      <div className="row">
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="part-category">Categoria</label>
          <select
            id="part-category"
            value={form.category_id ?? ''}
            onChange={(e) => set('category_id', e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">—</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field" style={{ width: 120 }}>
          <label htmlFor="part-min">Estoque mín.</label>
          <input
            id="part-min"
            type="number"
            min={0}
            value={form.min_qty}
            onChange={(e) => set('min_qty', Number(e.target.value))}
          />
        </div>
      </div>

      <div className="field">
        <label htmlFor="part-code">Código do fabricante</label>
        <input
          id="part-code"
          value={form.manufacturer_code}
          onChange={(e) => set('manufacturer_code', e.target.value)}
          placeholder="RC0805FR-0710KL"
        />
      </div>

      <div className="field">
        <label htmlFor="part-datasheet">Datasheet (URL)</label>
        <input
          id="part-datasheet"
          value={form.datasheet_url}
          onChange={(e) => set('datasheet_url', e.target.value)}
          placeholder="https://..."
        />
      </div>

      <div className="field">
        <label htmlFor="part-notes">Observações</label>
        <textarea
          id="part-notes"
          rows={2}
          value={form.notes}
          onChange={(e) => set('notes', e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="part-image">Foto</label>
        <input
          id="part-image"
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </div>

      {error && <div className="error">{error}</div>}

      <div className="row">
        <button type="submit" className="primary" disabled={saving}>
          {saving ? 'Salvando…' : 'Salvar'}
        </button>
        <button type="button" onClick={onCancel} disabled={saving}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
