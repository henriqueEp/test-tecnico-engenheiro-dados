# Documentação de Negócio

## Contexto

Este projeto analisa pedidos e clientes de uma operação de e-commerce. A partir de uma base de pedidos brutos, o pipeline identifica registros com problemas, consolida o comportamento de compra por cliente e calcula indicadores estatísticos para segmentação.

---

## O que o pipeline produz

O pipeline gera cinco resultados (chamados internamente de DF1 a DF5):

---

### DF1 — Pedidos com problema de qualidade

**O que é**: lista de todos os pedidos que não podem ser processados, com a descrição do motivo.

**Por que existe**: antes de qualquer análise, é necessário identificar e isolar pedidos que comprometam a confiabilidade dos resultados. Um pedido com valor negativo ou sem cliente válido não deve entrar nas métricas de negócio.

**Quais pedidos são rejeitados**:

| Motivo | Explicação |
|--------|------------|
| Valor negativo | O pedido registrou um valor monetário abaixo de zero |
| Valor ausente | O pedido não tem valor registrado |
| Identificador ausente | O pedido não possui um número de identificação |
| Código de cliente ausente ou inválido | O pedido não está associado a nenhum cliente |
| Cliente não encontrado | O pedido referencia um cliente que não existe na base de clientes |
| Identificador duplicado | Dois ou mais pedidos compartilham o mesmo número — impossível distingui-los |

> Um mesmo pedido pode aparecer com mais de um motivo — por exemplo, um pedido sem identificação e com valor nulo gerará duas entradas.

---

### DF2 — Consolidado de compras por cliente

**O que é**: resumo do histórico de compras de cada cliente, considerando apenas pedidos válidos (sem problemas de qualidade).

**Colunas**:

| Campo | Descrição |
|-------|-----------|
| `client_id` | Identificador único do cliente |
| `name` | Nome do cliente |
| `qtd_pedidos` | Quantidade de pedidos válidos realizados |
| `total_value` | Soma dos valores de todos os pedidos válidos (em R$) |

**Ordenação**: do cliente com maior valor total para o menor.

**Uso esperado**: base para identificação de clientes de alto valor, análise de churn, segmentação por volume de compras.

---

### DF3 — Indicadores estatísticos

**O que é**: quatro métricas que descrevem o comportamento de gasto dos clientes.

| Indicador | Significado no negócio |
|-----------|------------------------|
| **Média** | Valor médio de compras por cliente. Serve como referência para separar clientes abaixo e acima do padrão da base |
| **Mediana** | Valor que divide a base ao meio: metade dos clientes gasta menos, metade gasta mais. Menos sensível a extremos do que a média |
| **P10** | 10% dos clientes gastam menos do que esse valor — marca o limite inferior da base |
| **P90** | 10% dos clientes gastam mais do que esse valor — marca o limite superior da base |

---

### DF4 — Clientes acima da média

**O que é**: lista de clientes cujo total de compras supera a média geral da base.

**Critério de seleção**: `total_value > média` (calculada em DF3).

**Ordenação**: do cliente com menor valor total para o maior (crescente).

**Uso esperado**: identificação de clientes estratégicos, candidatos a programas de fidelidade ou ofertas exclusivas.

---

### DF5 — Clientes no intervalo central (P10 a P90)

**O que é**: lista de clientes com total de compras entre o P10 e o P90 — o chamado "grupo central" da base.

**Por que esse recorte**: ao remover os 10% que menos gastam e os 10% que mais gastam, obtém-se uma visão do comportamento típico da base, sem distorção causada por outliers. Esse grupo representa aproximadamente 80% dos clientes e é mais representativo do perfil médio de consumo.

**Ordenação**: crescente por valor total.

**Uso esperado**: análise de comportamento do cliente típico, definição de metas e benchmarks, campanhas de ativação para clientes com potencial de crescimento.
