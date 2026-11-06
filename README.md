# Orçamento Rápido de Reforma

API que recebe a descrição de uma reforma em texto livre e devolve um orçamento preliminar por item.

**Regra principal:** a IA só interpreta o texto (itens, quantidades, unidades). O preço vem sempre do código, consultando a tabela SINAPI. A IA nunca inventa preço.

## Status

| Etapa | Situação |
|---|---|
| Estrutura da API, validação e testes | Pronto |
| Integração com Gemini (extração de itens) | Pendente |
| Preços reais da tabela SINAPI (DuckDB) | Pendente |
| Front-end (React) e deploy | Pendente |

Hoje a API responde sempre com itens fixos de exemplo.

## Como rodar

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Documentação interativa: http://127.0.0.1:8000/docs

## Endpoint

`POST /orcamento`

```json
{ "descricao": "banheiro de 6 m², trocar piso, revestir paredes até 2,10 m, trocar louças" }
```

Resposta: `itens` (com preço e total), `nao_orcados` (com o motivo) e `total_estimado`.
Descrição vazia ou com mais de 2000 caracteres retorna 422.

## Como testar

```powershell
python -m pytest
```

## Estrutura

- `app/main.py`: FastAPI e endpoint
- `app/schemas.py`: modelos Pydantic de entrada e saída
- `app/servico_orcamento.py`: cálculo do orçamento
- `tests/`: testes com Pytest
- `SPEC.md`: especificação do projeto

## Desenvolvimento com IA

Projeto construído com Cursor, a partir do `SPEC.md`. Cada alteração gerada é lida antes de aceitar e coberta por testes.

Correções feitas por mim em relação ao código gerado:
- O comando de teste gerado (`pytest`) falhava com `ModuleNotFoundError`; troquei por `python -m pytest`.