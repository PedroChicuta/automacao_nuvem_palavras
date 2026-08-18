# Fase 0 — Setup & bootstrap
**Data/Hora**: 2026-08-17T21:05:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Criar a estrutura de pastas do projeto, atualizar `requirements.txt` e instalar as
dependências necessárias para o desenvolvimento das fases seguintes.

## O que foi feito
- Criada a árvore de diretórios do projeto: `src/`, `data/raw/`, `logs/fases/`, `scripts/`.
- Criado `src/__init__.py` tornando `src` um pacote Python importável.
- Atualizado `requirements.txt` adicionando `pandas` e `openpyxl`.
- Criado `.gitignore` para não versionar `venv/`, `__pycache__/`, checkpoints em
  `data/raw/`, logs de runtime (`*.log`) e planilhas geradas (regeneráveis).
- Instaladas as novas dependências no `venv` existente: `pandas 3.0.5`, `openpyxl 3.1.5`
  (já havia `playwright 1.62.0`).
- Escrito o `execution_plan.md` consolidando o workflow fase-a-fase.

## Arquivos criados/alterados
- `src/` (novo) — pacote Python do projeto.
- `src/__init__.py` (novo) — marca `src` como pacote.
- `data/raw/` (novo) — destino dos checkpoints JSON/JSONL.
- `logs/fases/` (novo) — destino dos logs de fase (este arquivo).
- `scripts/` (novo) — scripts auxiliares (ex.: gerar_termos.py na fase 8).
- `requirements.txt` (alterado) — adicionados pandas e openpyxl.
- `.gitignore` (novo) — ignora venv, caches, checkpoints e artefatos regeneráveis.
- `execution_plan.md` (novo) — plano operacional fase-a-fase.

## Verificação
- Comando: `python -c "import pandas, openpyxl, playwright; ..."`
- Resultado: **pass**
- Evidência: `OK pandas 3.0.5 | openpyxl 3.1.5 | playwright 1.62.0`

## Problemas encontrados
- `playwright` não expõe `__version__` como atributo de módulo; ajustado para usar
  `importlib.metadata.version('playwright')`. Sem impacto no projeto.

## Próxima fase
Fase 1: `config.py` — centralização de slugs, MAX_PAGINAS, delays e paths.
