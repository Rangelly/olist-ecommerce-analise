"""
Download do dataset "Brazilian E-Commerce Public Dataset by Olist" (Kaggle),
via `kagglehub` (lib oficial, mais simples que a Kaggle CLI).

Dataset público: o download funciona anônimo, sem credenciais. Se falhar
(raro, geralmente rate limit), ver data/README.md para configurar API key.

Uso:
    python data/download.py

kagglehub baixa (com cache) para uma pasta própria do usuário; este script
copia os CSVs de lá para data/raw/, que é o caminho usado pelo resto do
pipeline (src/build_analytics_dataset.py).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

DATASET = "olistbr/brazilian-ecommerce"

# data/raw relativo a este arquivo, não ao cwd de onde o script é chamado
RAW_DIR = Path(__file__).resolve().parent / "raw"


def main() -> int:
    try:
        import kagglehub
    except ImportError:
        print(
            "ERRO: pacote `kagglehub` não encontrado.\n"
            "Instale com: pip install kagglehub",
            file=sys.stderr,
        )
        return 1

    print(f"Baixando dataset '{DATASET}' via kagglehub...")
    try:
        cache_path = kagglehub.dataset_download(DATASET)
    except Exception as exc:  # kagglehub levanta exceções variadas de rede/rate-limit
        print(
            f"\nFalha ao baixar o dataset: {exc}\n"
            "Dataset público, download deveria funcionar anônimo. Se persistir:\n"
            "  - configure credenciais Kaggle (ver data/README.md)\n"
            "  - ou aceite os termos de uso do dataset manualmente no site do Kaggle",
            file=sys.stderr,
        )
        return 1

    print(f"kagglehub baixou/cacheou os arquivos em: {cache_path}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for csv_file in Path(cache_path).glob("*.csv"):
        shutil.copy2(csv_file, RAW_DIR / csv_file.name)
        copied += 1

    if copied == 0:
        print(
            f"AVISO: nenhum .csv encontrado em {cache_path}. Verifique o conteúdo manualmente.",
            file=sys.stderr,
        )
        return 1

    print(f"{copied} arquivo(s) CSV copiado(s) para: {RAW_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
