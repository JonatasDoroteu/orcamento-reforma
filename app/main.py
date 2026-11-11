from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from app.schemas import EntradaOrcamento, SaidaOrcamento
from app.servico_ia import MENSAGEM_ERRO_IA, ErroExtracaoIA, extrair_itens
from app.servico_orcamento import calcular_orcamento
from app.servico_sinapi import carregar_tabela

load_dotenv(override=False)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    carregar_tabela()
    yield


app = FastAPI(title="Orçamento Rápido de Reforma", lifespan=lifespan)


@app.post("/orcamento", response_model=SaidaOrcamento)
def criar_orcamento(entrada: EntradaOrcamento) -> SaidaOrcamento:
    try:
        itens = extrair_itens(entrada.descricao)
    except ErroExtracaoIA:
        raise HTTPException(status_code=502, detail=MENSAGEM_ERRO_IA)
    return calcular_orcamento(itens)
