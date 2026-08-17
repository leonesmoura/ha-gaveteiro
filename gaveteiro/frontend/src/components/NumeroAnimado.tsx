import { useEffect, useRef, useState } from 'react'

/**
 * Conta até o novo valor em vez de trocar de uma vez, e marca a direção da
 * mudança com cor — dá para ver que o ajuste foi registrado sem olhar o
 * histórico.
 */
export function NumeroAnimado({ valor, duracao = 350 }: { valor: number; duracao?: number }) {
  const [exibido, setExibido] = useState(valor)
  const [direcao, setDirecao] = useState<'sobe' | 'desce' | null>(null)
  const anterior = useRef(valor)

  useEffect(() => {
    const inicio = anterior.current
    if (inicio === valor) return

    setDirecao(valor > inicio ? 'sobe' : 'desce')
    anterior.current = valor

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setExibido(valor)
      const limpar = setTimeout(() => setDirecao(null), duracao)
      return () => clearTimeout(limpar)
    }

    let frame = 0
    const t0 = performance.now()
    const passo = (agora: number) => {
      const progresso = Math.min(1, (agora - t0) / duracao)
      // easeOutCubic: rápido no começo, assenta no fim.
      const suave = 1 - Math.pow(1 - progresso, 3)
      setExibido(Math.round(inicio + (valor - inicio) * suave))
      if (progresso < 1) frame = requestAnimationFrame(passo)
    }
    frame = requestAnimationFrame(passo)

    // requestAnimationFrame não roda em aba de fundo. Sem esta garantia o
    // número ficaria parado no valor antigo — errado, não só sem animação.
    const garantia = setTimeout(() => {
      setExibido(valor)
      setDirecao(null)
    }, duracao + 60)

    return () => {
      cancelAnimationFrame(frame)
      clearTimeout(garantia)
    }
  }, [valor, duracao])

  return <span className={`numero${direcao ? ` ${direcao}` : ''}`}>{exibido}</span>
}
