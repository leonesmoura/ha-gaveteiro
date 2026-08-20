import type {
  AuthStatus,
  Category,
  Drawer,
  DrawerDetail,
  Module,
  ModuleInput,
  ModuleLayoutItem,
  Movement,
  Part,
  PartInput,
  RenumberInput,
  SearchResult,
  StockEntry,
} from './types'

/**
 * O Ingress do Home Assistant serve o app sob /api/hassio_ingress/<token>/,
 * então a base da API é derivada do caminho atual, nunca fixada em '/api'.
 */
function apiBase(): string {
  const path = window.location.pathname
  const dir = path.endsWith('/') ? path : path.replace(/[^/]*$/, '')
  return `${dir}api`
}

export function imageUrl(filename: string): string {
  return `${apiBase()}/images/${filename}`
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    credentials: 'same-origin',
    ...init,
    headers:
      init?.body instanceof FormData
        ? init?.headers
        : { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })

  if (!response.ok) {
    let detail = response.statusText
    try {
      detail = (await response.json()).detail ?? detail
    } catch {
      /* resposta sem corpo JSON */
    }
    throw new ApiError(response.status, detail)
  }

  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}

const json = (body: unknown) => JSON.stringify(body)

export const api = {
  authStatus: () => request<AuthStatus>('/auth/status'),
  login: (username: string, password: string) =>
    request<AuthStatus>('/auth/login', { method: 'POST', body: json({ username, password }) }),
  logout: () => request<void>('/auth/logout', { method: 'POST' }),

  modules: () => request<Module[]>('/modules'),
  moveModule: (id: number, grid_col: number, grid_row: number) =>
    request<Module>(`/modules/${id}`, { method: 'PATCH', body: json({ grid_col, grid_row }) }),
  setLayout: (modules: ModuleLayoutItem[]) =>
    request<Module[]>('/modules/layout', { method: 'POST', body: json({ modules }) }),
  updateModule: (id: number, payload: Partial<ModuleInput>) =>
    request<Module>(`/modules/${id}`, { method: 'PATCH', body: json(payload) }),
  createModule: (payload: ModuleInput) =>
    request<Module>('/modules', { method: 'POST', body: json(payload) }),
  deleteModule: (id: number) => request<void>(`/modules/${id}`, { method: 'DELETE' }),
  setAppearance: (payload: { drawer_ratio?: number; drawer_scale?: number }) =>
    request<Module[]>('/modules/appearance', { method: 'POST', body: json(payload) }),

  drawers: () => request<Drawer[]>('/drawers'),
  drawer: (id: number) => request<DrawerDetail>(`/drawers/${id}`),
  renameDrawer: (id: number, label: string) =>
    request<Drawer>(`/drawers/${id}`, { method: 'PATCH', body: json({ label }) }),
  describeDrawer: (id: number, description: string) =>
    request<Drawer>(`/drawers/${id}`, { method: 'PATCH', body: json({ description }) }),
  uploadDrawerImage: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<Drawer>(`/drawers/${id}/image`, { method: 'POST', body: form })
  },
  deleteDrawerImage: (id: number) =>
    request<Drawer>(`/drawers/${id}/image`, { method: 'DELETE' }),
  renumber: (payload: RenumberInput) =>
    request<Drawer[]>('/drawers/renumber', { method: 'POST', body: json(payload) }),

  categories: () => request<Category[]>('/categories'),
  parts: () => request<Part[]>('/parts'),
  lowStock: () => request<Part[]>('/parts/low-stock'),
  createPart: (payload: PartInput) => request<Part>('/parts', { method: 'POST', body: json(payload) }),
  updatePart: (id: number, payload: Partial<PartInput>) =>
    request<Part>(`/parts/${id}`, { method: 'PATCH', body: json(payload) }),
  deletePart: (id: number) => request<void>(`/parts/${id}`, { method: 'DELETE' }),

  uploadImage: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<Part>(`/parts/${id}/image`, { method: 'POST', body: form })
  },

  assignPart: (drawerId: number, part_id: number, quantity: number) =>
    request<StockEntry[]>(`/drawers/${drawerId}/stock`, {
      method: 'POST',
      body: json({ part_id, quantity }),
    }),
  adjustStock: (
    drawerId: number,
    partId: number,
    payload: { delta?: number; set_to?: number; reason?: string },
  ) =>
    request<StockEntry[]>(`/drawers/${drawerId}/stock/${partId}`, {
      method: 'PATCH',
      body: json(payload),
    }),
  removeFromDrawer: (drawerId: number, partId: number) =>
    request<void>(`/drawers/${drawerId}/stock/${partId}`, { method: 'DELETE' }),

  movements: (params: { part_id?: number; drawer_id?: number; limit?: number } = {}) => {
    const query = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => [k, String(v)]),
    )
    return request<Movement[]>(`/movements?${query}`)
  },

  search: (q: string, categoryId?: number | null) => {
    const query = new URLSearchParams({ q })
    if (categoryId) query.set('category_id', String(categoryId))
    return request<SearchResult>(`/search?${query}`)
  },
}

export { ApiError }
