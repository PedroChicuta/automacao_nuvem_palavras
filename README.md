# Web Scraping de Vagas da Catho

Coleta automatizada de vagas da área de dados publicadas no site
[ Catho ](https://www.catho.com.br) para os cargos de **Cientista de Dados**,
**Engenheiro de Dados** e **Analista de Dados**, gerando uma planilha
estruturada e insumos para nuvem de palavras.

## Pré-requisitos

- Python 3.10+
- Navegador Chromium (instalado via Playwright)
- Ambiente virtual (recomendado)

## Instalação

```bash
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Uso

### Pipeline completo (coleta + planilha)

```bash
python -m src.pipeline
```

Coleta 2 páginas de listagem por cargo (~20 vagas/cargo) + detalhe de cada
vaga + geração da planilha e termos. É **retomável**: re-executar continua de
onde parou (checkpoints em `data/raw/`).

### Smoke test (validação rápida)

```bash
python -m src.pipeline --smoke
```

1 página de listagem + 5 vagas de detalhe por cargo.

### Executar etapas isoladas

```bash
python -m src.pipeline --only lista     # só listagem (URLs)
python -m src.pipeline --only detalhe   # só detalhe (visita cada vaga)
python -m src.pipeline --only gera      # só consolida planilha + termos
```

### Gerar frequência de termos (para nuvem de palavras)

```bash
python scripts/gerar_termos.py            # todos os termos
python scripts/gerar_termos.py --top 50   # top 50 por cargo
```

### Selecionar termos para a nuvem de palavras

A partir do `frequencia_termos.csv`, seleciona os top-N termos por cargo
combinando frequência no cargo com frequência global (prioriza termos
relevantes ao mercado e representativos do cargo), filtrando ruído
(benefícios, nomes de empresa, jargão de RH, etc.).

```bash
python scripts/selecionar_termos_nuvem.py                         # top 25 (default)
python scripts/selecionar_termos_nuvem.py --top 30                # top 30 por cargo
python scripts/selecionar_termos_nuvem.py --peso-cargo 3          # peso 3x no cargo
python scripts/selecionar_termos_nuvem.py --freq-min 5            # freq mínima 5 no cargo
```

## Arquivos de saída

| Arquivo | Descrição |
|---------|-----------|
| `data/vagas_catho.xlsx` | Planilha principal (uma linha por vaga, 17 colunas) |
| `data/vagas_catho.csv` | Espelho CSV (UTF-8 com BOM, abre no Excel) |
| `data/termos_para_nuvem.txt` | Descrições concatenadas por cargo (para wordcloud.online) |
| `data/frequencia_termos.csv` | Frequência de termos por cargo e global (`termo, cargo, frequencia`) |
| `data/termos_selecionados.csv` | Top-N termos por cargo filtrados e pontuados (para nuvem de palavras) |

### Colunas da planilha

`cargo, url_vaga, id_vaga, titulo_vaga, empresa, salario, salario_min,
salario_max, regiao, modalidade, tipo_contrato, horario, descricao_completa,
requisitos, habilidades, data_publicacao, data_coleta`

## Estrutura do projeto

```
src/
├── config.py            # slugs, delays, paths, configurações stealth
├── browser.py           # factory do navegador Playwright (modo stealth)
├── scraper_listagem.py  # coleta URLs da listagem + checkpoint
├── scraper_detalhe.py   # visita cada vaga + checkpoint JSONL
├── parser.py            # parse de salário BRL + limpeza de texto
├── storage.py           # consolida JSONL em XLSX/CSV + termos
└── pipeline.py          # orquestra listagem → detalhe → planilha
scripts/
├── gerar_termos.py          # tokenização + stopwords + frequência
└── selecionar_termos_nuvem.py # filtragem + seleção top-N por cargo
data/raw/                # checkpoints (gitignored)
logs/
├── scraping.log         # log de execução
└── fases/               # logs de desenvolvimento por fase
```

## Notas

- **Stealth**: a Catho bloqueia (HTTP 403) requisições headless puras. O
  navegador é aberto em modo headed com User-Agent real e
  `navigator.webdriver` oculto.
- **Rate limit**: delays humanizados (2–7s) entre páginas/vagas, pausa longa
  a cada 20 vagas.
- **Ética**: coleta apenas dados publicamente visíveis, sem login, sem
  acessar conteúdo exclusivo de assinantes.
- **Retomável**: checkpoints em `data/raw/` permitem interromper e retomar.
