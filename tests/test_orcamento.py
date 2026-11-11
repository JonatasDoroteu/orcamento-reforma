import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import MOTIVO_SEM_PRECO, ItemExtraido
from app.servico_orcamento import ITENS_EXEMPLO, calcular_orcamento

client = TestClient(app)


def test_entrada_valida(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.main.extrair_itens", lambda descricao: ITENS_EXEMPLO)
    monkeypatch.setattr(
        "app.servico_orcamento.escolher_codigos",
        lambda itens: {item.indice: "1001" for item in itens},
    )

    resposta = client.post(
        "/orcamento",
        json={"descricao": "banheiro de 6 m², trocar piso, revestir paredes até 2,10 m"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["itens"][0]["descricao"] == "Piso porcelanato"
    assert corpo["itens"][0]["quantidade"] == 6
    assert corpo["itens"][0]["descricao_sinapi"] == "PISO PORCELANATO ESMALTADO 60X60"
    assert corpo["itens"][0]["classificacao"] == "MATERIAL"
    assert corpo["itens"][0]["preco_unitario"] == 89.9
    assert corpo["itens"][0]["total"] == 539.4
    assert corpo["itens"][0]["codigo_sinapi"] == "1001"
    assert corpo["total_estimado"] == 539.4
    assert corpo["nao_orcados"] == [
        {"descricao": "Louça sanitária", "motivo": MOTIVO_SEM_PRECO}
    ]
    assert corpo["todos_itens_precificados"] is False


def test_texto_vazio_retorna_422() -> None:
    resposta = client.post("/orcamento", json={"descricao": ""})

    assert resposta.status_code == 422


def test_item_sem_preco_vai_para_nao_orcados() -> None:
    saida = calcular_orcamento(
        [ItemExtraido(descricao="Item inexistente", quantidade=2, unidade="un")]
    )

    assert saida.itens == []
    assert saida.total_estimado == 0.0
    assert len(saida.nao_orcados) == 1
    assert saida.nao_orcados[0].descricao == "Item inexistente"
    assert saida.nao_orcados[0].motivo == MOTIVO_SEM_PRECO


def test_todos_itens_precificados_quando_nao_ha_itens_nao_orcados(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.servico_orcamento.escolher_codigos",
        lambda itens: {item.indice: "1001" for item in itens},
    )

    saida = calcular_orcamento(
        [ItemExtraido(descricao="Piso porcelanato", quantidade=6, unidade="m²")]
    )

    assert saida.nao_orcados == []
    assert saida.todos_itens_precificados is True

def test_sem_itens_nao_tem_todos_itens_precificados() -> None:
    saida = calcular_orcamento([])

    assert saida.itens == []
    assert saida.todos_itens_precificados is False