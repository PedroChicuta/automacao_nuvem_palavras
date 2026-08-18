"""Scraper do detalhe de cada vaga da Catho.

Le o checkpoint da listagem (`listagem_{slug}.json`) para obter as URLs a
visitar, acessa cada pagina de vaga e extrai: titulo, descricao completa
(secao 'Sobre a vaga'), tipo de contrato, horario, salario e empresa.
Salva incrementalmente em `data/raw/detalhe_{slug}.jsonl` (uma linha por
vaga, append-only) — retomavel: IDs ja presentes sao pulados.

Uso:
    python -m src.scraper_detalhe              # todas as vagas da listagem
    python -m src.scraper_detalhe --smoke      # 5 vagas por cargo
    python -m src.scraper_detalhe --slug X     # apenas um cargo
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from datetime import datetime
from typing import Any

from src import config
from src.browser import abrir_pagina, criar_navegador

logger = logging.getLogger("scraper_detalhe")

# JS de extracao do detalhe. Retorna objeto estruturado.
_EXTRACT_JS = r"""
() => {
  const result = {
    titulo: null, descricao: '', tipo_contrato: '', horario: '',
    salario: '', empresa: '',
  };
  const trim = s => (s || '').trim();

  // Titulo: primeiro h2.title_offer ou h1
  const titleEl = document.querySelector('h2.title_offer') || document.querySelector('h1');
  result.titulo = titleEl ? trim(titleEl.innerText) : null;

  // Secao "Sobre a vaga": o h2 esta dentro de um div.flex (linha de header com
  // botao), entao o conteudo (descricao + sub-labels) esta nos irmaos do PAI
  // do h2, nao nos irmaos diretos do h2.
  const heads = Array.from(document.querySelectorAll('h2'));
  const sobreHead = heads.find(e => trim(e.innerText) === 'Sobre a vaga');
  if (sobreHead) {
    const parts = [];
    // Ponto de partida: irmao seguinte do pai do h2 (conteudo da secao).
    const startNode = sobreHead.parentElement
      ? sobreHead.parentElement.nextElementSibling
      : sobreHead.nextElementSibling;
    let node = startNode;
    while (node) {
      const tag = node.tagName;
      const cls = node.className || '';
      if (tag === 'H2' || (tag === 'DIV' && cls.includes('sub_box'))) break;
      const txt = trim(node.innerText);
      if (txt) parts.push({ tag, cls, txt });
      node = node.nextElementSibling;
    }
    for (let i = 0; i < parts.length; i++) {
      const p = parts[i];
      if (p.cls.includes('font-bold')) {
        if (/tipo de contrato/i.test(p.txt)) {
          result.tipo_contrato = parts[i + 1] ? parts[i + 1].txt : '';
        } else if (/hor[aá]rio de trabalho/i.test(p.txt)) {
          result.horario = parts[i + 1] ? parts[i + 1].txt : '';
        }
        // outros sub-labels sao ignorados (seus valores tambem)
      } else {
        result.descricao += (result.descricao ? '\n' : '') + p.txt;
      }
    }
  }

  // div.sub_box para Salario e Sobre a empresa
  const subBoxes = Array.from(document.querySelectorAll('div.sub_box'));
  for (const sb of subBoxes) {
    const lines = trim(sb.innerText).split('\n').map(s => s.trim()).filter(Boolean);
    if (lines[0] === 'Salário' && lines.length > 1) {
      result.salario = lines.slice(1).join(' ');
    } else if (lines[0] === 'Sobre a empresa' && lines.length > 1) {
      result.empresa = lines[1];
    }
  }
  return result;
}
"""

# Padrao para detectar modalidade dentro da descricao.
_RE_MODALIDADE = {
    "remoto": r"\bremoto\b",
    "híbrido": r"\bh[ií]brido\b",
    "presencial": r"\bpresencial\b",
}


def _detectar_modalidade(texto: str) -> str:
    low = texto.lower()
    for mod, pat in _RE_MODALIDADE.items():
        import re
        if re.search(pat, low):
            return mod.capitalize()
    return ""


def _carregar_listagem(slug: str) -> list[dict[str, Any]]:
    path = config.listagem_path(slug)
    if not path.exists():
        logger.warning("listagem ausente para %s — rode scraper_listagem antes", slug)
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _carregar_detalhe_ids(slug: str) -> set[str]:
    path = config.detalhe_path(slug)
    if not path.exists():
        return set()
    ids: set[str] = set()
    for linha in path.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            ids.add(json.loads(linha).get("id_vaga", ""))
        except json.JSONDecodeError:
            continue
    return ids


def _append_detalhe(slug: str, registro: dict[str, Any]) -> None:
    path = config.detalhe_path(slug)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def coletar_cargo(slug: str, cargo_nome: str, max_vagas: int | None = None) -> int:
    """Visita cada vaga da listagem de `slug` e extrai o detalhe.

    Retorna o numero de novas vagas detalhadas. `max_vagas` limita o total
    (util no smoke test).
    """
    listagem = _carregar_listagem(slug)
    if not listagem:
        return 0
    ja_feitos = _carregar_detalhe_ids(slug)
    logger.info("[%s] listagem=%d, ja detalhados=%d", slug, len(listagem), len(ja_feitos))

    pendentes = [v for v in listagem if v.get("id_vaga") and v["id_vaga"] not in ja_feitos]
    if max_vagas is not None:
        pendentes = pendentes[:max_vagas]
    logger.info("[%s] pendentes=%d", slug, len(pendentes))
    if not pendentes:
        return 0

    novos = 0
    with criar_navegador() as (_pw, _browser, ctx):
        for i, vaga in enumerate(pendentes, start=1):
            url = vaga["url_vaga"]
            tentativa = 0
            registro: dict[str, Any] | None = None
            while True:
                tentativa += 1
                try:
                    page, resp = abrir_pagina(ctx, url)
                    status = resp.status if resp else None
                    if status != 200:
                        raise RuntimeError(f"status={status}")
                    page.wait_for_timeout(3500)
                    extra = page.evaluate(_EXTRACT_JS)
                    page.close()
                    registro = {
                        "cargo": cargo_nome,
                        "id_vaga": vaga["id_vaga"],
                        "url_vaga": url,
                        "titulo": extra.get("titulo") or vaga.get("titulo", ""),
                        "empresa": extra.get("empresa") or vaga.get("empresa", ""),
                        "regiao": vaga.get("regiao", ""),
                        "salario": extra.get("salario", "") or vaga.get("salario_resumo", ""),
                        "tipo_contrato": extra.get("tipo_contrato", ""),
                        "horario": extra.get("horario", ""),
                        "modalidade": _detectar_modalidade(extra.get("descricao", "")),
                        "descricao_completa": extra.get("descricao", ""),
                        "data_publicacao": vaga.get("data_publicacao", ""),
                        "data_coleta": datetime.now().isoformat(timespec="seconds"),
                    }
                    break
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[%s] %s tentativa %d falhou: %s",
                                   slug, vaga["id_vaga"], tentativa, exc)
                    if tentativa >= config.DETALHE_MAX_TENTATIVAS:
                        logger.error("[%s] %s: max tentativas, pulando",
                                     slug, vaga["id_vaga"])
                        registro = {
                            "cargo": cargo_nome,
                            "id_vaga": vaga["id_vaga"],
                            "url_vaga": url,
                            "titulo": vaga.get("titulo", ""),
                            "empresa": vaga.get("empresa", ""),
                            "regiao": vaga.get("regiao", ""),
                            "salario": vaga.get("salario_resumo", ""),
                            "tipo_contrato": "",
                            "horario": "",
                            "modalidade": "",
                            "descricao_completa": "",
                            "data_publicacao": vaga.get("data_publicacao", ""),
                            "data_coleta": datetime.now().isoformat(timespec="seconds"),
                            "erro": str(exc),
                        }
                        break
                    time.sleep(config.DETALHE_BACKOFF_BASE * (2 ** (tentativa - 1)))

            if registro:
                _append_detalhe(slug, registro)
                novos += 1
                tem_desc = bool(registro.get("descricao_completa"))
                logger.info("[%s] (%d/%d) id=%s desc=%s",
                            slug, i, len(pendentes), vaga["id_vaga"],
                            "OK" if tem_desc else "VAZIA")

            # delay humano; pausa longa a cada N vagas
            if i % config.PAUSA_A_CADA_N_VAGAS == 0:
                time.sleep(random.uniform(config.PAUSA_LONGA_MIN, config.PAUSA_LONGA_MAX))
            else:
                time.sleep(random.uniform(config.DELAY_DETALHE_MIN,
                                          config.DELAY_DETALHE_MAX))

    return novos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scraper do detalhe da Catho")
    parser.add_argument("--smoke", action="store_true",
                        help=f"smoke test: {config.SMOKE_VAGAS_DETALHE} vagas por cargo")
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

    cargos = config.CARGOS
    if args.slug:
        cargos = [c for c in config.CARGOS if c["slug"] == args.slug]
        if not cargos:
            logger.error("slug desconhecido: %s", args.slug)
            return 2

    max_vagas = config.SMOKE_VAGAS_DETALHE if args.smoke else None
    total = 0
    for cargo in cargos:
        n = coletar_cargo(cargo["slug"], cargo["nome"], max_vagas=max_vagas)
        logger.info("[%s] novas detalhadas: %d", cargo["slug"], n)
        total += n
    logger.info("TOTAL novas detalhadas: %d", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
