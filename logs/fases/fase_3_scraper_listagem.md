# Fase 3 — scraper_listagem.py
**Data/Hora**: 2026-08-17T21:09:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Coletar as URLs e metadados básicos das vagas a partir da listagem da Catho,
para os 3 cargos, com checkpoint retomável por cargo. Smoke: 1 página/cargo.

## O que foi feito
- `coletar_cargo(slug, nome, max_paginas)`: percorre `?page=1..N`, extrai
  `<article>` via JS injetado, faz retry 3x com backoff em falha/403, salva
  checkpoint a cada página.
- Parser `_parse_article` **baseado em padrões** (não posicional) — tolera
  variações de layout como o badge "VAGA PATROCINADA", que desloca posições:
  - `data_publicacao`: regex `Publicada em DD/MM` ou `Publicada Hoje`;
  - `regiao`: regex `\d+ vaga`;
  - `salario_resumo`: regex `a combinar` ou `r$`;
  - `empresa`: `Empresa Confidencial` ou linha em CAIXA ALTA;
  - `titulo`: primeira linha restante não-ruido (não data/badge/vaga/salário);
  - `id_vaga`: extraído da URL via regex `/vagas/{slug}/(\d+)`.
- Checkpoint JSON em `data/raw/listagem_{slug}.json` (retomável: dedupe por
  `id_vaga`).
- CLI: `--smoke` (1 pág), `--slug X` (um cargo), default (MAX_PAGINAS=2).
- Logging simultâneo em arquivo (`logs/scraping.log`) e stdout.
- Delay humano entre páginas (`random.uniform` dos delays do config).

## Arquivos criados/alterados
- `src/scraper_listagem.py` (novo) — scraper de listagem com checkpoint.
- `scripts/_probe_listagem.py` (criado e removido) — sondagem descartável que
  validou a estrutura do `<article>` antes da implementação.

## Verificação
- Comando: `python -m src.scraper_listagem --smoke` (1 pág/cargo).
- Resultado: **pass**
- Evidência:
  ```
  [cientista-de-dados] pag 1: 19 articles, 19 novos (total 19)
  [engenheiro-de-dados]  pag 1: 20 articles, 20 novos (total 20)
  [analista-de-dados]    pag 1: 20 articles, 20 novos (total 20)
  TOTAL: 59 vagas em 3 cargo(s)
  ```
- Inspeção do checkpoint (analista-de-dados) após correção do parser:
  ```
  titulo: 'Analista de Banco de Dados'   (antes: 'Publicada em 11/08' — bug corrigido)
  data:   'Publicada em 11/08'           (antes: 'VAGA PATROCINADA'    — bug corrigido)
  empresa/regiao/salario: corretos
  ```

## Problemas encontrados
- **Bug de parsing em vagas patrocinadas**: o badge "VAGA PATROCINADA"
  aparecia como `lines[0]`, deslocando `titulo`/`data_publicacao`. Corrigido
  trocando parser posicional por parser baseado em padrões regex. Validado
  re-rodando após limpar checkpoints.

## Próxima fase
Fase 4: `scraper_detalhe.py` — visita cada URL de vaga e extrai os campos do
detalhe (salário, descrição, requisitos, habilidades etc.) com retry e
checkpoint JSONL. Smoke: 5 vagas/cargo.
