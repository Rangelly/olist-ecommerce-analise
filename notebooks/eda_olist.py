"""
EDA - Olist E-commerce

Script de analise exploratoria (nao interativo): carrega o dataset
analitico ja limpo (data/processed/olist_analytics.parquet), gera
graficos em reports/ e imprime um resumo de insights no terminal.

Objetivo do projeto: entender o que impacta a satisfacao do cliente
(review_score) e o atraso de entrega, com recomendacoes acionaveis.

Uso:
    python notebooks/eda_olist.py

Le src/PIPELINE_NOTES.md para entender o grao do dataset (1 linha = 1
item de pedido) e as decisoes de limpeza antes de interpretar qualquer
numero aqui -- em particular: `delivery_delay_days`/`is_late_delivery`
sao NaN para pedidos nao entregues/cancelados (nao viram 0), e o dataset
esta no grao de item, entao pedidos com >1 item aparecem em >1 linha
(agregamos por order_id quando faz sentido, ex.: satisfacao e atraso sao
atributos do pedido, nao do item).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")  # nao interativo -- roda via terminal, sem abrir janela

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "olist_analytics.parquet"
REPORTS_DIR = PROJECT_ROOT / "reports"

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 100
PALETTE = "viridis"

# Insights coletados ao longo do script para o resumo final
INSIGHTS: list[str] = []


def add_insight(text: str) -> None:
    INSIGHTS.append(text)
    print(f"  -> {text}")


def savefig(fig: plt.Figure, name: str) -> None:
    path = REPORTS_DIR / name
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[grafico salvo] {path}")


# ----------------------------------------------------------------------
# 1. Visao geral
# ----------------------------------------------------------------------


def secao_visao_geral(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("1. VISAO GERAL")
    print("=" * 70)

    print(f"Shape (linhas x colunas, grao=item de pedido): {df.shape}")

    periodo_ini = df["order_purchase_timestamp"].min()
    periodo_fim = df["order_purchase_timestamp"].max()
    print(f"Periodo coberto (compra): {periodo_ini.date()} a {periodo_fim.date()}")

    n_pedidos = df["order_id"].nunique()
    n_clientes = df["customer_unique_id"].nunique()
    print(f"Pedidos unicos: {n_pedidos:,} | Clientes unicos: {n_clientes:,}")

    # Um pedido = 1a linha de compra (evita contar mes errado por causa de
    # multiplos itens no mesmo pedido, que tem a mesma order_purchase_timestamp)
    pedidos = df.drop_duplicates(subset="order_id").copy()
    pedidos["mes_compra"] = pedidos["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    por_mes = pedidos.groupby("mes_compra").size()

    fig, ax = plt.subplots(figsize=(11, 4.5))
    por_mes.plot(ax=ax, marker="o", color=sns.color_palette(PALETTE, 1)[0])
    ax.set_title("Pedidos por mes")
    ax.set_xlabel("Mes da compra")
    ax.set_ylabel("Nº de pedidos")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    savefig(fig, "01_pedidos_por_mes.png")

    mes_pico = por_mes.idxmax()
    add_insight(
        f"Volume de pedidos cresceu ao longo do periodo analisado, com pico em "
        f"{mes_pico.strftime('%m/%Y')} ({por_mes.max():,} pedidos); dado tem cauda "
        f"final curta/incompleta (poucos meses no fim da serie)."
    )

    status_counts = pedidos["order_status"].value_counts(normalize=True) * 100
    print("\nDistribuicao de order_status (%):")
    print(status_counts.round(1).to_string())

    return pedidos  # reutilizado nas proximas secoes (1 linha por pedido)


# ----------------------------------------------------------------------
# 2. Satisfacao do cliente x atraso de entrega
# ----------------------------------------------------------------------


def secao_satisfacao(pedidos: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("2. SATISFACAO DO CLIENTE (review_score) x ATRASO DE ENTREGA")
    print("=" * 70)

    com_review = pedidos.dropna(subset=["review_score"])
    pct_sem_review = (1 - len(com_review) / len(pedidos)) * 100
    print(f"Pedidos sem review associada: {pct_sem_review:.1f}%")

    dist_scores = com_review["review_score"].value_counts(normalize=True).sort_index() * 100

    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.countplot(
        data=com_review, x="review_score", order=[1, 2, 3, 4, 5],
        hue="review_score", palette=PALETTE, legend=False, ax=ax,
    )
    ax.set_title("Distribuicao de review_score")
    ax.set_xlabel("Nota da review (1-5)")
    ax.set_ylabel("Nº de pedidos")
    savefig(fig, "02_distribuicao_review_score.png")

    pct_top2 = dist_scores.reindex([4, 5]).sum()
    pct_bottom2 = dist_scores.reindex([1, 2]).sum()
    add_insight(
        f"{pct_top2:.1f}% das reviews sao nota 4 ou 5 (clientes satisfeitos), mas "
        f"{pct_bottom2:.1f}% sao nota 1 ou 2 -- uma minoria vocal insatisfeita que "
        f"vale investigar a fundo."
    )

    # Atraso: so pedidos entregues tem delivery_delay_days nao-nulo
    entregues = com_review.dropna(subset=["delivery_delay_days"])
    pct_atrasado_geral = entregues["is_late_delivery"].mean() * 100

    media_score_por_atraso = entregues.groupby("is_late_delivery")["review_score"].mean()
    print("\nMedia de review_score por status de entrega:")
    print(media_score_por_atraso.round(2).to_string())

    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.boxplot(
        data=entregues, x="is_late_delivery", y="review_score",
        hue="is_late_delivery", palette=PALETTE, legend=False, ax=ax,
    )
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["No prazo / adiantado", "Atrasado"])
    ax.set_title("Review score: pedidos no prazo vs. atrasados")
    ax.set_xlabel("")
    ax.set_ylabel("Review score")
    savefig(fig, "03_review_score_vs_atraso.png")

    score_no_prazo = media_score_por_atraso.get(False, float("nan"))
    score_atrasado = media_score_por_atraso.get(True, float("nan"))
    add_insight(
        f"Pedidos atrasados tem review_score medio de {score_atrasado:.2f}, contra "
        f"{score_no_prazo:.2f} para pedidos no prazo -- diferenca de "
        f"{score_no_prazo - score_atrasado:.2f} pontos na escala de 1 a 5."
    )

    # % de pedidos atrasados com nota baixa (<=2)
    atrasados = entregues[entregues["is_late_delivery"]]
    pct_atrasado_nota_baixa = (atrasados["review_score"] <= 2).mean() * 100
    pct_no_prazo_nota_baixa = (
        entregues.loc[~entregues["is_late_delivery"], "review_score"] <= 2
    ).mean() * 100
    add_insight(
        f"{pct_atrasado_nota_baixa:.1f}% dos pedidos atrasados recebem review_score <= 2, "
        f"contra apenas {pct_no_prazo_nota_baixa:.1f}% dos pedidos entregues no prazo -- "
        f"atraso de entrega e um forte preditor de insatisfacao."
    )

    print(f"\n(Contexto: {pct_atrasado_geral:.1f}% dos pedidos entregues chegaram atrasados)")


# ----------------------------------------------------------------------
# 3. Atraso de entrega
# ----------------------------------------------------------------------


def secao_atraso(pedidos: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("3. ATRASO DE ENTREGA")
    print("=" * 70)

    entregues = pedidos.dropna(subset=["delivery_delay_days"]).copy()
    pct_nao_entregues = (1 - len(entregues) / len(pedidos)) * 100
    print(f"Pedidos sem data de entrega registrada (cancelados/em transito): {pct_nao_entregues:.1f}%")

    pct_atrasado = entregues["is_late_delivery"].mean() * 100
    add_insight(
        f"{pct_atrasado:.1f}% dos pedidos efetivamente entregues chegaram depois da "
        f"data estimada."
    )

    # Por estado do cliente -- top 15 estados por volume, pra nao poluir o grafico
    top_estados = entregues["customer_state"].value_counts().head(15).index
    atraso_por_estado = (
        entregues[entregues["customer_state"].isin(top_estados)]
        .groupby("customer_state")["is_late_delivery"]
        .mean()
        .sort_values(ascending=False) * 100
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        x=atraso_por_estado.values, y=atraso_por_estado.index,
        hue=atraso_por_estado.index, palette=PALETTE, legend=False, ax=ax,
    )
    ax.set_title("% de pedidos atrasados por estado do cliente (top 15 por volume)")
    ax.set_xlabel("% atrasado")
    ax.set_ylabel("Estado do cliente")
    savefig(fig, "04_atraso_por_estado_cliente.png")

    pior_estado = atraso_por_estado.index[0]
    pior_valor = atraso_por_estado.iloc[0]
    add_insight(
        f"O estado do cliente com maior taxa de atraso (entre os 15 de maior volume) "
        f"e {pior_estado}, com {pior_valor:.1f}% dos pedidos atrasados -- vs. media "
        f"geral de {pct_atrasado:.1f}%."
    )

    # Evolucao no tempo
    entregues["mes_compra"] = entregues["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    atraso_mes = entregues.groupby("mes_compra")["is_late_delivery"].mean() * 100

    fig, ax = plt.subplots(figsize=(11, 4.5))
    atraso_mes.plot(ax=ax, marker="o", color=sns.color_palette(PALETTE, 1)[0])
    ax.set_title("% de pedidos atrasados por mes de compra")
    ax.set_xlabel("Mes da compra")
    ax.set_ylabel("% atrasado")
    savefig(fig, "05_atraso_evolucao_mensal.png")

    # Cliente x vendedor em estados diferentes -- proxy de distancia logistica
    cruz = pedidos.dropna(subset=["delivery_delay_days", "customer_state", "seller_state"]).copy()
    cruz["mesmo_estado"] = cruz["customer_state"] == cruz["seller_state"]
    atraso_por_mesmo_estado = cruz.groupby("mesmo_estado")["is_late_delivery"].mean() * 100
    add_insight(
        f"Quando cliente e vendedor estao no mesmo estado, {atraso_por_mesmo_estado.get(True, float('nan')):.1f}% "
        f"dos pedidos atrasam; quando estao em estados diferentes, sobe para "
        f"{atraso_por_mesmo_estado.get(False, float('nan')):.1f}% -- distancia logistica pesa no prazo."
    )


# ----------------------------------------------------------------------
# 4. Ticket medio por categoria de produto
# ----------------------------------------------------------------------


def secao_categorias(df: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("4. TICKET MEDIO / VALOR POR CATEGORIA DE PRODUTO (TOP 10)")
    print("=" * 70)

    # Aqui o grao de item faz sentido: preco e por item, nao por pedido
    cat_col = "product_category_name_english"
    top10_categorias = df[cat_col].value_counts().head(10).index

    resumo_cat = (
        df[df[cat_col].isin(top10_categorias)]
        .groupby(cat_col)
        .agg(
            n_itens=("price", "size"),
            preco_medio=("price", "mean"),
            frete_medio=("freight_value", "mean"),
        )
        .sort_values("n_itens", ascending=False)
    )
    print(resumo_cat.round(2).to_string())

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ordem = resumo_cat.sort_values("preco_medio", ascending=False).index
    sns.barplot(
        data=df[df[cat_col].isin(top10_categorias)],
        y=cat_col, x="price", order=ordem,
        hue=cat_col, palette=PALETTE, legend=False, ax=ax, errorbar=None,
    )
    ax.set_title("Preco medio por item - top 10 categorias (por volume)")
    ax.set_xlabel("Preco medio (R$)")
    ax.set_ylabel("Categoria")
    savefig(fig, "06_preco_medio_top10_categorias.png")

    cat_mais_cara = resumo_cat["preco_medio"].idxmax()
    cat_mais_barata = resumo_cat["preco_medio"].idxmin()
    add_insight(
        f"Entre as top 10 categorias por volume, '{cat_mais_cara}' tem o maior preco "
        f"medio por item (R$ {resumo_cat.loc[cat_mais_cara, 'preco_medio']:.2f}), "
        f"enquanto '{cat_mais_barata}' tem o menor (R$ {resumo_cat.loc[cat_mais_barata, 'preco_medio']:.2f})."
    )

    # Ticket medio de pagamento por pedido (nao por item) para ter uma visao
    # complementar de valor "por compra"
    pedidos = df.drop_duplicates(subset="order_id")
    ticket_medio_pedido = pedidos["payment_total_value"].mean()
    print(f"\nTicket medio por pedido (payment_total_value): R$ {ticket_medio_pedido:.2f}")


# ----------------------------------------------------------------------
# 5. Angulo adicional: metodo de pagamento e parcelas x satisfacao/atraso
# ----------------------------------------------------------------------


def secao_pagamento(pedidos: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("5. PAGAMENTO: METODO E PARCELAS")
    print("=" * 70)

    dist_metodo = pedidos["payment_type"].value_counts(normalize=True) * 100
    print("Distribuicao de payment_type (%):")
    print(dist_metodo.round(1).to_string())

    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.countplot(
        data=pedidos, y="payment_type",
        order=pedidos["payment_type"].value_counts().index,
        hue="payment_type", palette=PALETTE, legend=False, ax=ax,
    )
    ax.set_title("Pedidos por metodo de pagamento")
    ax.set_xlabel("Nº de pedidos")
    ax.set_ylabel("Metodo de pagamento")
    savefig(fig, "07_metodo_pagamento.png")

    metodo_top = dist_metodo.index[0]
    add_insight(
        f"'{metodo_top}' e o metodo de pagamento mais usado, respondendo por "
        f"{dist_metodo.iloc[0]:.1f}% dos pedidos."
    )

    # Relacao parcelas x ticket
    corr = pedidos[["payment_installments", "payment_total_value"]].corr().iloc[0, 1]
    print(f"\nCorrelacao (Pearson, descritiva) entre nº de parcelas e valor pago: {corr:.2f}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(
            f"ERRO: dataset não encontrado em {DATA_PATH}.\n"
            "Rode `python src/build_analytics_dataset.py` primeiro (após baixar os "
            "dados brutos com `python data/download.py`) para gerar o parquet."
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Carregando dataset de {DATA_PATH} ...")
    df = pd.read_parquet(DATA_PATH)

    pedidos = secao_visao_geral(df)
    secao_satisfacao(pedidos)
    secao_atraso(pedidos)
    secao_categorias(df)
    secao_pagamento(pedidos)

    print("\n" + "=" * 70)
    print("RESUMO - INSIGHTS PRINCIPAIS")
    print("=" * 70)
    for i, insight in enumerate(INSIGHTS, start=1):
        print(f"{i}. {insight}")

    print(f"\nGraficos salvos em: {REPORTS_DIR}")
    print("Ver tambem reports/INSIGHTS.md para insights + recomendacoes de negocio.")


if __name__ == "__main__":
    main()
