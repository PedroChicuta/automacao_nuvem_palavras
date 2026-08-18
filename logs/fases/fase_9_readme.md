# Fase 9 — README.md
**Data/Hora**: 2026-08-17T21:23:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Documentar o projeto com instruções de instalação, execução, estrutura e
descrição dos arquivos de saída.

## O que foi feito
- README.md cobrindo:
  - descrição do projeto e cargos alvo;
  - pré-requisitos (Python 3.10+, Chromium);
  - instalação (pip + playwright install);
  - uso: pipeline completo, smoke test, etapas isoladas, gerar_termos;
  - tabela de arquivos de saída (XLSX, CSV, termos, frequência);
  - lista das 17 colunas da planilha;
  - árvore de estrutura do projeto;
  - notas sobre stealth, rate limit, ética e retomabilidade.

## Arquivos criados/alterados
- `README.md` (novo) — documentação do projeto.

## Verificação
- Comando: leitura do arquivo (`wc -l`, conferência visual).
- Resultado: **pass**
- Evidência: 78 linhas, seções bem-formadas, blocos de código cercados por
  ``` corretamente, tabelas em formato GitHub-flavored markdown.

## Problemas encontrados
- Nenhum.

## Próxima fase
Fase 10: rodada completa + aceitação — executar o pipeline em modo completo
(20 vagas/cargo, MAX_PAGINAS=2) e verificar os critérios de aceitação do
`plan.md` §8 / `execution_plan.md`.
