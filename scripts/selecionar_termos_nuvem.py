"""Seleciona os top-N termos por cargo a partir de `data/frequencia_termos.csv`.

Lê o CSV de frequência gerado por `scripts/gerar_termos.py`, filtra ruído
(stopwords de seleção) e pontua cada termo combinando sua frequência no cargo
com sua frequência global, de modo a priorizar termos relevantes para o
mercado e representativos do cargo. Exporta um CSV pronto para alimentar
geradores de nuvem de palavras (wordcloud.online/pt, biblioteca `wordcloud`,
etc.).

Fórmula de pontuação:
    score = peso_cargo * freq_cargo + peso_global * freq_global

Uso:
    python scripts/selecionar_termos_nuvem.py
    python scripts/selecionar_termos_nuvem.py --top 25
    python scripts/selecionar_termos_nuvem.py --top 30 --peso-cargo 3 --peso-global 1
    python scripts/selecionar_termos_nuvem.py --freq-min 5
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402

logger = logging.getLogger("selecionar_termos_nuvem")

# ---------------------------------------------------------------------------
# Stopwords de seleção — ruído que sobrevive à tokenização de `gerar_termos.py`
# mas não agrega valor à nuvem de palavras (benefícios, nomes de empresa,
# dias da semana, jargão de RH, modalidades de contratação, etc.).
# Mantida separada das stopwords de tokenização para não poluir `gerar_termos.py`.
# ---------------------------------------------------------------------------
STOPWORDS_SELECAO: set[str] = {
    # --- Dias da semana / jornada / regime ---
    "segunda", "sexta", "feira", "dia", "dias", "horario", "horarios",
    "horas", "diarias", "integral", "manha", "tarde", "tardes", "semanal",
    "semanais", "mensal", "mensais", "regime", "modalidade", "remoto",
    "remota", "presencial", "hibrido", "hibrida", "home", "office",
    "expediente", "escala", "turno", "turnos", "pausa", "intervalo",
    # --- Benefícios / vale / convênio ---
    "vale", "auxilio", "alimentacao", "refeicao", "odontologica", "medica",
    "convenio", "plano", "saude", "plr", "lucros", "previdencia", "privada",
    "anual", "orcamento", "creche", "clube", "vantagens", "desconto",
    "descontos", "subsidiado", "subsidiados", "extensiva", "comercio",
    "exterior", "credencial", "abrangencia", "amil", "bradesco", "hapvida",
    "unimed", "totalpass", "telepsicologia", "sesc", "sesi", "ppr",
    "parcerias", "estacionamento", "restaurante", "refeitorio",
    # --- Nomes de empresa / instituições ---
    "araujo", "moema", "scherner", "metrocasa", "weg", "rolls", "royce",
    "startups", "gigantes", "manpowergroup", "inovatalentos", "fabrikafilmes",
    "itaú", "fapesc", "iel", "ielsc", "bairesdev", "anapro", "visus",
    "safi", "blueyonder", "zsdpaletes", "bitrix", "salesforce", "jda",
    # --- Jargão de RH / boilerplate de vagas ---
    "você", "estamos", "buscamos", "talentos", "talento", "venha", "quer",
    "gosta", "opcional", "diferencial", "diferenciais", "foco", "busca",
    "oportunidade", "oportunidades", "desafio", "desafios", "missao",
    "missão", "objetivo", "objetivos", "equipe", "equipes", "time", "times",
    "colaborativo", "inovador", "orientado", "inova", "inovacao", "cultura",
    "ambiente", "ambientes", "crescimento", "carreira", "clareza", "clara",
    "claras", "candidato", "candidate", "candidatos", "entregar", "onboarding",
    "contratando", "concluido", "sera", "forma", "interesse", "disponibilidade",
    "contratacao", "previa", "serao", "queremos", "conhecer", "queremos",
    "quer", "gosta", "paixao", "apaixonado", "apaixonados", "paixoes",
    "celebrar", "chegada", "bebe", "momento", "grupo", "funeral", "amparo",
    "indenizacao", "lazer", "rotina", "verdade", "academy", "leads",
    "dedicada", "lubrificantes", "avaliacoes", "frequentes", "reconhecimento",
    "motiva", "indique", "bonus", "futuros", "premiacao", "brindes",
    "presentes", "datas", "confianca", "clima", "anonima", "credibilidade",
    "preocupacao", "certificada", "great", "place", "compromisso", "etico",
    "informatica", "internet", "editores", "texto", "logico", "classificar",
    "armazenar", "demanda", "confidencialidade", "zelar", "realize", "link",
    "somente", "serao", "considerados", "pcd", "valorizamos", "diversidade",
    "incentivamos", "novo", "rumo", "valoriza", "potencial", "reconhecido",
    "valorizado", "transforme", "gente", "inovatalentos",
    # --- Escolaridade / nível (já cobertos parcialmente por gerar_termos) ---
    "superior", "completo", "correlatas", "graduacao", "ensino", "formacao",
    "conforme", "pos", "anos", "paulo", "preferencialmente", "obrigatorios",
    "desejaveis", "cursos", "mestrado", "doutorado", "afins", "similares",
    "comprovada", "forte", "estar", "estejam", "provenientes", "curtando",
    "noções", "basico", "intermediario", "avancado", "basica", "cursando",
    # --- Verbos genéricos / conectivos que escaparam ---
    "manter", "nao", "parte", "pessoa", "pessoas", "demais", "alem",
    "incluindo", "diversas", "diversos", "total", "estendida", "doencas",
    "graves", "oficial", "respeito", "organizacional", "reforcando",
    "positivo", "raciocinio", "limpar", "transformem", "conosco",
    "destinada",
    # --- Geografia / endereço ---
    "local", "acesso", "avenida", "paulista", "bela", "vista", "jaragua",
    "sul", "piracicaba", "jundiaí", "osasco", "lapa", "olimpia", "vila",
    "matriz", "nacional", "brasil", "pais", "instituicoes", "instituto",
    "universidades", "escolas", "conferencia",
    # --- Inscricao / processo seletivo (boilerplate) ---
    "inscricao", "preencha", "campos", "verificando", "estao", "corretas",
    "atualizadas", "garanta", "chance", "transformador", "inscreva",
    "pesquisaedesenvolvimento", "carreiratech", "org", "conhece", "www",
    "net", "institutional", "startup", "diplomacia", "focada", "navegar",
    "procura", "assistente", "entrevista", "entrevistar", "entrevistas",
    "inserir", "justa", "agradavel",
    # --- Diversos ruido residual ---
    "xxxx", "espalhadas", "constante", "enxerga", "detalhe", "formas",
    "sinal", "essencia", "confira", "concorrer", "psicologia",
    "aprendizagem", "educacionais", "fornecam", "progresso", "engajamento",
    "academicas", "conduzir", "intervencoes", "pedagogicas", "recomendar",
    "ajustes", "analises", "evoluindo", "predicoes", "prescricoes",
    "solicitacao", "bacanas", "aluno", "entenda", "min", "veja", "zenklub",
    "ecoa", "escola", "livres", "gratuitos", "day", "off", "abono",
    "presente", "educadores", "fases", "marcantes", "casamento", "nova",
    "titulacao", "cor", "idade", "genero", "sexual", "religiao",
    "caracteristica", "particularidade", "desejo", "educadora", "sorte",
    "estudantes", "semestre", "economicos", "notas", "powerpoint",
    "conteudos", "traducao", "eventualmente", "escrito", "oral",
    "especializada", "pericias", "estagiario", "contribuam",
    "imobiliarias", "avaliadores", "geoprocessamento", "geopandas",
    "postgis", "vontade", "aprender", "excelencia", "relevancia", "inclui",
    "questoes", "investimentos", "revisar", "perguntas", "premissas",
    "executiva", "materiais", "consumer", "market", "cmi", "conectando",
    "incentivar", "fundamental", "nativo", "fornecedores", "excelentes",
    "fatores", "impactam", "gerados", "apresentadas", "pesquisador",
    "comeca", "chegou", "conecta", "mentes", "brilhantes", "peca",
    "mercadologica", "tecnologica", "negociavel", "prorrogacao", "liquidos",
    "mes", "almoco", "brinde", "final", "ambulatorial", "automate", "apps",
    "integrada", "previsao", "inicio", "agosto", "fique", "atento", "caixa",
    "spam", "lixo", "eletronico", "termos", "envie", "curriculo", "coloque",
    "audio", "vimeo", "studio", "feitas", "https", "mail", "conheca",
    "setor",
}


def ler_frequencia(path: Path) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    """Lê `frequencia_termos.csv` e devolve (global, por_cargo).

    global     : {termo: frequencia}
    por_cargo  : {cargo: {termo: frequencia}}
    """
    if not path.exists():
        logger.error("CSV ausente: %s — rode `python scripts/gerar_termos.py` antes.", path)
        return {}, {}

    global_freq: dict[str, int] = {}
    cargo_freq: dict[str, dict[str, int]] = defaultdict(dict)

    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            termo = (row["termo"] or "").strip()
            cargo = (row["cargo"] or "").strip()
            freq = int(row["frequencia"])
            if not termo:
                continue
            if cargo == "GLOBAL":
                global_freq[termo] = freq
            else:
                cargo_freq[cargo][termo] = freq

    return global_freq, dict(cargo_freq)


def pontuar(
    termos_cargo: dict[str, int],
    global_freq: dict[str, int],
    peso_cargo: float,
    peso_global: float,
    freq_min_cargo: int,
) -> list[tuple[str, int, int, float]]:
    """Pontua e ordena os termos de um cargo.

    Devolve uma lista de tuplas (termo, freq_cargo, freq_global, score),
    ordenada por score decrescente.
    """
    scored: list[tuple[str, int, int, float]] = []
    for termo, fc in termos_cargo.items():
        if termo in STOPWORDS_SELECAO:
            continue
        if fc < freq_min_cargo:
            continue
        fg = global_freq.get(termo, 0)
        score = peso_cargo * fc + peso_global * fg
        scored.append((termo, fc, fg, score))
    scored.sort(key=lambda x: -x[3])
    return scored


def selecionar(
    top: int = 25,
    peso_cargo: float = 2.0,
    peso_global: float = 1.0,
    freq_min_cargo: int = 0,
) -> dict[str, list[tuple[str, int, int, float]]]:
    """Seleciona os top-N termos por cargo.

    Parâmetros:
        top            : nº de termos por cargo (default 25).
        peso_cargo     : peso da frequência no cargo (default 2.0).
        peso_global    : peso da frequência global (default 1.0).
        freq_min_cargo : frequência mínima no cargo para ser considerado.

    Devolve:
        {cargo: [(termo, freq_cargo, freq_global, score), ...]}
    """
    global_freq, cargo_freq = ler_frequencia(config.FREQUENCIA_TERMOS_PATH)
    if not cargo_freq:
        return {}

    resultado: dict[str, list[tuple[str, int, int, float]]] = {}
    for cargo, termos in cargo_freq.items():
        scored = pontuar(
            termos, global_freq, peso_cargo, peso_global, freq_min_cargo
        )
        resultado[cargo] = scored[:top]
        logger.info(
            "%s: %d candidatos -> top %d selecionados",
            cargo, len(scored), min(top, len(scored)),
        )
    return resultado


def exportar(
    selecao: dict[str, list[tuple[str, int, int, float]]],
    saida: Path,
) -> Path:
    """Exporta a seleção para CSV (colunas: termo, cargo, frequencia)."""
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["termo", "cargo", "frequencia"])
        for cargo, itens in selecao.items():
            for termo, fc, _fg, _score in itens:
                writer.writerow([termo, cargo, fc])
    logger.info("exportado: %s (%d linhas)", saida, sum(len(v) for v in selecao.values()))
    return saida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seleciona top-N termos por cargo para nuvem de palavras"
    )
    parser.add_argument(
        "--top", type=int, default=25,
        help="nº de termos por cargo (default: 25)",
    )
    parser.add_argument(
        "--peso-cargo", type=float, default=2.0,
        help="peso da frequência no cargo (default: 2.0)",
    )
    parser.add_argument(
        "--peso-global", type=float, default=1.0,
        help="peso da frequência global (default: 1.0)",
    )
    parser.add_argument(
        "--freq-min", type=int, default=0,
        help="frequência mínima no cargo para ser considerado (default: 0)",
    )
    parser.add_argument(
        "--saida", type=str, default=None,
        help="caminho do CSV de saída (default: data/termos_selecionados.csv)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.RUNTIME_LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    selecao = selecionar(
        top=args.top,
        peso_cargo=args.peso_cargo,
        peso_global=args.peso_global,
        freq_min_cargo=args.freq_min,
    )
    if not selecao:
        logger.error("nenhum termo selecionado.")
        return 1

    saida = Path(args.saida) if args.saida else config.TERMOS_SELECIONADOS_PATH
    exportar(selecao, saida)

    print("\n" + "=" * 80)
    print(f"SELEÇÃO DE {args.top} TERMOS POR CARGO")
    print("=" * 80)
    for cargo, itens in selecao.items():
        print(f"\n### {cargo}\n")
        print(f"{'#':>3} {'termo':<25} {'freq_cargo':>10} {'freq_global':>12} {'score':>8}")
        print("-" * 65)
        for i, (t, fc, fg, sc) in enumerate(itens, 1):
            print(f"{i:>3} {t:<25} {fc:>10} {fg:>12} {sc:>8.0f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
