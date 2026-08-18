"""Consolidacao dos dados coletados em planilha e insumos para nuvem de palavras.

Le todos os `detalhe_{slug}.jsonl`, aplica parsing de salario e limpeza de
texto, monta um DataFrame pandas e exporta:
  - `data/vagas_catho.xlsx`  (planilha principal)
  - `data/vagas_catho.csv`   (espelho CSV)
  - `data/termos_para_nuvem.txt` (descricao concatenada por cargo)

Uso:
    python -m src.storage
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from src import config
from src.parser import limpar_salario, limpar_texto, parse_salario

logger = logging.getLogger("storage")

# Colunas finais da planilha, na ordem do plan.md (sec 4).
COLUNAS: list[str] = [
    "cargo",
    "url_vaga",
    "id_vaga",
    "titulo_vaga",
    "empresa",
    "salario",
    "salario_min",
    "salario_max",
    "regiao",
    "modalidade",
    "tipo_contrato",
    "horario",
    "descricao_completa",
    "requisitos",
    "habilidades",
    "data_publicacao",
    "data_coleta",
]


def _ler_detalhes() -> list[dict[str, Any]]:
    """Le todos os detalhe_*.jsonl e devolve a lista de registros."""
    registros: list[dict[str, Any]] = []
    for cargo in config.CARGOS:
        path = config.detalhe_path(cargo["slug"])
        if not path.exists():
            logger.warning("detalhe ausente: %s", path)
            continue
        for linha in path.read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            try:
                registros.append(json.loads(linha))
            except json.JSONDecodeError:
                logger.warning("linha invalida em %s", path)
    return registros


def _normalizar(reg: dict[str, Any]) -> dict[str, Any]:
    """Converte um registro bruto no schema final da planilha."""
    salario_bruto = reg.get("salario", "")
    salario_limpo = limpar_salario(salario_bruto)
    sal_min, sal_max = parse_salario(salario_bruto)
    descricao = limpar_texto(reg.get("descricao_completa", ""))
    return {
        "cargo": reg.get("cargo", ""),
        "url_vaga": reg.get("url_vaga", ""),
        "id_vaga": reg.get("id_vaga", ""),
        "titulo_vaga": reg.get("titulo", ""),
        "empresa": reg.get("empresa", ""),
        "salario": salario_limpo,
        "salario_min": sal_min,
        "salario_max": sal_max,
        "regiao": reg.get("regiao", ""),
        "modalidade": reg.get("modalidade", ""),
        "tipo_contrato": reg.get("tipo_contrato", ""),
        "horario": reg.get("horario", ""),
        "descricao_completa": descricao,
        # Na Catho, requisitos e habilidades estao embutidos na descricao.
        "requisitos": "",
        "habilidades": "",
        "data_publicacao": reg.get("data_publicacao", ""),
        "data_coleta": reg.get("data_coleta", ""),
    }


def consolidar() -> pd.DataFrame:
    """Le, normaliza e devolve o DataFrame consolidado (dedupe por id_vaga)."""
    regs = _ler_detalhes()
    if not regs:
        logger.warning("nenhum registro encontrado em data/raw/")
        return pd.DataFrame(columns=COLUNAS)
    norm = [_normalizar(r) for r in regs]
    df = pd.DataFrame(norm, columns=COLUNAS)
    antes = len(df)
    df = df.drop_duplicates(subset=["id_vaga"], keep="last").reset_index(drop=True)
    if len(df) < antes:
        logger.info("dedupe: %d -> %d registros", antes, len(df))
    return df


def exportar(df: pd.DataFrame) -> tuple[Path, Path]:
    """Exporta XLSX e CSV. Devolve (xlsx_path, csv_path)."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    xlsx = config.XLSX_PATH
    csv = config.CSV_PATH
    df.to_excel(xlsx, index=False)
    df.to_csv(csv, index=False, encoding="utf-8-sig")
    logger.info("exportado: %s (%d linhas)", xlsx, len(df))
    logger.info("exportado: %s", csv)
    return xlsx, csv


def gerar_termos_nuvem(df: pd.DataFrame) -> Path:
    """Gera `data/termos_para_nuvem.txt` com a descricao concatenada por cargo.

    Formato: blocos separados por cargo, com cabecalho `# CARGO: <nome>`,
    para que o arquivo possa ser usado tanto para nuvem global (ignorando
    cabecalhos) quanto para nuvem por cargo (fase 8 fara a frequencia).
    """
    path = config.TERMOS_NUVEM_PATH
    partes: list[str] = []
    for cargo, grupo in df.groupby("cargo"):
        textos = grupo["descricao_completa"].dropna().tolist()
        if not textos:
            continue
        bloco = f"# CARGO: {cargo}\n" + "\n\n".join(textos)
        partes.append(bloco)
    path.write_text("\n\n".join(partes), encoding="utf-8")
    n_cargos = df["cargo"].nunique()
    n_vagas = len(df)
    logger.info("termos para nuvem: %s (%d cargos, %d vagas)", path, n_cargos, n_vagas)
    return path


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.RUNTIME_LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    df = consolidar()
    if df.empty:
        logger.error("DataFrame vazio — nada a exportar.")
        return 1
    exportar(df)
    gerar_termos_nuvem(df)

    # Resumo para log
    logger.info("Resumo por cargo:")
    for cargo, grupo in df.groupby("cargo"):
        com_desc = grupo["descricao_completa"].str.len().gt(0).sum()
        com_sal = grupo["salario_min"].notna().sum()
        logger.info("  %s: %d vagas | %d com desc | %d com salario",
                    cargo, len(grupo), com_desc, com_sal)
    return 0


if __name__ == "__main__":
    sys.exit(main())
