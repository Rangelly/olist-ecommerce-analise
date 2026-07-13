# Insights - Olist E-commerce

EDA descritiva feita em `notebooks/eda_olist.py`, sobre `data/processed/olist_analytics.parquet`
(112.650 itens de pedido, 98.666 pedidos unicos, 95.420 clientes unicos, set/2016 a set/2018 -
os ultimos meses da serie tem poucos pedidos, entao o periodo mais recente esta incompleto e nao
deve ser lido como "queda de vendas").

Graficos completos em `reports/*.png`. Numeros abaixo conferidos diretamente contra o dataset.

## Os 5 insights principais

1. **Atraso de entrega e o fator isolado mais forte associado a insatisfacao.**
   Pedidos atrasados tem review_score medio de **2,27**, contra **4,29** nos pedidos entregues
   no prazo (diferenca de ~2 pontos, numa escala de 1 a 5). Olhando pelo outro lado: **62,4%**
   dos pedidos atrasados recebem nota 1 ou 2, contra apenas **9,3%** dos pedidos no prazo.

2. **A maioria dos clientes esta satisfeita, mas a insatisfacao e concentrada e ruidosa.**
   77,6% das reviews sao nota 4 ou 5. Ainda assim, 14,2% sao nota 1 ou 2 - e a nota 1 sozinha
   (11,1%) e mais comum que a nota 2 (3,1%) ou a nota 3 (8,3%), sinal de que quem fica
   insatisfeito tende a dar a pior nota possivel, nao uma nota intermediaria.

3. **So 6,8% dos pedidos entregues chegam atrasados, mas o impacto por estado e muito
   desigual.** Nos 15 estados de cliente com maior volume, o Maranhao (MA) tem a maior taxa de
   atraso (17,4%), seguido por Ceara (13,8%), Bahia (12,2%) e Rio de Janeiro (12,1%). Sao Paulo
   (4,5%) e Parana (4,0%) - os estados com maior volume de pedidos - tem as menores taxas.

4. **Distancia logistica (cliente e vendedor em estados diferentes) quase dobra a chance de
   atraso**: 8,0% de atraso quando cliente e vendedor estao em estados diferentes, contra 4,5%
   quando estao no mesmo estado. 64% dos pedidos ja envolvem estados diferentes.

5. **O ticket medio varia forte por categoria, mas as categorias mais vendidas nao sao as mais
   caras.** Entre as top 10 categorias por volume, `watches_gifts` tem o maior preco medio por
   item (R$ 201,14) e `telephony` o menor (R$ 71,21) - mas `bed_bath_table` (cama/mesa/banho) e a
   categoria mais vendida em volume, com ticket medio moderado (R$ 93,30). Ticket medio geral por
   pedido: R$ 160,61. Pagamento por cartao de credito domina (75,5% dos pedidos).

## Recomendacoes acionaveis

- **Tratar atraso de entrega como prioridade de retencao, nao so de logistica.** O salto de
  ~9% para ~62% de notas baixas quando o pedido atrasa sugere que reduzir atraso e provavelmente
  a alavanca individual mais eficiente para subir a satisfacao media - mais do que qualquer
  ajuste de produto ou preco.

- **Focar esforço logistico nos estados com pior desempenho, nao distribuir igual.** MA, CE, BA
  e RJ tem taxa de atraso 2-3x maior que SP/PR. Vale investigar se e problema de transportadora
  regional, prazo estimado mal calibrado para essas rotas, ou concentracao de vendedores longe
  desses clientes - e agir especificamente ali em vez de uma politica unica nacional.

- **Revisar a promessa de prazo (data estimada) para rotas interestaduais.** Como pedidos
  cliente-vendedor em estados diferentes atrasam quase 2x mais, pode ser mais barato ajustar a
  data estimada exibida no checkout (expectativa realista) do que tentar acelerar a entrega
  fisica nessas rotas - ambas resolvem o problema de satisfacao, mas com custos bem diferentes.

- **Investigar a experiencia de pos-venda para quem recebe atrasado**, mesmo quando o atraso e
  pequeno. Como a queda de nota associada ao atraso parece abrupta (nao gradual), comunicacao
  proativa (aviso de atraso antes da reclamacao, rastreio claro) pode amortecer parte do dano de
  satisfacao mesmo sem eliminar o atraso em si.

- **Nao tratar vendedores de categorias caras (ex. watches_gifts, auto) com a mesma politica de
  frete/prazo que categorias de alto volume e ticket menor** (ex. bed_bath_table, telephony) -
  o mix de produto por regiao pode explicar parte da variacao de atraso e vale cruzar com dado
  de peso/dimensao do produto (disponivel no dataset, ainda nao explorado aqui) antes de agir.

## O que fica para uma proxima etapa (fora do escopo desta EDA)

- Teste de hipotese / significancia estatistica sobre as diferencas acima (aqui e so
  descritivo).
- Modelo preditivo de atraso ou de review_score (regressao/classificacao).
- Segmentacao de clientes/vendedores (clustering).
- Uso da tabela de geolocalizacao para medir distancia real (nao so "mesmo estado ou nao").
