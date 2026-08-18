# Fase 2 — browser.py
**Data/Hora**: 2026-08-17T21:12:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Implementar a factory do navegador Playwright em modo stealth, encapsulando as
configurações que driblam o bloqueio anti-bot (403) da Catho, e validar ao vivo
com um smoke test (HTTP 200).

## O que foi feito
- `criar_navegador()` como context manager (`with`): devolve
  `(playwright, browser, context)` e fecha tudo ao sair.
- Configuração stealth encapsulada:
  - `headless=False` (catho bloqueia headless puro);
  - args `--disable-blink-features=AutomationControlled`, `--no-sandbox`,
    `--disable-dev-shm-usage`;
  - `user_agent` real Chrome/Linux, `locale=pt-BR`, `viewport` 1366x768,
    `timezone_id=America/Sao_Paulo`;
  - init script removendo `navigator.webdriver`, definindo `languages`,
    `plugins` e `window.chrome`.
- `abrir_pagina(context, url)` helper que cria `page`, faz `goto` com timeout
  do config e devolve `(page, response)`.
- Parâmetros opcionais `headless`/`user_agent` permitem sobrescrever o config
  em testes.

## Arquivos criados/alterados
- `src/browser.py` (novo) — factory stealth + helper `abrir_pagina`.

## Verificação
- Comando: smoke test ao vivo abrindo
  `https://www.catho.com.br/vagas/cientista-de-dados/?page=1`.
- Resultado: **pass**
- Evidência:
  ```
  STATUS: 200
  TITLE: Vagas de emprego de Cientista de dados | Catho
  ARTICLES: 20
  ```

## Problemas encontrados
- Nenhum. A configuração stealth já havia sido validada no diagnóstico do
  `plan.md`; aqui foi apenas encapsulada em código reutilizável.

## Próxima fase
Fase 3: `scraper_listagem.py` — coleta das URLs de vagas a partir da listagem,
com checkpoint JSON por cargo. Smoke: 1 página por cargo.
