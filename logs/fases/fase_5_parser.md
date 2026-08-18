# Fase 5 — parser.py
**Data/Hora**: 2026-08-17T21:20:00Z  |  **Status**: concluída  |  **Commit**: pendente

## Objetivo
Implementar funções de parsing e limpeza dos dados extraídos, com foco em
`parse_salario` (converter texto de salário em `salario_min`/`salario_max`
numéricos) e `limpar_texto` (normalizar descrições longas).

## O que foi feito
- `parse_salario(texto)` → `(min, max)` em float:
  - `"A Combinar"` / sem "R$" → `(None, None)`;
  - `"R$ 16.500 Benefícios..."` → `(16500.0, 16500.0)` (valor único);
  - `"A partir de R$ 5.000,00"` → `(5000.0, None)` (só mínimo);
  - `"Até R$ 5.000"` → `(None, 5000.0)` (só máximo);
  - `"R$ 5.000 a R$ 8.000"` → `(5000.0, 8000.0)` (faixa);
  - conversão de número BRL ("." = milhar, "," = decimal).
- `limpar_salario(texto)` → corta em "Benefícios" / "+ N benefícios",
  devolvendo só a parte do salário.
- `limpar_texto(texto)` → normaliza `\r\n`, colapsa espaços/tabulações,
  limita quebras de linha consecutivas a 2, remove espaço antes de pontuação.
- Self-test embutido (`python -m src.parser`) com 7 casos de salário
  cobrindo todos os formatos observados nos dados reais.

## Arquivos criados/alterados
- `src/parser.py` (novo) — parsing de salário e limpeza de texto.

## Verificação
- Comando: `python -m src.parser` (self-test com 7 casos).
- Resultado: **pass**
- Evidência:
  ```
  [OK] 'A Combinar'                              -> (None, None)
  [OK] 'A Combinar + 3 benefícios'               -> (None, None)
  [OK] 'A Combinar Benefícios Tíquete refeição'  -> (None, None)
  [OK] 'R$ 16.500 Benefícios Seguro saúde'       -> (16500.0, 16500.0)
  [OK] 'R$ 5.000 Benefícios Assistência médica'  -> (5000.0, 5000.0)
  [OK] 'A partir de R$ 5.000,00 Benefícios'      -> (5000.0, None)
  [OK] 'R$ 16.000 Benefícios Assistência médica' -> (16000.0, 16000.0)
  limpar_salario('R$ 16.500 Benefícios Seguro') = 'R$ 16.500'
  ```
- Casos derivados dos formatos reais observados nos 22 registros das fases
  3–4 (11× "A Combinar", 5× "R$ X.YYY Benefícios...", 1× "A partir de...").

## Problemas encontrados
- Nenhum. Os formatos foram mapeados inspecionando os dados reais antes de
  escrever o parser, então todos os casos de teste passaram de primeira.

## Próxima fase
Fase 6: `storage.py` — ler os `detalhe_*.jsonl`, consolidar com
`listagem_*.json`, aplicar `parser.parse_salario`/`limpar_texto`, e exportar
`vagas_catho.xlsx` + `.csv` + `termos_para_nuvem.txt`.
