from pathlib import Path

import pytest

FIXTURE_SINAPI = Path(__file__).parent / "fixtures" / "sinapi_mini.csv"


@pytest.fixture(autouse=True)
def tabela_sinapi_de_teste(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nenhum teste lê o CSV real nem usa chave de API verdadeira."""
    monkeypatch.setenv("SINAPI_CSV", str(FIXTURE_SINAPI))
    monkeypatch.setenv("GEMINI_API_KEY", "chave-falsa")
    from app.servico_sinapi import carregar_tabela

    carregar_tabela()
