"""
Download do dataset "Brazilian E-Commerce Public Dataset by Olist" (Kaggle),
via `kagglehub` (lib oficial, mais simples que a Kaggle CLI).

Pré-requisitos:
1. Ter o pacote `kagglehub` instalado no ambiente Python:
       pip install kagglehub
2. Credenciais Kaggle configuradas (kagglehub aceita qualquer uma das opções):
   - ~/.kaggle/kaggle.json (ou %USERPROFILE%\\.kaggle\\kaggle.json no Windows)
   - variáveis de ambiente KAGGLE_USERNAME / KAGGLE_KEY
   Veja o passo a passo em data/README.md.

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
    except Exception as exc:  # kagglehub levanta exceções variadas de auth/rede
        print(
            f"\nFalha ao baixar o dataset: {exc}\n"
            "Causas mais comuns:\n"
            "  - kaggle.json ausente/inválido em ~/.kaggle/ (ou %USERPROFILE%\\.kaggle\\ no Windows)\n"
            "  - variáveis de ambiente KAGGLE_USERNAME/KAGGLE_KEY não configuradas\n"
            "  - dataset exige aceitar os termos de uso no site do Kaggle antes do primeiro download\n"
            "Veja o passo a passo em data/README.md.",
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
