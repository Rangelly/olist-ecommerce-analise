# Dados — Olist Brazilian E-Commerce

## Fonte

- Dataset: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- Kaggle id: `olistbr/brazilian-ecommerce`
- Licença: CC BY-NC-SA 4.0 (uso não comercial, exige atribuição a Olist)
- Período: pedidos de 2016 a 2018, ~100k pedidos, ~9 tabelas relacionadas

## Estrutura de pastas

```
data/
├── raw/         # CSVs originais do Kaggle (NUNCA versionado, ver .gitignore)
├── processed/   # dataset analítico limpo, gerado pelo pipeline em src/
├── download.py  # script de download via Kaggle CLI
└── README.md    # este arquivo
```

## Como baixar os dados

### 1. Instalar o `kagglehub`

```bash
pip install kagglehub
```

(já incluso em `requirements.txt`)

### 2. Configurar credenciais do Kaggle

1. Acesse [kaggle.com/settings](https://www.kaggle.com/settings) > seção **API** > **Create New Token**.
2. Isso baixa um arquivo `kaggle.json` contendo `username` e `key`.
3. Coloque esse arquivo em:
   - Linux/Mac: `~/.kaggle/kaggle.json`
   - Windows: `C:\Users\<seu_usuario>\.kaggle\kaggle.json`
4. (Opcional, alternativa ao arquivo) defina variáveis de ambiente em vez do arquivo:
   ```bash
   set KAGGLE_USERNAME=seu_usuario
   set KAGGLE_KEY=sua_key
   ```
5. Na primeira vez, pode ser necessário aceitar os termos de uso do dataset
   na própria página do Kaggle (botão "Download" uma vez, manualmente, se o
   download retornar erro 403).

### 3. Rodar o download

```bash
python data/download.py
```

Isso usa `kagglehub.dataset_download(...)` para baixar/cachear o dataset e copia
os CSVs do cache para `data/raw/`.

## Arquivos esperados em `data/raw/` após o download

- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_products_dataset.csv`
- `olist_geolocation_dataset.csv`
- `product_category_name_translation.csv`

## Atribuição

Dataset "Brazilian E-Commerce Public Dataset by Olist", disponibilizado por
Olist no Kaggle sob licença CC BY-NC-SA 4.0. Uso restrito a fins não
comerciais (portfólio pessoal), com crédito à Olist.
