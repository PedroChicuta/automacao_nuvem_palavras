# Plano: Web Scraping de Vagas da Catho para Cargos da Área de Dados

> Objetivo: coletar, de forma automatizada, os dados das vagas publicadas no site
> `https://www.catho.com.br` para três cargos da área de dados e gerar uma planilha
> estruturada que sirva de insumo para a atividade descrita em `atividade.md`
> (nuvem de palavras + análise comparativa entre os três perfis profissionais).

---

## 1. Contexto e Escopo

### 1.1 O que a atividade pede
Conforme `atividade.md`, é necessário:

1. Baixar dados do site Catho e gerar uma **planilha** com: requisitos, conhecimentos
   técnicos, ferramentas, linguagens, competências, salário e habilidades associados
   aos cargos.
2. Organizar os termos e gerar uma **nuvem de palavras** (ex.: wordcloud.online/pt).
3. Analisar a nuvem respondendo a 4 perguntas (termos mais recorrentes, conhecimentos
   comuns aos três cargos, competências específicas de cada cargo, o que a frequência
   revela sobre semelhanças/diferenças).
4. Usar a visualização para identificar padrões do mercado de dados e como os três
   cargos se relacionam.

### 1.2 Os três cargos
A atividade fala em "três cargos" da "área de dados". Os três perfis clássicos do
mercado brasileiro são:

| # | Cargo                 | Path na Catho (slug)        |
|---|-----------------------|-----------------------------|
| 1 | Cientista de Dados    | `cientista-de-dados`        |
| 2 | Engenheiro de Dados   | `engenheiro-de-dados`       |
| 3 | Analista de Dados     | `analista-de-dados`         |

URL base: `https://www.catho.com.br/vagas/{slug}/?page={n}`

> Observação: o `atividade.md` cita apenas a URL de *cientista-de-dados*. Os outros
> dois slugs serão confirmados acessando as páginas antes de iniciar o scraping
> definitivo. Se algum slug não existir, busca-se o mais próximo (ex.:
> `analista-de-dados-junior`).

---

## 2. Diagnóstico do Site (levantamento já realizado)

- **Bloqueio anti-bot**: requisição headless "pura" retorna **HTTP 403 Forbidden**.
  Com `headless=False` + User-Agent real + `navigator.webdriver` oculto +
  `--disable-blink-features=AutomationControlled`, o site retorna **HTTP 200** e
  renderiza o conteúdo normalmente.
- **Renderização client-side**: a listagem depende de JavaScript => uso obrigatório
  de navegador (Playwright), não basta `requests`/`BeautifulSoup`.
- **Estrutura da listagem**:
  - ~20 `<article>` por página (vagas).
  - Links de detalhe no formato `https://www.catho.com.br/vagas/{slug}/{id_vaga}`.
  - Há paginação via `?page={n}`.
- **Detalhes da vaga** (salário, descrição, requisitos) ficam na **página de
  detalhe**, não no card da listagem => é necessário visitar cada vaga.

### 2.1 Implicações
- Precisamos de navegador real (Playwright) em modo **headed** (não headless).
- Precisamos de **delays** e rotação de comportamento para não sermos bloqueados.
- Precisamos de **cache/restart** para retomar em caso de queda (o scraping de
  detalhe é a parte mais lenta: 1 req por vaga).

---

## 3. Stack Tecnológica

| Camada              | Tecnologia            | Motivo                                        |
|---------------------|-----------------------|-----------------------------------------------|
| Navegador automation| Playwright (já no env)| Renderiza JS, dá stealth, já instalado        |
| Parsing             | Seletores Playwright  | Evita depender de BS4; o HTML vem pronto      |
| Dados tabulares     | `pandas`              | Montar e exportar a planilha                  |
| Planilha            | `.xlsx` (openpyxl) + `.csv` | Compatível com Excel/LibreOffice        |
| Resumo/nuvem        | `collections.Counter` | Contagem de termos para a nuvem               |
| Config/Logs         | `logging`, `json`     | Rastreabilidade e checkpoint                  |

### 3.1 Dependências a adicionar ao `requirements.txt`
```
playwright==1.62.0
pandas
openpyxl
```
(`pandas` e `openpyxl` serão instalados no `venv` já existente.)

---

## 4. Modelo de Dados (campos da planilha)

Cada linha da planilha = **uma vaga**. Colunas:

