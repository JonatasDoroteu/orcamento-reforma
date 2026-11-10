from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple

from app.schemas import (
    MOTIVO_SEM_PRECO,
    ItemExtraido,
    ItemNaoOrcado,
    ItemOrcado,
    SaidaOrcamento,
)

_CENTAVOS = Decimal("0.01")


class _PrecoExemplo(NamedTuple):
    codigo_sinapi: str
    preco_unitario: Decimal


# Substitui a tabela SINAPI até o CSV ser carregado. A chave é a descrição normalizada.
TABELA_PRECOS_EXEMPLO: dict[str, _PrecoExemplo] = {
    "piso porcelanato": _PrecoExemplo("87234", Decimal("89.90")),
    "revestimento de parede": _PrecoExemplo("87240", Decimal("75.00")),
}

# Itens de exemplo para os testes do endpoint. A extração real fica em servico_ia.
ITENS_EXEMPLO: list[ItemExtraido] = [
    ItemExtraido(descricao="Piso porcelanato", quantidade=6, unidade="m²"),
    ItemExtraido(descricao="Louça sanitária", quantidade=1, unidade="un"),
]


def calcular_orcamento(itens: list[ItemExtraido]) -> SaidaOrcamento:
    orcados: list[ItemOrcado] = []
    nao_orcados: list[ItemNaoOrcado] = []

    for item in itens:
        preco = TABELA_PRECOS_EXEMPLO.get(item.descricao.strip().casefold())
        if preco is None:
            nao_orcados.append(
                ItemNaoOrcado(descricao=item.descricao, motivo=MOTIVO_SEM_PRECO)
            )
            continue

        total = (Decimal(str(item.quantidade)) * preco.preco_unitario).quantize(
            _CENTAVOS, rounding=ROUND_HALF_UP
        )
        orcados.append(
            ItemOrcado(
                descricao=item.descricao,
                quantidade=item.quantidade,
                unidade=item.unidade,
                preco_unitario=float(preco.preco_unitario),
                total=float(total),
                codigo_sinapi=preco.codigo_sinapi,
            )
        )

    total_estimado = sum((Decimal(str(item.total)) for item in orcados), Decimal("0"))
    return SaidaOrcamento(
        itens=orcados,
        nao_orcados=nao_orcados,
        total_estimado=float(total_estimado.quantize(_CENTAVOS, rounding=ROUND_HALF_UP)),
    )
