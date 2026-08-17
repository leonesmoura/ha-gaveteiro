import { useMemo, useState } from 'react'

import { api } from '../api'
import type { Drawer, Module, RenumberInput } from '../types'

interface Props {
  modules: Module[]
  drawers: Drawer[]
  onChanged: () => void
}

/**
 * Configuração da numeração das gavetas. Mostra uma prévia calculada no
 * cliente com a mesma regra do backend, para o usuário conferir antes de
 * aplicar — renumerar mexe em todos os rótulos de uma vez.
 */
export function NumberingPanel({ modules, drawers, onChanged }: Props) {
  const [form, setForm] = useState<RenumberInput>({
    modo: 'pares',
    inicio: 1,
    ordem: 'linha',
    prefixo: '',
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState('')

  const preview = useMemo(() => previewLabels(modules, form), [modules, form])

  const aplicar = async () => {
    setBusy(true)
    setError('')
    setDone('')
    try {
      await api.renumber(form)
      onChanged()
      setDone('Numeração aplicada.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao renumerar')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack">
      <p className="muted">
        Renumerar troca o rótulo de todas as {drawers.length} gavetas. O conteúdo não se move.
      </p>

      <div className="field">
        <label htmlFor="modo">Como contar</label>
        <select
          id="modo"
          value={form.modo}
          onChange={(e) => setForm({ ...form, modo: e.target.value as RenumberInput['modo'] })}
        >
          <option value="pares">Aos pares (M1/M2 = 1-32, M3/M4 = 33-64…)</option>
          <option value="por_modulo">Bloco por módulo (M1 = 1-16, M2 = 17-32…)</option>
          <option value="continuo">Contínuo pela linha física do gaveteiro</option>
        </select>
      </div>

      <div className="field">
        <label htmlFor="ordem">Direção dentro do módulo</label>
        <select
          id="ordem"
          value={form.ordem}
          onChange={(e) => setForm({ ...form, ordem: e.target.value as RenumberInput['ordem'] })}
        >
          <option value="linha">Esquerda → direita, de cima para baixo</option>
          <option value="coluna">De cima para baixo, coluna por coluna</option>
        </select>
      </div>

      <div className="row">
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="inicio">Começa em</label>
          <input
            id="inicio"
            type="number"
            value={form.inicio}
            onChange={(e) => setForm({ ...form, inicio: Number(e.target.value) || 0 })}
          />
        </div>
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="prefixo">Prefixo (opcional)</label>
          <input
            id="prefixo"
            value={form.prefixo}
            placeholder="ex.: G"
            onChange={(e) => setForm({ ...form, prefixo: e.target.value })}
          />
        </div>
      </div>

      <div className="card">
        <div className="muted" style={{ marginBottom: 6 }}>
          Prévia dos dois primeiros módulos
        </div>
        <pre className="preview">{preview}</pre>
      </div>

      {error && <div className="error">{error}</div>}
      {done && <div className="ok-msg">{done}</div>}

      <button className="primary" onClick={aplicar} disabled={busy}>
        {busy ? 'Aplicando…' : 'Aplicar numeração'}
      </button>
    </div>
  )
}

/** Espelha a regra do backend (app/seed.py: numerar) para a prévia. */
function previewLabels(modules: Module[], form: RenumberInput): string {
  if (modules.length === 0) return ''

  const labels = new Map<string, string>()
  let numero = form.inicio
  const marcar = (moduleId: number, row: number, col: number) => {
    labels.set(`${moduleId}:${row}:${col}`, `${form.prefixo}${numero}`)
    numero += 1
  }

  const porPosicao = [...modules].sort((a, b) => a.grid_row - b.grid_row || a.grid_col - b.grid_col)
  // Blocos seguem o número do módulo (M1, M2, … M12), não a posição.
  const porNumero = [...modules].sort((a, b) => numeroDoModulo(a.name) - numeroDoModulo(b.name))

  if (form.modo === 'por_modulo') {
    for (const m of porNumero) percorrer(m, form.ordem, (row, col) => marcar(m.id, row, col))
  } else if (form.modo === 'pares') {
    for (let i = 0; i < porNumero.length; i += 2) {
      const par = porNumero.slice(i, i + 2)
      if (form.ordem === 'coluna') {
        for (const m of par)
          for (let col = 1; col <= m.cols; col++)
            for (let row = 1; row <= m.rows; row++) marcar(m.id, row, col)
      } else {
        for (let row = 1; row <= par[0].rows; row++)
          for (const m of par) for (let col = 1; col <= m.cols; col++) marcar(m.id, row, col)
      }
    }
  } else {
    for (const grid_row of [...new Set(porPosicao.map((m) => m.grid_row))]) {
      const naLinha = porPosicao.filter((m) => m.grid_row === grid_row)
      if (form.ordem === 'coluna') {
        for (const m of naLinha)
          for (let col = 1; col <= m.cols; col++)
            for (let row = 1; row <= m.rows; row++) marcar(m.id, row, col)
      } else {
        for (let row = 1; row <= naLinha[0].rows; row++)
          for (const m of naLinha) for (let col = 1; col <= m.cols; col++) marcar(m.id, row, col)
      }
    }
  }

  return (form.modo === 'continuo' ? porPosicao : porNumero)
    .slice(0, 2)
    .map((m) => {
      const linhas: string[] = []
      for (let row = 1; row <= m.rows; row++) {
        const celulas: string[] = []
        for (let col = 1; col <= m.cols; col++) {
          celulas.push((labels.get(`${m.id}:${row}:${col}`) ?? '').padStart(4))
        }
        linhas.push(celulas.join(' '))
      }
      return `${m.name}\n${linhas.join('\n')}`
    })
    .join('\n\n')
}

/** M9 antes de M10: ordem natural, não alfabética. */
function numeroDoModulo(name: string): number {
  const digitos = name.replace(/\D/g, '')
  return digitos ? Number(digitos) : Number.MAX_SAFE_INTEGER
}

function percorrer(module: Module, ordem: string, visit: (row: number, col: number) => void) {
  if (ordem === 'coluna') {
    for (let col = 1; col <= module.cols; col++)
      for (let row = 1; row <= module.rows; row++) visit(row, col)
  } else {
    for (let row = 1; row <= module.rows; row++)
      for (let col = 1; col <= module.cols; col++) visit(row, col)
  }
}
