# Changelog

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
