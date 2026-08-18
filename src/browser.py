"""Factory do navegador Playwright em modo stealth.

A Catho bloqueia (HTTP 403) requisições headless "puras". A configuração aqui
encapsulada (navegador headed + User-Agent real + `navigator.webdriver` oculto
+ flag `--disable-blink-features=AutomationControlled`) foi validada no
diagnostico e retorna HTTP 200 com conteudo renderizado.

Uso tipico:
    from src.browser import criar_navegador
    with criar_navegador() as (playwright, browser, context):
        page = context.new_page()
        page.goto("https://www.catho.com.br/vagas/cientista-de-dados/?page=1")
        ...
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from playwright.sync_api import Browser, BrowserContext, Playwright

from src import config


# Script injetado em cada documento antes de qualquer outro JS do site,
# removendo os marcadores mais comuns de automacao.
_STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = window.chrome || {runtime: {}};
"""


@contextmanager
def criar_navegador(
    headless: bool | None = None,
    user_agent: str | None = None,
) -> Iterator[tuple[Playwright, Browser, BrowserContext]]:
    """Cria e devolve `(playwright, browser, context)` em contexto `with`.

    Ao sair do `with`, fecha browser e playwright automaticamente.

    Parametros opcionais permitem sobrescrever `HEADLESS` e `USER_AGENT` do
    `config` (util em testes).
    """
    headless = config.HEADLESS if headless is None else headless
    user_agent = config.USER_AGENT if user_agent is None else user_agent

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    try:
        browser = pw.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            user_agent=user_agent,
            locale=config.LOCALE,
            viewport=config.VIEWPORT,
            timezone_id="America/Sao_Paulo",
            java_script_enabled=True,
        )
        context.set_default_timeout(config.NAV_TIMEOUT_MS)
        context.add_init_script(_STEALTH_INIT_SCRIPT)
        try:
            yield pw, browser, context
        finally:
            context.close()
            browser.close()
    finally:
        pw.stop()


def abrir_pagina(context: BrowserContext, url: str, wait_until: str = "domcontentloaded"):
    """Abre uma URL no contexto e devolve `(page, response)`.

    `response` pode ser None em navegacoes que nao geram evento de resposta.
    """
    page = context.new_page()
    response = page.goto(url, wait_until=wait_until, timeout=config.NAV_TIMEOUT_MS)
    return page, response
