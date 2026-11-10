from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from app.schemas import EntradaOrcamento, SaidaOrcamento
from app.servico_ia import MENSAGEM_ERRO_IA, ErroExtracaoIA, extrair_itens
from app.servico_orcamento import calcular_orcamento

load_dotenv(override=False)

app = FastAPI(title="Orçamento Rápido de Reforma")


@app.post("/orcamento", response_model=SaidaOrcamento)
def criar_orcamento(entrada: EntradaOrcamento) -> SaidaOrcamento:
    try:
        itens = extrair_itens(entrada.descricao)
    except ErroExtracaoIA:
        raise HTTPException(status_code=502, detail=MENSAGEM_ERRO_IA)
    return calcular_orcamento(itens)
