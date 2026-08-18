# Plano de Execução — Web Scraping Catho

> Plano operacional derivado de `plan.md`. Define o workflow automático fase-a-fase,
> com commit e log a cada fase.

## Workflow por fase (idêntico, automático)

1. **Implementar** a fase.
2. **Verificar** com comando explícito (smoke test).
3. **Escrever** `logs/fases/fase_N_<nome>.md` (template abaixo).
4. **Commit** em `master`: `<tipo>: <descrição> (fase N/10)`.
5. **Avançar** para a próxima fase automaticamente.

### Em falha
- Até 2 tentativas de correção dentro da fase.
- Se persistir: log `status=falha`, commit do parcial, **abortar** e reportar.

## Decisões consolidadas

- **Branch**: `master` (repo vazio, sem commits prévios).
- **Validação ao vivo (smoke test)**:
  - Fase 2: 1 request → HTTP 200.
  - Fase 3: 1 página por cargo.
  - Fase 4: 5 vagas por cargo.
- **Escopo Fase 10**: 20 vagas/cargo = 15 da pág 1 + 5 da pág 2 → `MAX_PAGINAS=2`
  (~60 vagas totais).
- **Falha**: abortar e reportar após 2 tentativas.

## Fases

| # | Fase | Entregáveis | Verificação (smoke) |
|---|------|------------|---------------------|
| 0 | Setup & bootstrap | `src/`, `data/raw`, `logs/fases/`, `scripts/`, `src/__init__.py`; `requirements.txt` (+pandas, openpyxl); deps instaladas | `python -c "import pandas, openpyxl, playwright"` |
| 1 | `config.py` | slugs (3 cargos), `MAX_PAGINAS=2`, delays, paths, URLs base | `python -c "from src import config; print(len(config.CARGOS))"` → 3 |
| 2 | `browser.py` | factory stealth (headed + UA real + webdriver oculto) | abrir 1 URL Catho → HTTP 200 |
| 3 | `scraper_listagem.py` | coleta URLs + checkpoint JSON | rodar 1 pág/cargo → JSON com ≥15 vagas/cargo |
| 4 | `scraper_detalhe.py` | detalhe + retry 3x + checkpoint JSONL | rodar 5 vagas/cargo → 15 registros com descrição |
| 5 | `parser.py` | limpeza texto + parse salário → min/max | unit checks em 3 amostras |
| 6 | `storage.py` | consolida jsonl → `vagas_catho.xlsx` + `.csv` + `termos_para_nuvem.txt` | gerar planilha dos dados da fase 4 |
| 7 | `pipeline.py` | orquestrador listagem→detalhe→planilha | `python -m src.pipeline --help` |
| 8 | `scripts/gerar_termos.py` | stopwords PT-BR + `frequencia_termos.csv` | rodar sobre dados da fase 4 |
| 9 | `README.md` | instruções de execução | markdown lint / leitura |
| 10 | Rodada completa + aceitação | pipeline completo (20 vagas/cargo) + checklist `plan.md` §8 | critérios de aceitação ✓ |

## Template do log por fase

```markdown
# Fase N — <Nome>
**Data/Hora**: <ISO>  |  **Status**: concluída | falha | parcial  |  **Commit**: <hash>

## Objetivo
<1-2 linhas>

## O que foi feito
- <item>

## Arquivos criados/alterados
- <path> (novo|alterado) — <resumo>

## Verificação
- Comando: `<cmd>`
- Resultado: pass|fail
- Evidência: <output resumido>

## Problemas encontrados
- <nenhum | descrição + como foi tratado>

## Próxima fase
Fase N+1: <nome>
```

## Critérios de aceitação finais (Fase 10)

Planilha `data/vagas_catho.xlsx` com:
- [ ] 3 cargos representados (≥20 vagas cada).
- [ ] Colunas `cargo/url_vaga/titulo_vaga/empresa/descricao_completa/requisitos/salario` preenchidas.
- [ ] `data/termos_para_nuvem.txt` gerado.
- [ ] `data/frequencia_termos.csv` gerado.
- [ ] `logs/scraping.log` sem erros fatais.
- [ ] Pipeline retomável (rodar 2x continua de onde parou).
