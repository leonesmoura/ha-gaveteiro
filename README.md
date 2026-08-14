# Gaveteiro — Add-on para Home Assistant

Controle de estoque para gaveteiros de componentes eletrônicos, com gaveteiro
interativo, fotos, busca e histórico de movimentações.

![gavetas](https://img.shields.io/badge/gavetas-configur%C3%A1vel-blue)
![arch](https://img.shields.io/badge/arch-amd64%20%7C%20aarch64-lightgrey)

## Instalação

Este é um **repositório de add-ons do Home Assistant**, não um repositório HACS
— o HACS não distribui add-ons. A instalação é pelo Supervisor:

1. **Settings → Add-ons → Add-on Store**
2. Menu **⋮** (canto superior direito) → **Repositories**
3. Cole a URL deste repositório e clique em **Add**
4. Feche, atualize a página e procure por **Gaveteiro** na loja
5. **Install** → aguarde a build → **Start**

Antes de iniciar, defina usuário e senha na aba **Configuration**.

## O que ele faz

- **Gaveteiro interativo** — os módulos aparecem na mesma disposição física que
  você tem na parede ou na bancada. Clicar numa gaveta abre o conteúdo.
- **Estoque com histórico** — toda alteração de quantidade gera um registro,
  com motivo opcional.
- **Busca que aponta a gaveta** — procure por `10k`, `0805`, `NE555` e as
  gavetas correspondentes acendem no grid.
- **Estoque mínimo** — defina um mínimo por peça e veja a lista do que repor.
- **Fotos** — uma imagem por peça, redimensionada e convertida para WebP.
- **Layout configurável** — mova e renomeie módulos; renumere as gavetas com
  prévia antes de aplicar.

## Configuração

| Opção | Padrão | Descrição |
|---|---|---|
| `username` | `admin` | Usuário do acesso pela porta direta |
| `password` | `troque-esta-senha` | Senha — **troque antes de expor na rede** |
| `image_max_size` | `800` | Lado maior das fotos salvas, em pixels |

O acesso pela **sidebar do Home Assistant** (Ingress) usa a autenticação do
próprio HA e dispensa esse login. O usuário e senha valem para o acesso direto
por `http://IP-DO-HA:8099`, útil no celular e para salvar na tela inicial.

## Onde ficam os dados

- **Banco:** `/share/gaveteiro/gaveteiro.db` (SQLite, modo WAL)
- **Imagens:** `/data/images` no volume do add-on

Ambos entram nos backups do Home Assistant. O banco fica em `/share` de
propósito: assim o add-on **SQLite Web** consegue abri-lo para inspeção e
edição manual — é o equivalente do phpMyAdmin para SQLite.

## Adaptando ao seu gaveteiro

O seed inicial cria 12 módulos de 4×4 (192 gavetas). Para outro formato, ajuste
`DEFAULT_LAYOUT` em [`gaveteiro/backend/app/seed.py`](gaveteiro/backend/app/seed.py)
antes da primeira execução — cada entrada é `(nome, coluna, linha)`. Depois de
criado, posição e nome dos módulos se alteram pelo modo **Configurar** na
interface; a quantidade de linhas e colunas de cada módulo, não.

## Desenvolvimento

```bash
cd gaveteiro/backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
cd ../frontend && npm install && npm run build
cd ../backend && DB_PATH=./data/dev.db uvicorn app.main:app --reload --port 8099
```

Testes:

```bash
cd gaveteiro/backend && .venv/bin/pytest
```

## Licença

MIT
