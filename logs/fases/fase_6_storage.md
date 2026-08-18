# Fase 6 — storage.py
**Data/Hora**: 2026-08-17T21:20:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Consolidar os `detalhe_*.jsonl` em uma planilha estruturada (XLSX + CSV)
aplicando parsing de salário e limpeza de texto, e gerar o insumo de termos
para a nuvem de palavras.

## O que foi feito
- `consolidar()`: lê todos os `detalhe_{slug}.jsonl`, normaliza cada registro
  para o schema de 17 colunas do `plan.md` §4, dedupe por `id_vaga`.
- `_normalizar(reg)`: aplica `parser.limpar_salario` (corta benefícios),
  `parser.parse_salario` → `salario_min`/`salario_max`, e
  `parser.limpar_texto` na descrição.
- `exportar(df)`: salva `data/vagas_catho.xlsx` (openpyxl) e
  `data/vagas_catho.csv` (UTF-8 com BOM para Excel).
- `gerar_termos_nuvem(df)`: gera `data/termos_para_nuvem.txt` com blocos por
  cargo (`# CARGO: <nome>` + descrições concatenadas) — serve para nuvem
  global ou por cargo.
- `main()`: orquestra consolidação → exportação → termos, com resumo por
  cargo no log (vagas / com descrição / com salário).
- Schema final: `cargo, url_vaga, id_vaga, titulo_vaga, empresa, salario,
  salario_min, salario_max, regiao, modalidade, tipo_contrato, horario,
  descricao_completa, requisitos, habilidades, data_publicacao, data_coleta`.
  (Na Catho, requisitos/habilidades estão embutidos na descrição, por isso
  essas colunas ficam vazias mas presentes para conformidade do schema.)

## Arquivos criados/alterados
- `src/storage.py` (novo) — consolidação, exportação XLSX/CSV e termos.

## Verificação
- Comando: `python -m src.storage` (sobre os 22 registros das fases 3–4).
- Resultado: **pass**
- Evidência:
  ```
  exportado: data/vagas_catho.xlsx (22 linhas)
  exportado: data/vagas_catho.csv
  termos para nuvem: data/termos_para_nuvem.txt (3 cargos, 22 vagas)
  Resumo por cargo:
    Analista de Dados:  7 vagas | 7 com desc | 2 com salario
    Cientista de Dados: 10 vagas | 10 com desc | 3 com salario
    Engenheiro de Dados: 5 vagas | 5 com desc | 0 com salario
  ```
- Inspeção do XLSX: 22×17, `salario_min/max` parseados corretamente
  (16500.0, 5000.0, NaN p/ "A Combinar"), `tipo_contrato` preenchido
  (CLT, PJ, Cooperado, Temporário).

## Problemas encontrados
- Nenhum. `modalidade` ficou majoritariamente NaN (só 1 "Remoto") porque as
  descrições nem sempre usam literalmente "remoto/híbrido/presencial"; isso
  é esperado e aceitável — a nuvem de palavras usará a descrição completa.

## Próxima fase
Fase 7: `pipeline.py` — orquestrador que executa listagem → detalhe →
consolidação em um único comando, com suporte a `--smoke` e `--help`.