| Campo               | Descrição                                           | Origem                |
|---------------------|-----------------------------------------------------|-----------------------|
| `cargo`             | cientista/engenheiro/analista de dados              | query param           |
| `url_vaga`          | URL canônica da vaga                                | listagem              |
| `id_vaga`           | ID numérico da Catho                                | URL                   |
| `titulo_vaga`       | Título completo anunciado                           | detalhe               |
| `empresa`           | Nome da empresa                                     | detalhe               |
| `salario`           | Faixa salarial (texto bruto)                        | detalhe               |
| `salario_min`       | Valor mínimo (numérico, se parseable)              | derivado              |
| `salario_max`       | Valor máximo (numérico, se parseable)              | derivado              |
| `regiao`            | Cidade/Estado                                       | detalhe               |
| `modalidade`        | Presencial/Híbrido/Remoto                           | detalhe               |
| `tipo_contrato`     | CLT/PJ/Estágio etc.                                 | detalhe               |
| `descricao_completa`| Texto completo da descrição                         | detalhe               |
| `requisitos`        | Texto da seção de requisitos                        | detalhe               |
| `habilidades`       | Lista de habilidades (se houver tag)               | detalhe               |
| `data_publicacao`   | Data do anúncio (se disponível)                     | detalhe               |
| `data_coleta`       | Timestamp da coleta                                 | sistema               |

> **Importante**: o foco da atividade são *requisitos, conhecimentos técnicos,
> ferramentas, linguagens, competências, salário e habilidades*. Boa parte virá
> dentro de `descricao_completa` + `requisitos` em texto livre. A nuvem de palavras
> será gerada a partir da concatenação desses campos de texto.

---

## 5. Estrutura do Projeto

```
webscraping/
├── atividade.md            # enunciado (já existe)
├── plan.md                 # este plano
├── requirements.txt        # deps
├── README.md               # como executar
├── src/
│   ├── __init__.py
│   ├── config.py           # slugs, nº de páginas, delays, paths
│   ├── browser.py          # factory do navegador stealth (Playwright)
│   ├── scraper_listagem.py # coleta lista de vagas (URLs + metadados básicos)
│   ├── scraper_detalhe.py  # visita cada vaga e extrai campos do detalhe
│   ├── parser.py           # funções de parsing/limpeza de texto e salário
│   ├── storage.py          # salva CSV/XLSX + checkpoint JSON
│   └── pipeline.py         # orquestra listagem -> detalhe -> planilha
├── data/
│   ├── raw/                # checkpoint de URLs coletadas por cargo
│   ├── vagas_catho.xlsx    # planilha final
│   └── vagas_catho.csv     # espelho CSV
├── logs/
│   └── scraping.log
└── scripts/
    └── gerar_termos.py     # consolida termos p/ nuvem de palavras (opcional)
```

---

## 6. Estratégia de Scraping (passo a passo)

### 6.1 Fase 0 — Preparação
- [ ] Confirmar os 3 slugs abrindo cada URL manualmente e checar HTTP 200.
- [ ] Instalar `pandas` e `openpyxl` no venv.
- [ ] Criar a estrutura de pastas acima.

### 6.2 Fase 1 — Navegador stealth (`browser.py`)
Configurações essenciais (validadas no diagnóstico):
- `headless=False` (necessário para passar pelo 403).
- `args=['--disable-blink-features=AutomationControlled']`.
- Contexto com `user_agent` real, `locale='pt-BR'`, `viewport` desktop.
- `add_init_script` removendo `navigator.webdriver`.
- Função `criar_navegador()` retorna `(playwright, browser, context)`.

### 6.3 Fase 2 — Coleta da listagem (`scraper_listagem.py`)
Para cada cargo, paginar `?page=1..N`:
- Abrir a URL, aguardar `domcontentloaded` + sleep aleatório (2–5s).
- Selecionar todos os `article` / links `/vagas/{slug}/{id}`.
- Extrair: `id_vaga`, `url_vaga`, `cargo`, `titulo_resumo`, `empresa_resumo`,
  `salario_resumo` (se vier no card).
- Salvar incrementalmente em `data/raw/listagem_{cargo}.json` (checkpoint).
- **Detecção de fim**: página sem novos `<article>` ou botão "próxima" ausente.
- **Limite configurável** (`config.MAX_PAGINAS`) para evitar rodadas infinitas.

### 6.4 Fase 3 — Coleta do detalhe (`scraper_detalhe.py`)
Para cada `url_vaga` ainda não visitada (lê checkpoint):
- Abrir a URL, aguardar conteúdo.
- Extrair os campos da tabela do §4 do bloco de detalhe.
- **Retry**: até 3 tentativas com backoff exponencial em caso de 403/timeout.
- **Checkpoint**: a cada vaga, append em `data/raw/detalhe_{cargo}.jsonl`.
- **Delay humano**: 3–7s aleatório entre vagas; pausa maior a cada 20 vagas.

