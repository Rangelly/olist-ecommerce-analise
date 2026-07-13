# Insights - Olist E-commerce

EDA descritiva feita em `notebooks/eda_olist.py`, sobre `data/processed/olist_analytics.parquet`
(112.650 itens de pedido, 98.666 pedidos únicos, 95.420 clientes únicos, set/2016 a set/2018 -
os últimos meses da série têm poucos pedidos, então o período mais recente está incompleto e não
deve ser lido como "queda de vendas").

Gráficos completos em `reports/*.png`. Números abaixo conferidos diretamente contra o dataset.

## Os 5 insights principais

1. **Atraso de entrega é o fator isolado mais forte associado a insatisfação.**
   Pedidos atrasados têm review_score médio de **2,27**, contra **4,29** nos pedidos entregues
   no prazo (diferença de ~2 pontos, numa escala de 1 a 5). Olhando pelo outro lado: **62,4%**
   dos pedidos atrasados recebem nota 1 ou 2, contra apenas **9,3%** dos pedidos no prazo.

2. **A maioria dos clientes está satisfeita, mas a insatisfação é concentrada e ruidosa.**
   77,6% das reviews são nota 4 ou 5. Ainda assim, 14,2% são nota 1 ou 2 - e a nota 1 sozinha
   (11,1%) é mais comum que a nota 2 (3,1%) ou a nota 3 (8,3%), sinal de que quem fica
   insatisfeito tende a dar a pior nota possível, não uma nota intermediária.

3. **Só 6,8% dos pedidos entregues chegam atrasados, mas o impacto por estado é muito
   desigual.** Nos 15 estados de cliente com maior volume, o Maranhão (MA) tem a maior taxa de
   atraso (17,4%), seguido por Ceará (13,8%), Bahia (12,2%) e Rio de Janeiro (12,1%). São Paulo
   (4,5%) e Paraná (4,0%) - os estados com maior volume de pedidos - têm as menores taxas.

4. **Distância logística (cliente e vendedor em estados diferentes) quase dobra a chance de
   atraso**: 8,0% de atraso quando cliente e vendedor estão em estados diferentes, contra 4,5%
   quando estão no mesmo estado. 64% dos pedidos já envolvem estados diferentes.

5. **O ticket médio varia forte por categoria, mas as categorias mais vendidas não são as mais
   caras.** Entre as top 10 categorias por volume, `watches_gifts` tem o maior preço médio por
   item (R$ 201,14) e `telephony` o menor (R$ 71,21) - mas `bed_bath_table` (cama/mesa/banho) é a
   categoria mais vendida em volume, com ticket médio moderado (R$ 93,30). Ticket médio geral por
   pedido: R$ 160,61. Pagamento por cartão de crédito domina (75,5% dos pedidos).

## Recomendações de negócio

- **Tratar atraso de entrega como prioridade de retenção, não só de logística.** O salto de
  ~9% para ~62% de notas baixas quando o pedido atrasa sugere que reduzir atraso é provavelmente
  a alavanca individual mais eficiente para subir a satisfação média - mais do que qualquer
  ajuste de produto ou preço.

- **Focar esforço logístico nos estados com pior desempenho, não distribuir igual.** MA, CE, BA
  e RJ têm taxa de atraso 2-3x maior que SP/PR. Vale investigar se é problema de transportadora
  regional, prazo estimado mal calibrado para essas rotas, ou concentração de vendedores longe
  desses clientes - e agir especificamente ali em vez de uma política única nacional.

- **Revisar a promessa de prazo (data estimada) para rotas interestaduais.** Como pedidos
  cliente-vendedor em estados diferentes atrasam quase 2x mais, pode ser mais barato ajustar a
  data estimada exibida no checkout (expectativa realista) do que tentar acelerar a entrega
  física nessas rotas - ambas resolvem o problema de satisfação, mas com custos bem diferentes.

- **Investigar a experiência de pós-venda para quem recebe atrasado**, mesmo quando o atraso é
  pequeno. Como a queda de nota associada ao atraso parece abrupta (não gradual), comunicação
  proativa (aviso de atraso antes da reclamação, rastreio claro) pode amortecer parte do dano de
  satisfação mesmo sem eliminar o atraso em si.

- **Não tratar vendedores de categorias caras (ex. watches_gifts, auto) com a mesma política de
  frete/prazo que categorias de alto volume e ticket menor** (ex. bed_bath_table, telephony) -
  o mix de produto por região pode explicar parte da variação de atraso e vale cruzar com dado
  de peso/dimensão do produto (disponível no dataset, ainda não explorado aqui) antes de agir.

## O que fica para uma próxima etapa (fora do escopo desta EDA)

- Teste de hipótese / significância estatística sobre as diferenças acima (aqui é só
  descritivo).
- Modelo preditivo de atraso ou de review_score (regressão/classificação).
- Segmentação de clientes/vendedores (clustering).
- Uso da tabela de geolocalização para medir distância real (não só "mesmo estado ou não").
