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
├── download.py  # script de download via kagglehub
└── README.md    # este arquivo
```

## Como baixar os dados

```bash
pip install -r requirements.txt   # inclui kagglehub
python data/download.py
```

Isso usa `kagglehub.dataset_download(...)`, que baixa/cacheia o dataset e copia
os CSVs do cache para `data/raw/`. Por ser um dataset público, o download
funciona anônimo, sem precisar de conta/API key do Kaggle.

Se o download falhar (raro, geralmente rate limit), configure credenciais:
1. [kaggle.com/settings](https://www.kaggle.com/settings) > **API** > **Create New Token**, baixa um `kaggle.json`.
2. Coloque em `~/.kaggle/kaggle.json` (Linux/Mac) ou `%USERPROFILE%\.kaggle\kaggle.json` (Windows),
   ou defina `KAGGLE_USERNAME`/`KAGGLE_KEY` como variáveis de ambiente.

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