### 6.5 Fase 4 — Consolidação (`storage.py` + `pipeline.py`)
- Ler todos os `detalhe_*.jsonl`.
- Cruzar com `listagem_*.json`.
- Montar `DataFrame` pandas com as colunas do §4.
- Normalizar salário (`parser.parse_salario`) -> `salario_min/max`.
- Exportar:
  - `data/vagas_catho.xlsx` (planilha principal).
  - `data/vagas_catho.csv` (espelho).
- Salvar `data/termos_para_nuvem.txt` (concatenação de `requisitos` +
  `descricao_completa` + `habilidades` por cargo) para uso na nuvem de palavras.

### 6.6 Fase 5 — Termos para nuvem (`scripts/gerar_termos.py`, opcional)
- Tokenizar o texto, remover stopwords PT-BR, remover pontuação.
- Contar frequência por cargo e global.
- Exportar `data/frequencia_termos.csv` (`termo, cargo, frequencia`).
- Esse CSV pode ser colado em wordcloud.online/pt ou usado com `wordcloud` Python.

---

## 7. Boas Práticas e Mitigação de Riscos

| Risco                          | Mitigação                                              |
|--------------------------------|--------------------------------------------------------|
| Bloqueio 403 anti-bot          | Navegador headed + stealth (já validado)               |
| Bloqueio por frequência        | Delays aleatórios, pausas a cada N vagas, user-agent   |
| Layout mudar                   | Seletores isolados em `config.py`; fallbacks por texto |
| Queda no meio                  | Checkpoint JSONL por vaga; retomável                   |
| Vagas duplicadas               | Dedupe por `id_vaga`                                   |
| Conteúdo atrás de login        | Verificar; se bloqueado, registrar e pular (não login) |
| Lentidão (1 req/vaga)          | Paralelismo limitado/sequencial p/ não quebrar stealth |
| Termos poluídos na nuvem       | Stopwords PT-BR + lista customizada de ruído           |
| Ética/Legal                    | Apenas dados públicos; rate-limit respeitoso; sem login|

> **Decisão de ética**: não faremos login nem acessaremos conteúdo exclusivo de
> assinantes. Coletaremos apenas o que é publicamente visível. O scraping será
> throttled para não impactar o site.

---

## 8. Critérios de Aceitação

A planilha `data/vagas_catho.xlsx` estará pronta quando:
- [ ] Contiver registros para os **3 cargos** (coluna `cargo` preenchida).
- [ ] Cada linha tiver ao menos: `cargo`, `url_vaga`, `titulo_vaga`, `empresa`,
      `descricao_completa`/`requisitos` e `salario` (quando informado pela vaga).
- [ ] `data/termos_para_nuvem.txt` existir e conter texto concatenado por cargo.
- [ ] `data/frequencia_termos.csv` existir com `termo,cargo,frequencia`.
- [ ] Log em `logs/scraping.log` sem erros fatais (403 pontuais com retry OK).
- [ ] Script retomável: rodar 2x continua de onde parou.

---

## 9. Como Executar (preview p/ README futuro)

```bash
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium       # já instalado, mas garantido
python -m src.pipeline            # roda listagem + detalhe + planilha
# ou em fases:
python -m src.scraper_listagem    # só URLs
python -m src.scraper_detalhe     # só detalhe (retomável)
python -m src.storage             # só consolida planilha
python scripts/gerar_termos.py    # só termos p/ nuvem
```

---

## 10. Ordem de Implementação (roadmap)

1. **Config + estrutura de pastas** (`config.py`, dirs `data/`, `logs/`).
2. **`browser.py`** com factory stealth (já provado contra o 403).
3. **`scraper_listagem.py`** + checkpoint — validar coletando ~1 página/cargo.
4. **`scraper_detalhe.py`** + retry + checkpoint — validar com 5 vagas.
5. **`parser.py`** (limpeza de texto + parse de salário).
6. **`storage.py`** (consolidação + export XLSX/CSV).
7. **`pipeline.py`** (orquestração completa).
8. **`scripts/gerar_termos.py`** (termos para nuvem).
9. **`README.md`** com instruções.
10. **Rodada completa** + checagem dos critérios de aceitação.

---

## 11. Entregáveis da Atividade (pós-scraping)

Após o scraping, para fechar `atividade.md`:
1. Planilha `data/vagas_catho.xlsx`.
2. Nuvem de palavras (gerar em wordcloud.online/pt a partir de
   `data/termos_para_nuvem.txt` ou via Python `wordcloud`).
3. Respostas às 4 perguntas (a serem escritas em um relatório `relatorio.md`
   após análise da nuvem) — **fora do escopo deste plano**, que cobre só o
   scraping e a geração dos insumos.
