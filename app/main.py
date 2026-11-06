from fastapi import FastAPI

from app.schemas import EntradaOrcamento, SaidaOrcamento
from app.servico_orcamento import ITENS_EXEMPLO, calcular_orcamento

app = FastAPI(title="Orçamento Rápido de Reforma")


@app.post("/orcamento", response_model=SaidaOrcamento)
def criar_orcamento(entrada: EntradaOrcamento) -> SaidaOrcamento:
    # A descrição já foi validada. A interpretação por IA entra depois;
    # por enquanto o cálculo usa itens fixos de exemplo.
    _ = entrada.descricao
    return calcular_orcamento(ITENS_EXEMPLO)
