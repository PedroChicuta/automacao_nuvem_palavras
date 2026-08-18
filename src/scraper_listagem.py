"""Scraper da listagem de vagas da Catho.

Para cada cargo (slug), percorre as paginas 1..max_paginas e extrai dos
`<article>` da listagem os metadados basicos: id, url, titulo, empresa,
regiao, salario resumo e data de publicacao. Salva incrementalmente em
`data/raw/listagem_{slug}.json` (checkpoint retomavel).

A execucao pode ser feita de duas formas:
    python -m src.scraper_listagem              # coleta padrao (MAX_PAGINAS)
    python -m src.scraper_listagem --smoke      # smoke test (SMOKE_PAGINAS)
    python -m src.scraper_listagem --slug X     # apenas um cargo
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
import time
from typing import Any

from src import config
from src.browser import abrir_pagina, criar_navegador

logger = logging.getLogger("scraper_listagem")

# Regex para o ID da vaga no final da URL: /vagas/{slug}/{id}
_RE_ID = re.compile(r"/vagas/[a-z0-9-]+/(\d+)(?:\?|$)")

# JS que extrai todos os articles da pagina.
_EXTRACT_JS = r"""
() => {
  const arts = document.querySelectorAll('article');
  const out = [];
  for (const a of Array.from(arts)) {
    const link = a.querySelector('a[href*="/vagas/"]');
    if (!link) continue;
    const href = link.href || '';
    if (!/\/vagas\/[a-z0-9-]+\/\d+/.test(href)) continue;
    const lines = (a.innerText || '').split('\n').map(s => s.trim()).filter(s => s.length);
    out.push({ href: href, lines: lines });
  }
  return out;
}
"""


# Padroes de linha reconhecidos no card da listagem.
_RE_DATA = re.compile(r"Publicada em \d{2}/\d{2}|Publicada Hoje", re.I)
_RE_REGIAO = re.compile(r"\d+\s+vaga", re.I)
_RE_SALARIO = re.compile(r"a combinar|r\$\s*\d", re.I)
# Linhas de ruido do card que nao sao campos uteis.
_RUIDO = {
    "vaga patrocinada",
    "quero me candidatar",
    "recrutador ativo",
    "por que?",
}
# Sufixos que aparecem grudados em campos reais (ex.: "+ 3 beneficios").
_RE_LIMPA = re.compile(r"\s+recrutador ativo.*$|\s+por que\?.*$", re.I)


def _parse_article(href: str, lines: list[str], cargo_nome: str) -> dict[str, Any]:
    """Converte o {href, lines} de um article em um registro estruturado.

    Parser baseado em padroes (nao posicional) para tolerar variacoes de
    layout como o badge 'VAGA PATROCINADA', que desloca as posicoes.
    Campos:
      - data_publicacao: linha que casa 'Publicada em DD/MM' ou 'Publicada Hoje'
      - regiao:          linha que casa 'N vaga(s)'
      - salario_resumo:  linha que casa 'A Combinar' ou 'R$ ...'
      - empresa:         'Empresa Confidencial' ou linha em CAIXA ALTA (nome da empresa)
      - titulo:          primeira linha restante nao-classificada e nao-ruido
    """
    m = _RE_ID.search(href)
    id_vaga = m.group(1) if m else ""

    data_publicacao = ""
    regiao = ""
    salario_resumo = ""
    empresa = ""
    titulo = ""

    candidatas_titulo: list[str] = []

    for ln in lines:
        ln_clean = _RE_LIMPA.sub("", ln).strip()
        low = ln_clean.lower()
        if not ln_clean or low in _RUIDO:
            continue
        if not data_publicacao and _RE_DATA.search(ln_clean):
            data_publicacao = ln_clean
        elif not regiao and _RE_REGIAO.search(ln_clean):
            regiao = ln_clean
        elif not salario_resumo and _RE_SALARIO.search(ln_clean):
            salario_resumo = ln_clean
        elif not empresa and ("empresa confidencial" in low or ln_clean.isupper()):
            empresa = ln_clean.replace(" Por que?", "").strip()
        else:
            candidatas_titulo.append(ln_clean)

    # Heuristica para o titulo: se ouver candidato, o primeiro; senao, o cargo.
    titulo = candidatas_titulo[0] if candidatas_titulo else cargo_nome

    return {
        "cargo": cargo_nome,
        "id_vaga": id_vaga,
        "url_vaga": href,
        "titulo": titulo,
        "empresa": empresa,
        "regiao": regiao,
        "salario_resumo": salario_resumo,
        "data_publicacao": data_publicacao,
    }


def _carregar_checkpoint(slug: str) -> list[dict[str, Any]]:
    path = config.listagem_path(slug)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("checkpoint corrompido, iniciando do zero: %s", path)
    return []


def _salvar_checkpoint(slug: str, registros: list[dict[str, Any]]) -> None:
    path = config.listagem_path(slug)
    path.write_text(
        json.dumps(registros, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def coletar_cargo(slug: str, cargo_nome: str, max_paginas: int) -> list[dict[str, Any]]:
    """Coleta a listagem de um cargo, paginando de 1..max_paginas.

    E retomavel: paginas ja coletadas (presentes no checkpoint com a mesma
    faixa) sao puladas. Dedup por id_vaga.
    """
    registros = _carregar_checkpoint(slug)
    ids_existentes = {r["id_vaga"] for r in registros if r.get("id_vaga")}
    logger.info("[%s] checkpoint: %d vagas ja conhecidas", slug, len(ids_existentes))

    with criar_navegador() as (_pw, _browser, ctx):
        for pagina in range(1, max_paginas + 1):
            url = config.URL_BASE_LISTAGEM.format(slug=slug, pagina=pagina)
            logger.info("[%s] pag %d -> %s", slug, pagina, url)

            tentativa = 0
            while True:
                tentativa += 1
                try:
                    page, resp = abrir_pagina(ctx, url)
                    if resp is None or resp.status != 200:
                        raise RuntimeError(f"status={getattr(resp, 'status', None)}")
                    page.wait_for_timeout(3000)
                    raw = page.evaluate(_EXTRACT_JS)
                    page.close()
                    break
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[%s] pag %d tentativa %d falhou: %s",
                                   slug, pagina, tentativa, exc)
                    if tentativa >= config.DETALHE_MAX_TENTATIVAS:
                        logger.error("[%s] pag %d: max tentativas, pulando", slug, pagina)
                        raw = []
                        break
                    time.sleep(config.DETALHE_BACKOFF_BASE * (2 ** (tentativa - 1)))

            novos = 0
            for item in raw:
                reg = _parse_article(item["href"], item["lines"], cargo_nome)
                if not reg["id_vaga"] or reg["id_vaga"] in ids_existentes:
                    continue
                registros.append(reg)
                ids_existentes.add(reg["id_vaga"])
                novos += 1
            logger.info("[%s] pag %d: %d articles, %d novos (total %d)",
                        slug, pagina, len(raw), novos, len(registros))

            if not raw:
                logger.info("[%s] pag %d sem articles: fim antecipado", slug, pagina)
                _salvar_checkpoint(slug, registros)
                break

            _salvar_checkpoint(slug, registros)
            # delay humano entre paginas
            time.sleep(random.uniform(config.DELAY_LISTAGEM_MIN,
                                      config.DELAY_LISTAGEM_MAX))

    return registros


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scraper da listagem da Catho")
    parser.add_argument("--smoke", action="store_true",
                        help=f"smoke test: {config.SMOKE_PAGINAS} pagina(s) por cargo")
    parser.add_argument("--slug", default=None,
                        help="slug unico para processar (default: todos)")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.RUNTIME_LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    max_paginas = config.SMOKE_PAGINAS if args.smoke else config.MAX_PAGINAS
    cargos = config.CARGOS
    if args.slug:
        cargos = [c for c in config.CARGOS if c["slug"] == args.slug]
        if not cargos:
            logger.error("slug desconhecido: %s", args.slug)
            return 2

    total = 0
    for cargo in cargos:
        regs = coletar_cargo(cargo["slug"], cargo["nome"], max_paginas)
        logger.info("[%s] final: %d vagas", cargo["slug"], len(regs))
        total += len(regs)
    logger.info("TOTAL: %d vagas em %d cargo(s)", total, len(cargos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
