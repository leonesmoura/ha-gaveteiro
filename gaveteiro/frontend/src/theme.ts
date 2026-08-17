/**
 * Integração com o tema do Home Assistant.
 *
 * Sob o Ingress o app roda num iframe da mesma origem do HA, então dá para ler
 * as variáveis de tema do documento pai e reaproveitá-las. Fora do HA (acesso
 * direto pela porta 8099) não há pai, e aí valem as cores próprias com
 * claro/escuro pela preferência do sistema.
 */

/** Nossa variável -> variáveis do HA, na ordem de preferência. */
const MAPA: Record<string, string[]> = {
  '--bg': ['--primary-background-color', '--lovelace-background'],
  '--surface': ['--card-background-color', '--ha-card-background'],
  '--surface-2': ['--secondary-background-color', '--table-row-alternative-background-color'],
  '--border': ['--divider-color'],
  '--text': ['--primary-text-color'],
  '--muted': ['--secondary-text-color'],
  '--accent': ['--primary-color'],
  '--danger': ['--error-color'],
  '--ok': ['--success-color'],
}

function documentoPai(): Document | null {
  try {
    // Origem diferente lança aqui; é o caso quando não estamos sob o Ingress.
    if (window.parent === window) return null
    return window.parent.document
  } catch {
    return null
  }
}

/**
 * Copia o tema do HA para as variáveis do app.
 * Devolve true se conseguiu — quem chama usa isso para decidir o fallback.
 */
export function aplicarTemaDoHomeAssistant(): boolean {
  const pai = documentoPai()
  if (!pai) return false

  const estilo = getComputedStyle(pai.documentElement)
  const raiz = document.documentElement
  let aplicadas = 0

  for (const [nossa, candidatas] of Object.entries(MAPA)) {
    for (const candidata of candidatas) {
      const valor = estilo.getPropertyValue(candidata).trim()
      if (valor) {
        raiz.style.setProperty(nossa, valor)
        aplicadas += 1
        break
      }
    }
  }

  if (aplicadas === 0) return false

  // O HA não tem equivalente para a sombra da gaveta; deriva do texto para
  // funcionar tanto em tema claro quanto escuro.
  const texto = estilo.getPropertyValue('--primary-text-color').trim()
  raiz.style.setProperty('--sombra', ehClaro(texto) ? 'rgba(0,0,0,.45)' : 'rgba(0,0,0,.18)')
  raiz.dataset.tema = 'home-assistant'
  return true
}

/** Luminância aproximada: decide se a cor do texto é clara (tema escuro). */
function ehClaro(cor: string): boolean {
  const nums = cor.match(/\d+/g)
  if (!nums || nums.length < 3) return cor.trim().toLowerCase() === '#fff'
  const [r, g, b] = nums.map(Number)
  return (r * 299 + g * 587 + b * 114) / 1000 > 128
}

/** Observa mudanças de tema no HA (o usuário pode trocar sem recarregar). */
export function observarTema(): () => void {
  if (!aplicarTemaDoHomeAssistant()) return () => {}

  const pai = documentoPai()
  if (!pai) return () => {}

  const observer = new MutationObserver(() => aplicarTemaDoHomeAssistant())
  observer.observe(pai.documentElement, { attributes: true, attributeFilter: ['style', 'class'] })
  return () => observer.disconnect()
}
