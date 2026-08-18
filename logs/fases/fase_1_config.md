# Fase 1 — config.py
**Data/Hora**: 2026-08-17T21:08:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Centralizar em um único módulo (`src/config.py`) os slugs dos cargos, URLs,
parâmetros de execução (MAX_PAGINAS, delays), caminhos de arquivo e
configurações stealth do navegador, de modo que os próximos módulos importem
tudo deste ponto.

## O que foi feito
- Definidos os 3 cargos em `CARGOS` (cientista/engenheiro/analista de dados),
  cada um com `slug` e `nome` legível.
- Definida `URL_BASE_LISTAGEM` com placeholders `{slug}` e `{pagina}`.
- `MAX_PAGINAS = 2` (escopo Fase 10: ~20 vagas/cargo = 15 da pág 1 + 5 da pág 2).
- Constantes de smoke test: `SMOKE_PAGINAS=1`, `SMOKE_VAGAS_DETALHE=5`.
- Configuração stealth: `HEADLESS=False`, `USER_AGENT` real Chrome/Linux,
  `LOCALE='pt-BR'`, `VIEWPORT` 1366x768.
- Delays humanizados (min/max para `random.uniform`) para listagem e detalhe,
  pausa longa a cada 20 vagas.
- Retry do detalhe: 3 tentativas, backoff base 5s (5/10/20s).
- Caminhos de saída (XLSX/CSV/termos/frequência/log) e helpers
  `listagem_path(slug)` / `detalhe_path(slug)` para checkpoints.
- Criação idempotente dos diretórios ao importar o módulo.

## Arquivos criados/alterados
- `src/config.py` (novo) — configurações centrais.

## Verificação
- Comando: `python -c "from src import config; print(len(config.CARGOS)); ..."`
- Resultado: **pass**
- Evidência:
  ```
  CARGOS: 3
    cientista-de-dados -> Cientista de Dados
    engenheiro-de-dados -> Engenheiro de Dados
    analista-de-dados -> Analista de Dados
  MAX_PAGINAS: 2
  URL exemplo: https://www.catho.com.br/vagas/cientista-de-dados/?page=1
  ROOT_DIR existe: True
  RAW_DIR existe: True
  ```

## Problemas encontrados
- Nenhum.

## Próxima fase
Fase 2: `browser.py` — factory do navegador stealth (Playwright) e smoke test
ao vivo (HTTP 200) contra a URL da Catho.
