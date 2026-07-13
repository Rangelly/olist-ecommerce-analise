"""
Pipeline de ETL: junta as tabelas brutas do Olist em um único dataset
analítico (grão = item de pedido) e salva o resultado limpo em
data/processed/olist_analytics.parquet.

Não faz nenhuma análise/gráfico/insight -- só extração, limpeza e
modelagem do dataset final. Isso fica a cargo de outra etapa (notebooks/
análise exploratória).

Uso:
    python src/build_analytics_dataset.py

Pré-requisito: os CSVs brutos precisam existir em data/raw/ (ver
data/download.py e data/README.md para instruções de download).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "olist_analytics.parquet"

REQUIRED_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_products_dataset.csv",
    "product_category_name_translation.csv",
]

DATE_COLUMNS_ORDERS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
DATE_COLUMNS_REVIEWS = ["review_creation_date", "review_answer_timestamp"]
DATE_COLUMNS_ITEMS = ["shipping_limit_date"]


def check_raw_files_exist() -> None:
    missing = [f for f in REQUIRED_FILES if not (RAW_DIR / f).exists()]
    if missing:
        raise FileNotFoundError(
            "Arquivos brutos ausentes em data/raw/: "
            + ", ".join(missing)
            + "\nRode `python data/download.py` para baixar o dataset antes de rodar "
            "este pipeline (veja data/README.md)."
        )


# ----------------------------------------------------------------------
# Carga
# ----------------------------------------------------------------------


def load_raw() -> dict[str, pd.DataFrame]:
    return {
        "orders": pd.read_csv(RAW_DIR / "olist_orders_dataset.csv", parse_dates=DATE_COLUMNS_ORDERS),
        "items": pd.read_csv(RAW_DIR / "olist_order_items_dataset.csv", parse_dates=DATE_COLUMNS_ITEMS),
        "payments": pd.read_csv(RAW_DIR / "olist_order_payments_dataset.csv"),
        "reviews": pd.read_csv(RAW_DIR / "olist_order_reviews_dataset.csv", parse_dates=DATE_COLUMNS_REVIEWS),
        "customers": pd.read_csv(RAW_DIR / "olist_customers_dataset.csv"),
        "sellers": pd.read_csv(RAW_DIR / "olist_sellers_dataset.csv"),
        "products": pd.read_csv(RAW_DIR / "olist_products_dataset.csv"),
        "category_translation": pd.read_csv(RAW_DIR / "product_category_name_translation.csv"),
    }


# ----------------------------------------------------------------------
# Limpeza por tabela
# ----------------------------------------------------------------------


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset="order_id")
    # order_id é a chave primária: linhas sem ela não servem para nenhum merge
    df = df.dropna(subset=["order_id", "customer_id"])
    after = len(df)
    print(f"[orders] {before} -> {after} linhas (duplicatas/PK nula removidas: {before - after})")
    return df


def clean_items(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["order_id", "order_item_id"])
    df = df.dropna(subset=["order_id", "product_id", "seller_id"])
    # preço/frete não podem ser negativos ou zero -- descarta linhas absurdas
    df = df[(df["price"] > 0) & (df["freight_value"] >= 0)]
    after = len(df)
    print(f"[order_items] {before} -> {after} linhas (duplicatas/valores inválidos removidos: {before - after})")
    return df


def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=["order_id"])
    df = df[df["payment_value"] >= 0]

    # Um pedido pode ter várias linhas de pagamento (parcelas/métodos combinados).
    # Agregamos para o grão de pedido: valor total pago, método "principal"
    # (o de maior valor) e nº de parcelas máximo informado.
    agg = (
        df.sort_values("payment_value", ascending=False)
        .groupby("order_id")
        .agg(
            payment_total_value=("payment_value", "sum"),
            payment_type=("payment_type", "first"),  # maior valor após sort
            payment_installments=("payment_installments", "max"),
            payment_methods_count=("payment_type", "nunique"),
        )
        .reset_index()
    )
    print(f"[order_payments] {before} linhas brutas -> {len(agg)} pedidos agregados")
    return agg


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=["order_id"])
    # Alguns pedidos têm mais de uma review (reabertura de atendimento).
    # Mantemos a mais recente por review_creation_date. na_position="first" garante
    # que, se uma das reviews duplicadas tiver data nula, a com data valida "vence"
    # (senão a linha com NaT ficaria por último no sort e seria "a mais recente" por engano).
    df = df.sort_values("review_creation_date", na_position="first").drop_duplicates(
        subset="order_id", keep="last"
    )
    keep_cols = ["order_id", "review_score", "review_creation_date", "review_answer_timestamp"]
    df = df[keep_cols]
    after = len(df)
    print(f"[order_reviews] {before} -> {after} linhas (uma review por pedido, mantida a mais recente)")
    return df


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset="customer_id")
    after = len(df)
    print(f"[customers] {before} -> {after} linhas (duplicatas removidas: {before - after})")
    return df


def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset="seller_id")
    after = len(df)
    print(f"[sellers] {before} -> {after} linhas (duplicatas removidas: {before - after})")
    return df


def clean_products(df: pd.DataFrame, translation: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset="product_id")

    df = df.merge(translation, on="product_category_name", how="left")
    # Categoria sem tradução (ausente na tabela de-para) ou nula na origem
    # vira "unknown" em vez de descartar o produto -- não queremos perder
    # linhas de venda só por causa de metadado de categoria.
    df["product_category_name_english"] = df["product_category_name_english"].fillna("unknown")
    df["product_category_name"] = df["product_category_name"].fillna("unknown")

    after = len(df)
    print(f"[products] {before} -> {after} linhas (duplicatas removidas, categoria traduzida)")
    return df


# ----------------------------------------------------------------------
# Montagem do dataset analítico
# ----------------------------------------------------------------------


def build_analytics_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    orders = clean_orders(tables["orders"])
    items = clean_items(tables["items"])
    payments = clean_payments(tables["payments"])
    reviews = clean_reviews(tables["reviews"])
    customers = clean_customers(tables["customers"])
    sellers = clean_sellers(tables["sellers"])
    products = clean_products(tables["products"], tables["category_translation"])

    # Grão final = item de pedido. Orders/customers/reviews/payments são
    # 1:1 com order_id (após a agregação/dedup acima); products e sellers
    # são 1:1 com product_id/seller_id. Todo merge abaixo é, portanto,
    # many-to-one a partir de `items`.
    df = items.merge(orders, on="order_id", how="inner", validate="many_to_one")
    df = df.merge(customers, on="customer_id", how="left", validate="many_to_one")
    df = df.merge(products, on="product_id", how="left", validate="many_to_one")
    df = df.merge(sellers, on="seller_id", how="left", validate="many_to_one")
    df = df.merge(payments, on="order_id", how="left", validate="many_to_one")
    df = df.merge(reviews, on="order_id", how="left", validate="many_to_one")

    # Coluna de atraso de entrega: dias entre a entrega real ao cliente e a
    # data estimada. Positivo = atrasado, negativo/zero = dentro do prazo.
    # Fica NaN para pedidos ainda não entregues/cancelados (sem data real).
    df["delivery_delay_days"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.days
    df["is_late_delivery"] = df["delivery_delay_days"] > 0

    return df


def report_missing(df: pd.DataFrame) -> None:
    null_share = df.isna().mean().sort_values(ascending=False)
    top_nulls = null_share[null_share > 0].head(15)
    if not top_nulls.empty:
        print("\nColunas com maior % de nulos no dataset final:")
        print((top_nulls * 100).round(1).to_string())


def main() -> int:
    try:
        check_raw_files_exist()
    except FileNotFoundError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    tables = load_raw()
    analytics_df = build_analytics_table(tables)

    report_missing(analytics_df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    analytics_df.to_parquet(OUTPUT_PATH, index=False)

    print(f"\nDataset analítico salvo em: {OUTPUT_PATH}")
    print(f"Linhas: {len(analytics_df)} | Colunas: {analytics_df.shape[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
