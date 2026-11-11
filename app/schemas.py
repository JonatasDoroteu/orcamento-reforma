from pydantic import BaseModel, Field, field_validator

LIMITE_DESCRICAO = 2_000
MOTIVO_SEM_PRECO = "item não encontrado na tabela SINAPI"
MOTIVO_SEM_ESCOLHA = "nenhum código SINAPI compatível foi escolhido"
MOTIVO_FALHA_ESCOLHA = "não foi possível escolher o código na tabela SINAPI"


class EntradaOrcamento(BaseModel):
    descricao: str

    @field_validator("descricao")
    @classmethod
    def descricao_util(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("A descrição não pode ser vazia.")
        if len(texto) > LIMITE_DESCRICAO:
            raise ValueError("A descrição excede o limite de 2000 caracteres.")
        return texto


class ItemExtraido(BaseModel):
    """Item interpretado do texto, ainda sem preço."""

    descricao: str = Field(min_length=1)
    quantidade: float = Field(gt=0)
    unidade: str = Field(min_length=1)


class ItemOrcado(BaseModel):
    descricao: str
    descricao_sinapi: str
    classificacao: str
    quantidade: float
    unidade: str
    preco_unitario: float
    total: float
    codigo_sinapi: str


class ItemNaoOrcado(BaseModel):
    descricao: str
    motivo: str


class SaidaOrcamento(BaseModel):
    itens: list[ItemOrcado]
    nao_orcados: list[ItemNaoOrcado]
    total_estimado: float
    todos_itens_precificados: bool
