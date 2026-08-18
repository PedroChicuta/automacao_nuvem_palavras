"""Funcoes de parsing e limpeza de dados extraidos da Catho.

Foco em:
- `parse_salario`: converte texto de salario ("R$ 16.500 Beneficios ...",
  "A partir de R$ 5.000,00", "A Combinar") em (min, max) numericos.
- `limpar_texto`: normaliza espacamento/quebras de linha de textos longos.
- `limpar_salario`: separa o valor do salario do restante (beneficios etc.).
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Salario
# ---------------------------------------------------------------------------
# Captura valores no formato brasileiro: "R$ 16.500", "R$ 5.000,00",
# "R$ 16.500,00". Agrupa parte inteira e decimal.
_RE_VALOR = re.compile(
    r"r\$\s*([\d.,]+)\s*(?:,(\d{2}))?",
    re.IGNORECASE,
)
# Detecta "A partir de" -> so ha minimo.
_RE_A_PARTIR = re.compile(r"a partir de", re.IGNORECASE)
# Detecta "Ate" -> so ha maximo.
_RE_ATE = re.compile(r"at[eé]\s", re.IGNORECASE)
# Detecta faixa com "a": "R$ 5.000 a R$ 8.000".
_RE_FAIXA = re.compile(r"\ba\b", re.IGNORECASE)


def _parse_numero_brl(num_str: str) -> float:
    """Converte '16.500' ou '5.000,00' em float (formato brasileiro)."""
    # Remove pontos de milhar e troca virgula decimal por ponto.
    limpo = num_str.replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def parse_salario(texto: str) -> tuple[float | None, float | None]:
    """Extrai (salario_min, salario_max) de uma string de salario.

    Retorno:
      (None, None)            -> "A Combinar" / sem valor.
      (valor, valor)          -> valor unico ("R$ 16.500").
      (valor, None)           -> "A partir de R$ 5.000".
      (None, valor)           -> "Ate R$ 5.000".
      (min, max)              -> faixa "R$ 5.000 a R$ 8.000".
    """
    if not texto:
        return None, None

    low = texto.lower()
    if "a combinar" in low and "r$" not in low:
        return None, None

    valores: list[tuple[str, str | None]] = _RE_VALOR.findall(texto)
    # findall com grupo opcional pode retornar tuplas; normaliza.
    nums: list[float] = []
    for grp in _RE_VALOR.finditer(texto):
        num_str = grp.group(1)
        # Se o grupo 1 termina com virgula+2 digitos, o grupo 2 vem separado.
        # Aqui tratamos o numero completo ja que o regex captura tudo no grp1.
        nums.append(_parse_numero_brl(num_str))

    if not nums:
        return None, None

    if _RE_A_PARTIR.search(low):
        return (nums[0], None)
    if _RE_ATE.search(low):
        return (None, nums[0])
    if len(nums) >= 2 and _RE_FAIXA.search(low):
        return (min(nums[0], nums[1]), max(nums[0], nums[1]))
    # Default: valor unico.
    return (nums[0], nums[0])


def limpar_salario(texto: str) -> str:
    """Devolve apenas a parte do salario (corta em 'Beneficios' ou similares)."""
    if not texto:
        return ""
    # Corta no primeiro marcador de beneficios/extra.
    corte = re.split(r"\s+Benef[ií]cios|\s+\+\s*\d+\s+benef", texto, maxsplit=1,
                     flags=re.IGNORECASE)
    return corte[0].strip()


# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------
_RE_MULTI_ESPACO = re.compile(r"[ \t]+")
_RE_MULTI_LINHA = re.compile(r"\n{3,}")
_RE_PONT_FINAL = re.compile(r"\s+([,.;:!?])")


def limpar_texto(texto: str) -> str:
    """Normaliza espacamento e quebras de linha de um texto longo.

    - Remove espacos/tabulacoes sobrando.
    - Colapsa 3+ quebras de linha seguidas em 2.
    - Remove espaco antes de pontuacao.
    - Strip global.
    """
    if not texto:
        return ""
    t = texto.replace("\r\n", "\n").replace("\r", "\n")
    t = _RE_MULTI_ESPACO.sub(" ", t)
    t = _RE_MULTI_LINHA.sub("\n\n", t)
    t = _RE_PONT_FINAL.sub(r"\1", t)
    return t.strip()


# ---------------------------------------------------------------------------
# Auto-teste simples (executavel via `python -m src.parser`)
# ---------------------------------------------------------------------------
_CASOS_SALARIO = [
    ("A Combinar", (None, None)),
    ("A Combinar + 3 benefícios", (None, None)),
    ("A Combinar Benefícios Tíquete refeição", (None, None)),
    ("R$ 16.500 Benefícios Seguro saúde", (16500.0, 16500.0)),
    ("R$ 5.000 Benefícios Assistência médica", (5000.0, 5000.0)),
    ("A partir de R$ 5.000,00 Benefícios", (5000.0, None)),
    ("R$ 16.000 Benefícios Assistência médica", (16000.0, 16000.0)),
]


def _self_test() -> int:
    falhas = 0
    for texto, esperado in _CASOS_SALARIO:
        obtido = parse_salario(texto)
        ok = obtido == esperado
        status = "OK" if ok else "FAIL"
        if not ok:
            falhas += 1
        print(f"  [{status}] {texto[:50]!r:55} -> {obtido} (esperado {esperado})")
    print(f"\nlimpar_salario('R$ 16.500 Benefícios Seguro') = "
          f"{limpar_salario('R$ 16.500 Benefícios Seguro saúde')!r}")
    print(f"limpar_texto: multi-espaco -> "
          f"{limpar_texto('ola   mundo  \n\n\n\n teste   .')!r}")
    return 1 if falhas else 0


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())
