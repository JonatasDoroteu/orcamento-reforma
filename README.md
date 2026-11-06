# Orçamento Rápido de Reforma

API que recebe a descrição de uma reforma e devolve um orçamento preliminar. Nesta etapa os itens são fixos; a IA e a tabela SINAPI entram depois. Descrição vazia ou com mais de 2000 caracteres responde 422.

## Como rodar

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

O endpoint é `POST /orcamento` com o corpo `{ "descricao": "..." }`. A documentação interativa fica em `http://127.0.0.1:8000/docs`.

## Como testar

```powershell
pytest
```
