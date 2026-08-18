# Fase 4 — scraper_detalhe.py
**Data/Hora**: 2026-08-17T21:15:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Visitar cada URL de vaga (proveniente do checkpoint da listagem) e extrair os
campos do detalhe: título, descrição completa ("Sobre a vaga"), tipo de
contrato, horário, salário, empresa, modalidade — com retry e checkpoint
JSONL append-only retomável. Smoke: 5 vagas/cargo.

## O que foi feito
- `coletar_cargo(slug, nome, max_vagas)`: lê `listagem_{slug}.json`, filtra
  pendentes (IDs ausentes do `detalhe_{slug}.jsonl`), visita cada URL.
- Extração via JS injetado (`_EXTRACT_JS`) que:
  - localiza `h2 "Sobre a vaga"`;
  - percorre os irmãos do **pai** do h2 (o h2 está dentro de um `div.flex`
    de header com botão; o conteúdo é sibling do pai, não do h2);
  - separa a descrição (primeiro `<p>`) dos sub-labels `Tipo de contrato` e
    `Horário de trabalho` (próximos `<p class="font-bold">` + valor);
  - lê `Salário` e `Sobre a empresa` dos `div.sub_box`.
- `_detectar_modalidade`: regex sobre a descrição (remoto/híbrido/presencial).
- Retry 3x com backoff exponencial (5/10/20s) em falha/403; em falha final,
  registra a vaga com `descricao_completa=""` e flag `erro` (não perde o ID).
- Checkpoint JSONL append-only (`data/raw/detalhe_{slug}.jsonl`) — retomável.
- Merge dos campos da listagem (regiao, data_publicacao) quando o detalhe
  não traz o campo.
- CLI: `--smoke` (5 vagas), `--slug X`, default (todas).
- Delays humanizados (3–7s) + pausa longa a cada 20 vagas.
- Timestamp `data_coleta` em cada registro.

## Arquivos criados/alterados
- `src/scraper_detalhe.py` (novo) — scraper de detalhe com retry + checkpoint.
- `scripts/_probe_detalhe.py`, `_probe_detalhe2.py`, `_probe_detalhe3.py`
  (criados e removidos) — sondagens que mapearam a estrutura do DOM.

## Verificação
- Comando: `python -m src.scraper_detalhe --smoke` (5 vagas/cargo).
- Resultado: **pass**
- Evidência:
  ```
  detalhe_analista-de-dados.jsonl:  7 regs, 7 com descricao
  detalhe_cientista-de-dados.jsonl: 10 regs, 10 com descricao
  detalhe_engenheiro-de-dados.jsonl:  5 regs, 5 com descricao
  TOTAL: 22 regs, 22 com descricao
  ```
- Amostra de qualidade (cientista 37855388):
  - salario: 'A Combinar' | contrato: 'Prestador de serviços (PJ)'
  - horario: 'Período Integral' | desc_len: 1861
  - desc_preview: "Graduação em Estatística, Matemática, Ciência da
    Computação... Profundo domínio de estatística, modelagem e frameworks
    avançados de machine learning..."

## Problemas encontrados
- **Descrições vazias na 1ª execução**: o JS percorria `sobreHead.nextElementSibling`,
  que é um `BUTTON` (o h2 está num `div.flex` de header). Corrigido sondando
  o DOM (probe 3) e ajustando para percorrer `sobreHead.parentElement.nextElementSibling`.
  Validado re-rodando após limpar checkpoints: todas as 22 vagas com `desc=OK`.
- **Typo no path** ("websraping"): arquivo criado em diretório errado; movido
  para o local correto e diretório espúrio removido.
- **Timeout do bash (120s)**: a coleta de 15+ vagas com delays excede o
  timeout padrão. Contornado executando por cargo e com timeout maior.

## Próxima fase
Fase 5: `parser.py` — funções de limpeza de texto e parsing de salário
(extrair `salario_min`/`salario_max` numéricos de strings como "R$ 16.500").
