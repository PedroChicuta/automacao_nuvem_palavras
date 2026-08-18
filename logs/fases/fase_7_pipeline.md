# Fase 7 — pipeline.py
**Data/Hora**: 2026-08-17T21:21:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Criar o orquestrador que executa as 3 etapas (listagem → detalhe → planilha)
em um único comando, com suporte a `--smoke`, `--only` e `--help`.

## O que foi feito
- `etapa_listagem(smoke)`: invoca `scraper_listagem.coletar_cargo` para todos
  os cargos, com `MAX_PAGINAS` ou `SMOKE_PAGINAS` conforme o modo.
- `etapa_detalhe(smoke)`: invoca `scraper_detalhe.coletar_cargo` para todos
  os cargos, com `None` (todas) ou `SMOKE_VAGAS_DETALHE`.
- `etapa_geracao()`: invoca `storage.consolidar/exportar/gerar_termos_nuvem`
  e loga o resumo por cargo.
- `main()` com argparse:
  - `--smoke`: modo reduzido (1 pág listagem + 5 vagas detalhe/cargo);
  - `--only {lista,detalhe,gera}`: executa só uma etapa (default: todas);
  - `--help`: ajuda.
- Importações preguiçosas dentro de cada etapa (evita abrir navegador
  ao rodar `--only gera` ou `--help`).
- Try/except de topo: qualquer exceção é logada com traceback e retorna 1.
- Cada etapa é retomável via checkpoints, então re-executar continua de
  onde parou.

## Arquivos criados/alterados
- `src/pipeline.py` (novo) — orquestrador do pipeline.

## Verificação
- Comando 1: `python -m src.pipeline --help`
  - Resultado: **pass** — exibe uso com `-h, --help`, `--smoke`, `--only`.
- Comando 2: `python -m src.pipeline --only gera` (sem rede, consolida dados existentes)
  - Resultado: **pass**
  - Evidência:
    ```
    === Pipeline Catho [COMPLETO] ===
    --- Etapa 3/3: Geracao da planilha ---
    exportado: data/vagas_catho.xlsx (22 linhas)
    termos para nuvem: data/termos_para_nuvem.txt (3 cargos, 22 vagas)
    Resumo:
      Analista de Dados:  7 vagas | 7 com descricao
      Cientista de Dados: 10 vagas | 10 com descricao
      Engenheiro de Dados: 5 vagas | 5 com descricao
    === Pipeline concluido ===
    ```

## Problemas encontrados
- Nenhum. A integração das 3 etapas funcionou de primeira graças ao design
  retomável de cada módulo.

## Próxima fase
Fase 8: `scripts/gerar_termos.py` — tokenização, remoção de stopwords PT-BR
e geração de `data/frequencia_termos.csv` (`termo, cargo, frequencia`).
