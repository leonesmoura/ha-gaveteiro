# Gaveteiro

Controle de estoque de componentes eletrônicos com gaveteiro interativo:
192 gavetas (12 módulos de 4x4), busca, fotos, estoque mínimo e histórico.

Roda como **add-on do Home Assistant**, acessível de dois jeitos:

- pela barra lateral do HA (Ingress, já autenticado pelo HA);
- direto pela rede em `http://IP-DO-HAOS:8099`, com usuário e senha próprios.

---

## Instalação no HAOS

1. Instale o add-on **Samba share** ou **Terminal & SSH** para conseguir copiar arquivos.
2. Copie a pasta deste projeto para `/addons/gaveteiro` no HAOS
   (pelo Samba, é o compartilhamento `addons`).
3. No HA: **Settings → Add-ons → Add-on Store → ⋮ → Check for updates**.
4. O card **Gaveteiro** aparece em "Local add-ons". Abra e clique em **Install**
   (a primeira build leva alguns minutos).
5. Na aba **Configuration**, defina `username` e `password`. Troque a senha padrão.
6. **Start**, e ligue **Show in sidebar**.

### Inspecionar o banco na mão

O banco fica em `/share/gaveteiro/gaveteiro.db`. Instale o add-on comunitário
**SQLite Web** e aponte para esse caminho — dá para navegar tabelas, rodar query,
editar linha e exportar (é o equivalente do phpMyAdmin para SQLite; phpMyAdmin em
si só fala MySQL/MariaDB).

### Backup

`/data` (imagens) e `/share` (banco) entram no backup do Home Assistant.

---

## Desenvolvimento local (Windows)

```bash
cd gaveteiro/backend && python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt
```

Backend:

```bash
cd gaveteiro/backend && .venv/Scripts/python -m uvicorn app.main:app --reload --port 8099
```

Frontend (proxy para o backend acima):

```bash
cd gaveteiro/frontend && npm install && npm run dev
```

Credenciais padrão em dev: `admin` / `gaveteiro` (só valem fora do add-on).

Testes:

```bash
cd gaveteiro/backend && .venv/Scripts/python -m pytest
```

Build do frontend para dentro do backend (é o que o `Dockerfile` faz sozinho):

```bash
cd gaveteiro/frontend && npm run build
```

---

## Como está organizado

| Caminho | O que é |
|---|---|
| `backend/app/models.py` | Tabelas: módulos, gavetas, peças, estoque, movimentos |
| `backend/app/seed.py` | Cria os 12 módulos e as 192 gavetas no arranjo físico atual |
| `backend/app/routers/` | API REST (`/api/...`) |
| `backend/app/auth.py` | Login próprio + liberação de requisições vindas do Ingress |
| `frontend/src/components/Cabinet.tsx` | O gaveteiro interativo |
| `frontend/src/components/DrawerPanel.tsx` | Painel da gaveta: peças, quantidade, histórico |
| `config.yaml`, `Dockerfile`, `run.sh` | Empacotamento como add-on |

### Arranjo físico dos módulos

Como está hoje (editável em `seed.py`, e pela API `PATCH /api/modules/{id}`):

```
        M3   M4
        M5   M6
        M7   M8
        M9   M10
M1  M2  M11  M12
```

Cada módulo tem 16 gavetas (4x4), rotuladas `M3-A1` … `M3-D4`.

---

## Próximos passos possíveis

- Etiquetas com QR code por gaveta (abrir a gaveta no celular pela câmera)
- Importação de peças via CSV
- Upload de datasheet em PDF (hoje é só link)
