# Gaveteiro

Controle de estoque para gaveteiros de componentes eletrônicos.

## Instalação

1. **Settings → Add-ons → Add-on Store → ⋮ → Repositories**
2. Adicione `https://github.com/leonesmoura/ha-gaveteiro`
3. Instale o **Gaveteiro** e ajuste as opções antes de iniciar

## Configuração

| Opção | Padrão | O que faz |
|---|---|---|
| `username` | `admin` | Usuário do acesso direto por `http://IP:8099` |
| `password` | `troque-esta-senha` | Senha — **troque antes de iniciar** |
| `image_max_size` | `800` | Lado maior das fotos, em pixels |

Pela barra lateral do Home Assistant (Ingress) o login é dispensado: quem
entrou no HA já está autenticado. O usuário e senha valem para o acesso pela
porta 8099, útil no celular ou para salvar na tela inicial.

## Primeiro uso

O add-on cria um gaveteiro de exemplo com 12 módulos de 4×4 (192 gavetas).
Ajuste ao seu gaveteiro real em **Configurar**:

- **Setas** movem o módulo pelo arranjo. Mover para uma célula ocupada troca
  os dois de lugar.
- **Grade** define quantas linhas × colunas o módulo tem. Aumentar cria
  gavetas novas continuando a numeração; reduzir só remove gaveta vazia.
- **Gaveta** é a proporção largura/altura, para representar gavetas rasas ou
  fundas.
- **Escala** é o tamanho em relação aos outros módulos, para gaveteiros que
  misturam gavetas pequenas e grandes.
- **+ Módulo** adiciona outro gaveteiro ao arranjo; **apagar** remove um
  módulo vazio.

Depois, em **Numeração**, escolha como as gavetas são numeradas — com prévia
antes de aplicar. Renumerar troca só os rótulos; o conteúdo não se move.

## Fotos nas gavetas

Cada gaveta mostra uma miniatura ao fundo. Sem configurar nada, ela herda a
foto da primeira peça que tiver imagem. Para uma foto própria — útil quando a
gaveta tem várias peças, ou para fotografar o conteúdo real — clique na gaveta
e use **Foto da gaveta**; no celular abre direto a câmera. Remover a foto
própria faz a gaveta voltar a herdar a da peça.

O botão **Sem fotos** na barra superior desliga as miniaturas. É preferência
de cada navegador, não do gaveteiro.

## Numeração

| Modo | Como conta |
|---|---|
| **Aos pares** | Módulos em duplas na ordem do número, com a linha atravessando as duas: M1/M2 = 1-32, M3/M4 = 33-64 |
| **Bloco por módulo** | Cada módulo com sua faixa: M1 = 1-16, M2 = 17-32 |
| **Contínuo pela linha física** | Segue a leitura visual do arranjo, atravessando todos os módulos da linha |

Todos aceitam número inicial e prefixo (`G1`, `G2`, …), e a direção pode ser
por linha ou por coluna.

## Importar de planilha

O repositório traz `tools/import_xlsx.py`, que lê uma planilha onde cada bloco
de colunas representa uma gaveta, e envia para `POST /api/import`:

```bash
python tools/import_xlsx.py Estoque.xlsx --dry-run
python tools/import_xlsx.py Estoque.xlsx --url http://IP:8099 --user admin --password SENHA
```

Com `reset: true` no payload, a importação limpa o conteúdo anterior — útil
para reimportar depois de mudar a numeração, já que o conteúdo precisa seguir
o número da gaveta e não a posição física.

## Dados e backup

- **Banco:** `/share/gaveteiro/gaveteiro.db` (SQLite em modo WAL)
- **Imagens:** `/data/images`

Os dois entram nos backups do Home Assistant. O banco fica em `/share` de
propósito, para o add-on **SQLite Web** conseguir abri-lo — é o equivalente
do phpMyAdmin para SQLite.

## Problemas comuns

**O painel não aparece na barra lateral.** Ative *Show in sidebar* nas
informações do add-on.

**Não consigo reduzir um módulo.** A redução só remove gaveta vazia. O erro
lista quais gavetas ainda têm conteúdo.

**Esqueci a senha.** Troque nas opções do add-on e reinicie.
