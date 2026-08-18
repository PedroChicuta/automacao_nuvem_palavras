# Fase 8 — scripts/gerar_termos.py
**Data/Hora**: 2026-08-17T21:22:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Tokenizar as descrições das vagas, remover stopwords PT-BR e ruído de
anúncios, contar frequência por cargo e global, e exportar
`data/frequencia_termos.csv` para alimentar a nuvem de palavras.

## O que foi feito
- Lista embutida de ~250 stopwords PT-BR (sem dependência de NLTK) cobrindo:
  - preposições, artigos, pronomes, conjugações comuns;
  - ruído específico de anúncios de vagas (com e sem acento): vaga, empresa,
    contrato, experiência, área, função, conhecimento, competência, etc.
- `tokenizar(texto)`: regex `[a-záàâãéêíóôõúçñ]+`, lowercase, descarta tokens
  ≤2 chars e stopwords.
- `_ler_descricoes_por_cargo()`: lê `data/vagas_catho.csv` e agrupa
  descrições por cargo.
- `gerar_frequencia(top)`: conta por cargo + global, ordena, escreve
  `data/frequencia_termos.csv` (colunas: `termo, cargo, frequencia`).
- CLI: `--top N` para limitar o top-N por cargo.

## Arquivos criados/alterados
- `scripts/gerar_termos.py` (novo) — tokenização, stopwords e frequência.

## Verificação
- Comando: `python scripts/gerar_termos.py` (sobre os 22 registros).
- Resultado: **pass**
- Evidência (top 10 global):
  ```
  dados: 142 | modelos: 45 | desenvolver: 32 | análise: 25 | sql: 24
  desenvolvimento: 23 | machine: 22 | learning: 21 | negócio: 21 | ciência: 20
  ```
- Evidência (top 8 por cargo — diferenciação clara):
  ```
  Cientista:  dados, modelos, machine, learning, ciência, análise, sql
  Engenheiro: dados, data, pipelines, engenharia, plataforma, desenvolvimento
  Analista:   dados, power, indicadores, relatórios, dashboards, análises
  ```
- CSV: 2277 linhas, 4 grupos (3 cargos + GLOBAL).

## Problemas encontrados
- **Stopwords sem acento não filtravam tokens acentuados**: "experiencia"
  na lista não casava com "experiência" no texto. Corrigido adicionando as
  versões acentuadas de todas as palavras de ruído (área/área, função/função,
  experiência/experiência, etc.). Re-rodado: top 10 agora sem ruído genérico.

## Próxima fase
Fase 9: `README.md` — instruções de instalação, execução e descrição dos
arquivos de saída.
