"""Gera `data/frequencia_termos.csv` a partir da planilha de vagas.

Lê `data/vagas_catho.csv`, tokeniza as descricoes completas, remove stopwords
PT-BR e ruido, conta frequencia por cargo e global, e exporta
`data/frequencia_termos.csv` (colunas: termo, cargo, frequencia).

Uso:
    python scripts/gerar_termos.py
    python scripts/gerar_termos.py --top 30   # so top 30 termos por cargo
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

# Adiciona a raiz do projeto ao path para importar src.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402

logger = logging.getLogger("gerar_termos")

# ---------------------------------------------------------------------------
# Stopwords PT-BR (lista embutida — sem dependencia de NLTK)
# ---------------------------------------------------------------------------
STOPWORDS_PT: set[str] = {
    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "nao",
    "uma", "os", "as", "dos", "das", "pelo", "pela", "aos", "pelas", "pelos",
    "no", "na", "nos", "nas", "se", "por", "ao", "as", "aos", "mais", "menos",
    "que", "ou", "mas", "como", "quando", "onde", "porque", "entao", "ja",
    "ainda", "tambem", "sem", "sob", "sobre", "apos", "antes", "depois",
    "entre", "ate", "contra", "desde", "durante", "mediante", "perante",
    "tras", "afora", "alem", "ceu", "este", "esta", "estes", "estas",
    "esse", "essa", "esses", "essas", "aquele", "aquela", "aqueles", "aquelas",
    "isto", "isso", "aquilo", "seu", "sua", "seus", "suas", "meu", "minha",
    "meus", "minhas", "nosso", "nossa", "nossos", "nossas", "dele", "dela",
    "deles", "delas", "deste", "desta", "desses", "dessas", "disto", "disso",
    "aqui", "ali", "la", "ca", "so", "muito", "muitos", "muita", "muitas",
    "pouco", "poucos", "tudo", "nada", "algo", "alguem", "ninguem", "todo",
    "todos", "toda", "todas", "cada", "outro", "outra", "outros", "outras",
    "mesmo", "mesma", "mesmos", "mesmas", "proprio", "propria", "tais",
    "qual", "quais", "cujo", "cuja", "cujos", "cujas", "quem", "cujo",
    "ser", "era", "sao", "foram", "sera", "serao", "tem", "tinha", "tem",
    "ter", "terao", "teria", "teriam", "haver", "havia", "ha", "houver",
    "pode", "poder", "poderia", "poderiam", "deve", "devem", "devia",
    "fazer", "faz", "fez", "faria", "fariam", "ir", "vai", "foi", "ira",
    "estao", "estavam", "estava", "estar", "tenha", "tenham", "tivesse",
    "tivessem", "caso", "seja", "sejam", "embora", "todavia", "contudo",
    "entretanto", "porem", "assim", "logo", "portanto", "por isso", "nem",
    "tanto", "quanto", "tal", "tao", "sempre", "nunca", "agora", "hoje",
    "sera", "apos", "atraves", "dba", "das", "aos", "as", "aos",
    # Ruido especifico de anuncios de vagas (com e sem acento)
    "vaga", "vagas", "beneficios", "beneficio", "benefícios", "benefício",
    "empresa", "contrato", "experiencia", "experiência", "area", "área",
    "areas", "áreas", "cargo", "funcao", "função", "funcoes", "funções",
    "trabalho", "trabalhar", "atuar", "atuacao", "atuação", "perfil",
    "desejavel", "desejável", "obrigatorio", "obrigatório",
    "requisitos", "requisito", "habilidades", "habilidade",
    "competencias", "competências", "competencia", "competência",
    "conhecimentos", "conhecimento", "ser", "ter", "boa", "bom",
    "otimo", "otima", "excelente", "desejada", "desejadas",
    "solidos", "sólidos", "solida", "sólida", "vivencia", "vivência",
    "vivencias", "vivências", "pratica", "prática", "praticas", "práticas",
    "pratico", "prático", "boas", "bons", "grande", "grandes",
    "capacidade", "principais", "principal", "tipo", "tipos",
    "periodo", "período", "jornada",
    "presencial", "remoto", "híbrido", "híbrida", "clt", "pj", "efetivo",
    "temporario", "temporário", "cooperado", "prestador",
    "servicos", "serviços", "servico", "serviço",
    "candidatar", "candidatura", "publicada", "combinar", "combinar",
    "nível", "nivel", "pleno", "senior", "sênior", "junior", "júnior",
    "selecionar", "seleção", "selecao", "processo", "vaga", "oferece",
    "oportunidade", "oportunidades", "posição", "posicao", "posição",
    "profissional", "profissionais", "equipe", "equipes", "time", "times",
    "desafio", "desafios", "missao", "missão", "objetivo", "objetivos",
    "garantir", "assegurar", "responsavel", "responsável",
    "responsabilidades", "responsabilidade", "atividades", "atividade",
}

# Termos muito curtos ou que sao puro numero sao descartados.
_RE_TOKEN = re.compile(r"[a-záàâãéêíóôõúçñ]+")


def tokenizar(texto: str) -> Iterable[str]:
    """Devolve tokens em minusculas, sem pontuacao, sem numeros isolados."""
    for tok in _RE_TOKEN.findall(texto.lower()):
        if len(tok) <= 2:
            continue
        if tok in STOPWORDS_PT:
            continue
        yield tok


def _ler_descricoes_por_cargo() -> dict[str, list[str]]:
    """Le o CSV e devolve {cargo: [descricao1, descricao2, ...]}."""
    csv_path = config.CSV_PATH
    if not csv_path.exists():
        logger.error("CSV ausente: %s — rode `python -m src.storage` antes.", csv_path)
        return {}
    por_cargo: dict[str, list[str]] = {}
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cargo = row.get("cargo", "")
            desc = row.get("descricao_completa", "")
            if cargo and desc:
                por_cargo.setdefault(cargo, []).append(desc)
    return por_cargo


def gerar_frequencia(top: int | None = None) -> Path:
    """Gera `data/frequencia_termos.csv` com colunas: termo, cargo, frequencia.

    Inclui uma linha por (termo, cargo) e tambem um agrupamento GLOBAL.
    Se `top` for fornecido, limita aos top-N termos de cada cargo.
    """
    por_cargo = _ler_descricoes_por_cargo()
    if not por_cargo:
        return Path()

    saida = config.FREQUENCIA_TERMOS_PATH
    global_counter: Counter[str] = Counter()
    linhas: list[dict[str, object]] = []

    for cargo, descricoes in por_cargo.items():
        counter: Counter[str] = Counter()
        for desc in descricoes:
            counter.update(tokenizar(desc))
        global_counter.update(counter)
        itens = counter.most_common(top) if top else counter.most_common()
        for termo, freq in itens:
            linhas.append({"termo": termo, "cargo": cargo, "frequencia": freq})

    # Agrupamento global
    itens_glob = global_counter.most_common(top) if top else global_counter.most_common()
    for termo, freq in itens_glob:
        linhas.append({"termo": termo, "cargo": "GLOBAL", "frequencia": freq})

    # Ordena: GLOBAL primeiro por freq, depois cada cargo
    linhas.sort(key=lambda r: (r["cargo"] != "GLOBAL", r["cargo"],
                               -(r["frequencia"] if isinstance(r["frequencia"], int) else 0)))

    with saida.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["termo", "cargo", "frequencia"])
        writer.writeheader()
        writer.writerows(linhas)

    logger.info("gerado: %s (%d linhas)", saida, len(linhas))
    logger.info("top 10 global:")
    for termo, freq in global_counter.most_common(10):
        logger.info("  %s: %d", termo, freq)
    return saida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera frequencia de termos para nuvem de palavras")
    parser.add_argument("--top", type=int, default=None,
                        help="limita aos top-N termos por cargo (default: todos)")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.RUNTIME_LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    path = gerar_frequencia(top=args.top)
    return 0 if path.exists() else 1


if __name__ == "__main__":
    sys.exit(main())
