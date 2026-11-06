# Orçamento Rápido de Reforma com IA

## Objetivo
Receber a descrição de uma reforma em texto livre e devolver um orçamento
preliminar por item, com preços vindos de uma tabela SINAPI.

## Regra principal
- A IA SÓ interpreta o texto e extrai itens, quantidades e unidades.
- O PREÇO vem sempre do código, consultando a tabela SINAPI. A IA nunca inventa preço.

## Entrada
POST /orcamento
{ "descricao": "banheiro de 6 m², trocar piso, revestir paredes até 2,10 m, trocar louças" }

## Saída
{
  "itens": [
    { "descricao": "Piso porcelanato", "quantidade": 6, "unidade": "m²",
      "preco_unitario": 0.0, "total": 0.0, "codigo_sinapi": "..." }
  ],
  "nao_orcados": [
    { "descricao": "...", "motivo": "item não encontrado na tabela SINAPI" }
  ],
  "total_estimado": 0.0
}

## Fluxo
1. Validar entrada (texto vazio ou muito longo retorna 422).
2. Chamar a API de IA (Gemini) pedindo JSON com itens extraídos.
3. Validar a resposta da IA com Pydantic (se inválida, retry 1 vez; depois erro 502).
4. Para cada item, buscar o preço na tabela SINAPI (CSV carregado no DuckDB).
5. Item sem correspondência vai para "nao_orcados" com o motivo.
6. Calcular totais no código.

## Tratamento de falhas
- Timeout de 30 s na chamada da IA.
- Retry apenas em erros 429/5xx.
- Mitigar prompt injection: o texto do usuário é dado, nunca instrução.

## Stack
- Back: Python, FastAPI, Pydantic, DuckDB, Pytest
- IA: Gemini (chave via variável de ambiente, nunca no código)
- Front (depois): React gerado no v0
- Deploy: Render (back) e Vercel (front)

## Fora do escopo (por enquanto)
Login, banco de dados de clientes, geração de PDF.