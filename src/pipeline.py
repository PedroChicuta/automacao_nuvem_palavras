"""Pipeline de scraping da Catho: listagem -> detalhe -> planilha.

Orquestra as 3 etapas em um unico comando. Cada etapa e retomavel (usa
checkpoints), entao re-executar o pipeline continua de onde parou.

Uso:
    python -m src.pipeline              # coleta completa (MAX_PAGINAS)
    python -m src.pipeline --smoke      # smoke test (1 pag listagem, 5 vagas detalhe)
    python -m src.pipeline --only lista   # so a etapa de listagem
    python -m src.pipeline --only detalhe # so a etapa de detalhe
    python -m src.pipeline --only gera    # so a consolidacao (planilha)
    python -m src.pipeline --help        # ajuda
"""
from __future__ import annotations

import argparse
import logging
import sys

from src import config

logger = logging.getLogger("pipeline")


def etapa_listagem(smoke: bool) -> None:
    from src.scraper_listagem import coletar_cargo
    max_paginas = config.SMOKE_PAGINAS if smoke else config.MAX_PAGINAS
    for cargo in config.CARGOS:
        coletar_cargo(cargo["slug"], cargo["nome"], max_paginas)


def etapa_detalhe(smoke: bool) -> None:
    from src.scraper_detalhe import coletar_cargo as coletar_detalhe
    max_vagas = config.SMOKE_VAGAS_DETALHE if smoke else None
    for cargo in config.CARGOS:
        coletar_detalhe(cargo["slug"], cargo["nome"], max_vagas=max_vagas)


def etapa_geracao() -> None:
    from src.storage import consolidar, exportar, gerar_termos_nuvem
    df = consolidar()
    if df.empty:
        logger.warning("DataFrame vazio — nenhum dado para gerar planilha.")
        return
    exportar(df)
    gerar_termos_nuvem(df)
    logger.info("Resumo:")
    for cargo, grupo in df.groupby("cargo"):
        com_desc = grupo["descricao_completa"].str.len().gt(0).sum()
        logger.info("  %s: %d vagas | %d com descricao", cargo, len(grupo), com_desc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pipeline de scraping da Catho (listagem -> detalhe -> planilha)",
    )
    parser.add_argument("--smoke", action="store_true",
                        help="smoke test: 1 pagina listagem + 5 vagas detalhe por cargo")
    parser.add_argument("--only", choices=["lista", "detalhe", "gera"],
                        default=None,
                        help="executa apenas uma etapa (default: todas em sequencia)")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.RUNTIME_LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    modo = "SMOKE" if args.smoke else "COMPLETO"
    logger.info("=== Pipeline Catho [%s] ===", modo)

    try:
        if args.only is None or args.only == "lista":
            logger.info("--- Etapa 1/3: Listagem ---")
            etapa_listagem(args.smoke)
        if args.only is None or args.only == "detalhe":
            logger.info("--- Etapa 2/3: Detalhe ---")
            etapa_detalhe(args.smoke)
        if args.only is None or args.only == "gera":
            logger.info("--- Etapa 3/3: Geracao da planilha ---")
            etapa_geracao()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline falhou: %s", exc)
        return 1

    logger.info("=== Pipeline concluido ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
