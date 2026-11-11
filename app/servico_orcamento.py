from decimal import Decimal, ROUND_HALF_UP

from app.schemas import (
    MOTIVO_FALHA_ESCOLHA,
    MOTIVO_SEM_ESCOLHA,
    MOTIVO_SEM_PRECO,
    ItemExtraido,
    ItemNaoOrcado,
    ItemOrcado,
    SaidaOrcamento,
)
from app.servico_ia import (
    CandidatoEnviado,
    ErroExtracaoIA,
    ItemComCandidatos,
    escolher_codigos,
)
from app.servico_sinapi import buscar_candidatos, obter_preco

_CENTAVOS = Decimal("0.01")

# Itens de exemplo para os testes do endpoint. A extração real fica em servico_ia.
ITENS_EXEMPLO: list[ItemExtraido] = [
    ItemExtraido(descricao="Piso porcelanato", quantidade=6, unidade="m²"),
    ItemExtraido(descricao="Louça sanitária", quantidade=1, unidade="un"),
]


def calcular_orcamento(itens: list[ItemExtraido]) -> SaidaOrcamento:
    orcados: list[ItemOrcado] = []
    nao_orcados: list[ItemNaoOrcado] = []
    fila: list[tuple[ItemExtraido, int | None]] = []
    para_escolha: list[ItemComCandidatos] = []

    for item in itens:
        candidatos = buscar_candidatos(item.descricao, item.unidade)
        if not candidatos:
            fila.append((item, None))
            continue
        indice = len(para_escolha)
        para_escolha.append(
            ItemComCandidatos(
                indice=indice,
                descricao=item.descricao,
                quantidade=item.quantidade,
                unidade=item.unidade,
                candidatos=[
                    CandidatoEnviado(
                        codigo=candidato.codigo,
                        descricao=candidato.descricao,
                        unidade=candidato.unidade,
                    )
                    for candidato in candidatos
                ],
            )
        )
        fila.append((item, indice))

    escolhas: dict[int, str | None] = {}
    falha_escolha = False
    if para_escolha:
        try:
            escolhas = escolher_codigos(para_escolha)
        except ErroExtracaoIA:
            falha_escolha = True

    codigos_por_indice = {
        item.indice: {candidato.codigo for candidato in item.candidatos}
        for item in para_escolha
    }

    for item, indice in fila:
        if indice is None:
            nao_orcados.append(
                ItemNaoOrcado(descricao=item.descricao, motivo=MOTIVO_SEM_PRECO)
            )
            continue
        if falha_escolha:
            nao_orcados.append(
                ItemNaoOrcado(descricao=item.descricao, motivo=MOTIVO_FALHA_ESCOLHA)
            )
            continue

        codigo = escolhas.get(indice)
        if codigo is None or codigo not in codigos_por_indice[indice]:
            nao_orcados.append(
                ItemNaoOrcado(descricao=item.descricao, motivo=MOTIVO_SEM_ESCOLHA)
            )
            continue

        preco = obter_preco(codigo)
        if preco is None:
            nao_orcados.append(
                ItemNaoOrcado(descricao=item.descricao, motivo=MOTIVO_SEM_PRECO)
            )
            continue

        total = (Decimal(str(item.quantidade)) * preco).quantize(
            _CENTAVOS, rounding=ROUND_HALF_UP
        )
        orcados.append(
            ItemOrcado(
                descricao=item.descricao,
                quantidade=item.quantidade,
                unidade=item.unidade,
                preco_unitario=float(preco),
                total=float(total),
                codigo_sinapi=codigo,
            )
        )

    total_estimado = sum((Decimal(str(item.total)) for item in orcados), Decimal("0"))
    return SaidaOrcamento(
        itens=orcados,
        nao_orcados=nao_orcados,
        total_estimado=float(total_estimado.quantize(_CENTAVOS, rounding=ROUND_HALF_UP)),
    )
