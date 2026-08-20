# Changelog

## 1.8.0

- Miniatura por gaveta: foto própria enviada pela galeria ou pela câmera do
  celular, ou herdada automaticamente da primeira peça que tiver imagem
- Botão "Sem fotos"/"Com fotos" liga e desliga as miniaturas; a escolha fica
  guardada no navegador de cada pessoa
- Remover a foto própria devolve a herdada da peça

## 1.7.0

- Controle geral de proporção e escala na barra de configuração, aplicando a
  todos os módulos de uma vez; a etiqueta avisa "(misto)" quando os módulos
  estão diferentes entre si
- Botão "Padrão" devolve proporção e escala aos valores originais

## 1.6.1

- Cabeçalho mostra "Gaveteiro, Estoque" e a versão instalada, para conferir
  de olho se o navegador carregou a build nova
- `index.html` deixa de ser cacheado: sem isso o navegador continuava
  carregando a versão antiga do app mesmo depois de atualizar o add-on

## 1.6.0

- Grade configurável por módulo: criar módulos de qualquer tamanho, não só 4×4
- Proporção e escala da gaveta por módulo, para gaveteiros com gavetas de tamanhos diferentes
- Criar e apagar módulos pela interface
- Reduzir um módulo recusa se alguma gaveta que sairia da grade tiver conteúdo

## 1.5.0

- Opção `reset` na importação, para reimportar depois de mudar a numeração

## 1.4.0

- Numeração "aos pares": M1/M2 = 1-32, M3/M4 = 33-64, com a linha atravessando os dois módulos

## 1.3.0

- Herda o tema do Home Assistant sob o Ingress; claro/escuro automático fora dele
- Rótulo, descrição e barra de ocupação visíveis na própria gaveta
- Busca destaca as gavetas em sequência, com contador e navegação entre resultados
- Quantidades animam ao mudar; confirmação visual nas ações
- Layout de celular: painel em folha, "Ver tudo" para o gaveteiro inteiro caber na tela

## 1.2.0

- Endpoint `POST /api/import` para importação em lote
- Descrição por gaveta e criação de módulos

## 1.1.0

- Modo de configuração: mover e renomear módulos
- Configuração da numeração das gavetas com prévia

## 1.0.0

- Primeira versão: gaveteiro interativo, peças com foto, busca, estoque mínimo e histórico
