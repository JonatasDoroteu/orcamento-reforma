import csv
import os
import re
import threading
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import duckdb
from pydantic import BaseModel, Field

RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_PADRAO = RAIZ / "data" / "insumos_limpos.csv"
REGIME_PRECO = "sem_desoneracao"
LIMITE_CANDIDATOS = 8
LIMIAR_MINIMO = 0.5
_CENTAVOS = Decimal("0.01")

# Palavras que não identificam o insumo. "trocar"/"instalacao" saem para o
# texto livre ("trocar piso") não competir com a descrição oficial.
_PALAVRAS_VAZIAS = frozenset(
    {
        "a",
        "o",
        "as",
        "os",
        "de",
        "do",
        "da",
        "dos",
        "das",
        "e",
        "em",
        "no",
        "na",
        "nos",
        "nas",
        "um",
        "uma",
        "para",
        "com",
        "por",
        "troca",
        "trocar",
        "trocada",
        "trocado",
        "instalacao",
        "instalar",
        "instalada",
        "instalado",
    }
)

_conexao: duckdb.DuckDBPyConnection | None = None
_caminho_carregado: Path | None = None
_trava = threading.Lock()


class CandidatoSinapi(BaseModel):
    codigo: str = Field(min_length=1)
    descricao: str = Field(min_length=1)
    unidade: str = Field(min_length=1)
    classificacao: str = Field(min_length=1)


def caminho_tabela() -> Path:
    bruto = os.environ.get("SINAPI_CSV", "").strip()
    if not bruto:
        return CAMINHO_PADRAO
    caminho = Path(bruto)
    if not caminho.is_absolute():
        caminho = RAIZ / caminho
    return caminho


def carregar_tabela() -> None:
    """Carrega o CSV no DuckDB. A mesma path não é lida de novo."""
    with _trava:
        _carregar_sem_trava()


def buscar_candidatos(
    descricao: str, unidade: str, limite: int = LIMITE_CANDIDATOS
) -> list[CandidatoSinapi]:
    unidade_norm = normalizar_unidade(unidade)
    consulta = tokens(descricao)
    if not unidade_norm or not consulta or limite <= 0:
        return []

    with _trava:
        _carregar_sem_trava()
        assert _conexao is not None
        linhas = _conexao.execute(
            """
            SELECT codigo, descricao, unidade, classificacao, descricao_norm
            FROM insumos
            WHERE unidade_norm = ?
            """,
            [unidade_norm],
        ).fetchall()

    pontuados: list[tuple[float, str, str, str, str]] = []
    for codigo, descricao_oficial, unidade_oficial, classificacao, descricao_norm in linhas:
        palavras = set(descricao_norm.split())
        comuns = consulta & palavras
        if not comuns:
            continue
        pontuacao = len(comuns) / len(consulta)
        if pontuacao < LIMIAR_MINIMO:
            continue
        pontuados.append(
            (pontuacao, codigo, descricao_oficial, unidade_oficial, classificacao)
        )

    pontuados.sort(key=lambda item: (-item[0], item[1]))
    return [
        CandidatoSinapi(
            codigo=codigo,
            descricao=descricao_oficial,
            unidade=unidade_oficial,
            classificacao=classificacao,
        )
        for _, codigo, descricao_oficial, unidade_oficial, classificacao in pontuados[:limite]
    ]


def obter_preco(codigo: str) -> Decimal | None:
    with _trava:
        _carregar_sem_trava()
        assert _conexao is not None
        linha = _conexao.execute(
            "SELECT preco FROM insumos WHERE codigo = ?",
            [str(codigo).strip()],
        ).fetchone()
    if linha is None:
        return None
    return Decimal(linha[0]).quantize(_CENTAVOS, rounding=ROUND_HALF_UP)


def normalizar_texto(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(letra for letra in sem_acento if not unicodedata.combining(letra))
    minusculo = sem_acento.casefold()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", minusculo).split())


def normalizar_unidade(unidade: str) -> str:
    return normalizar_texto(unidade).replace(" ", "")


def tokens(texto: str) -> set[str]:
    return {
        palavra
        for palavra in normalizar_texto(texto).split()
        if palavra not in _PALAVRAS_VAZIAS and not palavra.isdigit()
    }


def _carregar_sem_trava() -> None:
    global _conexao, _caminho_carregado
    caminho = caminho_tabela().resolve()
    if _conexao is not None and _caminho_carregado == caminho:
        return
    if not caminho.is_file():
        raise FileNotFoundError(f"CSV SINAPI não encontrado: {caminho}")

    registros = _ler_registros(caminho)
    conexao = duckdb.connect(":memory:")
    conexao.execute(
        """
        CREATE TABLE insumos (
            codigo VARCHAR PRIMARY KEY,
            descricao VARCHAR,
            unidade VARCHAR,
            unidade_norm VARCHAR,
            classificacao VARCHAR,
            preco VARCHAR,
            descricao_norm VARCHAR
        )
        """
    )
    conexao.executemany("INSERT INTO insumos VALUES (?, ?, ?, ?, ?, ?, ?)", registros)
    if _conexao is not None:
        _conexao.close()
    _conexao = conexao
    _caminho_carregado = caminho


def _ler_registros(caminho: Path) -> list[tuple[str, str, str, str, str, str, str]]:
    registros: list[tuple[str, str, str, str, str, str, str]] = []
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")
        for linha in leitor:
            if (linha.get("regime") or "").strip() != REGIME_PRECO:
                continue
            codigo = (linha.get("codigo") or "").strip()
            descricao = (linha.get("descricao") or "").strip()
            unidade = (linha.get("unidade") or "").strip()
            classificacao = (linha.get("classificacao") or "").strip()
            if not codigo or not descricao or not unidade:
                continue
            preco = _preco_decimal(linha.get("preco") or "")
            descricao_norm = " ".join(sorted(tokens(descricao)))
            registros.append(
                (
                    codigo,
                    descricao,
                    unidade,
                    normalizar_unidade(unidade),
                    classificacao,
                    format(preco, "f"),
                    descricao_norm,
                )
            )
    return registros


def _preco_decimal(bruto: str) -> Decimal:
    texto = bruto.strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return Decimal(texto).quantize(_CENTAVOS, rounding=ROUND_HALF_UP)
