"""Configurações centrais do projeto de scraping da Catho.

Centraliza slugs dos cargos, URLs, parâmetros de execução (MAX_PAGINAS, delays),
caminhos de arquivos e cabeçalhos/stealth do navegador. Todos os demais módulos
importam deste, de forma que ajustes de configuração ficam em um único lugar.
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos base do projeto
# ---------------------------------------------------------------------------
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = ROOT_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
LOGS_DIR: Path = ROOT_DIR / "logs"
FASE_LOGS_DIR: Path = LOGS_DIR / "fases"
SCRIPTS_DIR: Path = ROOT_DIR / "scripts"

# Arquivos de saída
XLSX_PATH: Path = DATA_DIR / "vagas_catho.xlsx"
CSV_PATH: Path = DATA_DIR / "vagas_catho.csv"
TERMOS_NUVEM_PATH: Path = DATA_DIR / "termos_para_nuvem.txt"
FREQUENCIA_TERMOS_PATH: Path = DATA_DIR / "frequencia_termos.csv"
RUNTIME_LOG_PATH: Path = LOGS_DIR / "scraping.log"

# ---------------------------------------------------------------------------
# Alvo da coleta
# ---------------------------------------------------------------------------
# Os três cargos da área de dados solicitados pela atividade.
# slug  : caminho na URL da Catho (https://www.catho.com.br/vagas/{slug}/?page={n})
# nome  : rótulo legível usado na coluna `cargo` da planilha.
CARGOS: list[dict[str, str]] = [
    {"slug": "cientista-de-dados", "nome": "Cientista de Dados"},
    {"slug": "engenheiro-de-dados", "nome": "Engenheiro de Dados"},
    {"slug": "analista-de-dados", "nome": "Analista de Dados"},
]

URL_BASE_LISTAGEM: str = "https://www.catho.com.br/vagas/{slug}/?page={pagina}"

# Escopo da coleta final (Fase 10): 15 vagas da pág 1 + 5 da pág 2 ≈ 20 vagas/cargo.
MAX_PAGINAS: int = 2

# Limite de vagas por cargo para os smoke tests das fases intermediárias.
SMOKE_PAGINAS: int = 1          # Fase 3: 1 página por cargo.
SMOKE_VAGAS_DETALHE: int = 5    # Fase 4: 5 vagas por cargo.

# ---------------------------------------------------------------------------
# Comportamento do navegador / delays (evitar bloqueio anti-bot)
# ---------------------------------------------------------------------------
HEADLESS: bool = False  # Catho retorna 403 em headless puro; headed é obrigatório.

USER_AGENT: str = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)
LOCALE: str = "pt-BR"
VIEWPORT: dict[str, int] = {"width": 1366, "height": 768}

# Delays (em segundos). Valores usados com `random.uniform(a, b)`.
DELAY_LISTAGEM_MIN: float = 2.0
DELAY_LISTAGEM_MAX: float = 5.0
DELAY_DETALHE_MIN: float = 3.0
DELAY_DETALHE_MAX: float = 7.0
PAUSA_A_CADA_N_VAGAS: int = 20
PAUSA_LONGA_MIN: float = 15.0
PAUSA_LONGA_MAX: float = 30.0

# Retry do detalhe
DETALHE_MAX_TENTATIVAS: int = 3
DETALHE_BACKOFF_BASE: float = 5.0  # 5s, 10s, 20s...

# Timeout de navegação (ms)
NAV_TIMEOUT_MS: int = 45000

# ---------------------------------------------------------------------------
# Checkpoints
# ---------------------------------------------------------------------------
def listagem_path(slug: str) -> Path:
    return RAW_DIR / f"listagem_{slug}.json"


def detalhe_path(slug: str) -> Path:
    return RAW_DIR / f"detalhe_{slug}.jsonl"


# Garante que os diretórios essenciais existem ao importar o módulo.
for _d in (DATA_DIR, RAW_DIR, LOGS_DIR, FASE_LOGS_DIR, SCRIPTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
