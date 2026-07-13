# Notas do pipeline de limpeza (`build_analytics_dataset.py`)

## Grão do dataset final

Uma linha = **um item de pedido** (`order_id` + `order_item_id`). É o menor
grão que ainda faz sentido juntar com preço/frete/vendedor sem duplicar
informação de forma ambígua. Pedido, cliente e review "sobem" repetidos
para cada item do mesmo pedido -- é esperado e é responsabilidade da
análise (agregação por `order_id` quando fizer sentido).

Saída: `data/processed/olist_analytics.parquet`.

## Por que Parquet e não CSV

- Preserva tipos (datas como datetime, não string) -- evita reparsing e
  bugs de fuso/formatação na etapa de análise.
- Arquivo menor (compressão colunar) para um dataset com ~110k linhas e
  dezenas de colunas.
- Leitura mais rápida em pandas (`pd.read_parquet`) do que `read_csv` com
  `parse_dates`.
- Trade-off aceito: não é abrível diretamente num editor de texto/Excel.
  Se isso for necessário no futuro, é trivial gerar um CSV a partir do
  parquet (`df.to_csv(...)`).

## Decisões de limpeza, tabela a tabela

**orders**
- Remove duplicatas por `order_id` (chave primária).
- Descarta linhas sem `order_id` ou `customer_id` (não dá pra juntar nada
  sem essas chaves).
- Datas parseadas: `order_purchase_timestamp`, `order_approved_at`,
  `order_delivered_carrier_date`, `order_delivered_customer_date`,
  `order_estimated_delivery_date`. Pedidos ainda não entregues/cancelados
  ficam com `order_delivered_customer_date` nulo -- **não é erro**, é
  esperado (status `canceled`, `unavailable`, `shipped` etc.), então essas
  linhas são mantidas, só a métrica de atraso fica nula para elas.

**order_items**
- Remove duplicatas por `(order_id, order_item_id)`.
- Descarta linhas com `product_id`/`seller_id` nulos.
- Filtra `price > 0` e `freight_value >= 0`: preço zero/negativo é
  inconsistência de dado, não uma venda real.

**order_payments**
- Um pedido pode ter várias linhas de pagamento (parcelamento, ou
  combinação de métodos, ex. voucher + cartão). Agregado para 1 linha por
  `order_id`:
  - `payment_total_value` = soma de todos os pagamentos do pedido.
  - `payment_type` = método com maior valor pago (proxy de "método
    principal"; um pedido pode ter 2+ métodos, mas guardar uma lista
    complicaria o grão final sem necessidade nesta etapa).
  - `payment_installments` = máximo de parcelas informado.
  - `payment_methods_count` = quantos métodos distintos foram usados.
- Descarta `payment_value < 0` (estornos representados como negativo
  quebrariam a soma sem contexto adicional que este pipeline não modela).

**order_reviews**
- Uma pequena fração dos pedidos tem mais de uma review (reabertura de
  atendimento pelo cliente). Mantida apenas a mais recente por
  `review_creation_date`, para garantir 1:1 com `order_id`.
- Mantidas só as colunas relevantes para análise (`review_score` e datas);
  os textos livres de review (`review_comment_title/message`) foram
  descartados nesta etapa por não serem necessários para análise
  quantitativa e por conterem PII/texto livre em português que exigiria
  tratamento à parte (NLP), fora de escopo aqui.

**customers / sellers**
- Apenas dedupe por chave primária (`customer_id` / `seller_id`).
- `customer_unique_id` (identifica a pessoa através de múltiplos
  `customer_id`) foi mantido como veio, sem dedupe adicional -- decisão de
  agregação por cliente único fica para a etapa de análise.

**products**
- Dedupe por `product_id`.
- Categoria traduzida via `product_category_name_translation` (left join).
  Quando a tradução não existe (categoria ausente na tabela de-para) ou o
  nome da categoria é nulo na origem, o valor vira `"unknown"` em vez de
  descartar o produto -- perder linhas de venda por causa de metadado de
  categoria seria pior que ter uma categoria "unknown".
- Atributos físicos do produto (peso, dimensões, nº de fotos) que vierem
  nulos do CSV bruto **não foram imputados** nesta etapa -- ficam como
  `NaN` no dataset final. Decisão deliberada: imputar peso/dimensão median
  poderia mascarar dado ausente de forma enganosa para quem for analisar
  logística; melhor deixar explícito e decidir na análise se vale a pena.

## Coluna calculada: atraso de entrega

```
delivery_delay_days = order_delivered_customer_date - order_estimated_delivery_date
is_late_delivery = delivery_delay_days > 0
```

- Positivo = entregou depois do prometido (atraso).
- Zero ou negativo = dentro do prazo ou adiantado.
- `NaN` quando o pedido não tem `order_delivered_customer_date` (não
  entregue/cancelado) -- **não é preenchido com 0 nem descartado**, para
  não confundir "não entregue" com "entregue no prazo".

## Merges e integridade referencial

Todos os merges usam `validate="many_to_one"` (de `order_items` para as
demais tabelas já agregadas/dedupe 1:1 por chave) -- se alguma limpeza
anterior deixar duplicata residual numa chave, o pipeline quebra em vez de
silenciosamente multiplicar linhas.

`orders` -> `items` é `inner join`: um item sem pedido correspondente (ou
vice-versa) não tem uso analítico. As demais tabelas (customers, products,
sellers, payments, reviews) são `left join` a partir de `items`, porque
ausência de review ou de metadado de produto não deve derrubar a linha de
venda -- só gera nulos nessas colunas (reportados no log de execução do
pipeline, seção "Colunas com maior % de nulos").

## O que este pipeline explicitamente NÃO faz

- Nenhuma análise exploratória, gráfico ou conclusão de negócio (fica para
  a etapa de análise/notebook).
- Não usa `geolocation` (tabela de lat/long por CEP) -- não fazia parte do
  join analítico pedido; pode ser incorporada depois se a análise precisar
  de mapa/distância.
- Não trata os textos de review (NLP/sentimento) -- fora de escopo.

## Resultado

Executado de ponta a ponta contra os CSVs reais: 112.650 linhas x 39
colunas em `data/processed/olist_analytics.parquet`.
