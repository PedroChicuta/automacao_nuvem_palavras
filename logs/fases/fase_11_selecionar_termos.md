# Fase 11 — scripts/selecionar_termos_nuvem.py
**Data/Hora**: 2026-08-18T00:00:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Tornar o processo de filtragem e seleção dos top-N termos por cargo (para
alimentação da nuvem de palavras) em um script Python reutilizável e
documentá-lo conforme a arquitetura do projeto.

## O que foi feito
- Criado `scripts/selecionar_termos_nuvem.py` — script reutilizável que:
  - Lê `data/frequencia_termos.csv` (gerado por `scripts/gerar_termos.py`).
  - Filtra ruído via `STOPWORDS_SELECAO` (~400 termos: benefícios, nomes de
    empresa, dias da semana, jargão de RH, boilerplate de vagas, endereços,
    etc.) — mantida separada das stopwords de tokenização para não poluir
    `gerar_termos.py`.
  - Pontua cada termo com: `score = peso_cargo * freq_cargo + peso_global * freq_global`
    (default: peso 2 para cargo, 1 para global), priorizando termos
    relevantes ao mercado e representativos do cargo.
  - Seleciona os top-N termos por cargo (default: 25).
  - Exporta `data/termos_selecionados.csv` (colunas: `termo, cargo, frequencia`).
  - CLI parametrizável: `--top`, `--peso-cargo`, `--peso-global`, `--freq-min`,
    `--saida`.
- Adicionado `TERMOS_SELECIONADOS_PATH` em `src/config.py` (centralização de
  caminhos conforme padrão do projeto).
- Atualizado `README.md`:
  - Seção "Uso" com instruções do novo script.
  - Tabela de arquivos de saída com `termos_selecionados.csv`.
  - Árvore de estrutura do projeto com o novo script.

## Arquivos criados/alterados
- `scripts/selecionar_termos_nuvem.py` (novo) — filtragem + seleção top-N.
- `src/config.py` (alterado) — adicionado `TERMOS_SELECIONADOS_PATH`.
- `README.md` (alterado) — documentação do novo script e arquivo de saída.
- `logs/fases/fase_11_selecionar_termos.md` (novo) — este log.

## Verificação
- Comando: `python scripts/selecionar_termos_nuvem.py --top 25`
- Resultado: **pass**
- Evidência (top 5 por cargo):
  ```
  Analista de Dados: dados(150), análise(43), sql(23), relatórios(30), desenvolvimento(15)
  Cientista de Dados: dados(207), modelos(79), análise(39), ciência(48), desenvolvimento(32)
  Engenheiro de Dados: dados(186), análise(11), engenharia(25), data(31), desenvolvimento(22)
  ```
- Diferenciação entre cargos preservada:
  - Analista → power, dashboards, indicadores, relatórios (BI/visualização)
  - Cientista → modelos, machine, learning, estatística (ML/estatística)
  - Engenheiro → pipelines, aws, arquitetura, engenharia (infra/pipelines)
- CSV gerado: 75 linhas (25 × 3 cargos), colunas `termo, cargo, frequencia`.

## Problemas encontrados
- **BOM + CRLF no CSV de entrada**: `frequencia_termos.csv` usa
  `utf-8-sig` (BOM) e CRLF. Corrigido abrindo com `encoding="utf-8-sig"` e
  `newline=""` (já era o padrão do `gerar_termos.py`).
- **Stopwords de seleção vs. tokenização**: a lista de stopwords de
  `gerar_termos.py` filtra ruído na tokenização, mas alguns termos de ruído
  sobrevivem (ex.: nomes de empresa, benefícios, dias da semana). Decidido
  manter uma lista separada `STOPWORDS_SELECAO` neste script para não
  alterar o comportamento do `gerar_termos.py` e preserve reusabilidade.

## Próxima fase
Não há próxima fase — o pipeline de scraping + geração de insumos + seleção
de termos está completo. Os entregáveis para `atividade.md` são:
1. `data/vagas_catho.xlsx` (planilha)
2. `data/frequencia_termos.csv` (frequência bruta)
3. `data/termos_selecionados.csv` (top-N filtrado para nuvem)
4. `assets/*.png` (nuvens de palavras por cargo)
