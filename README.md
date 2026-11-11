# Orçamento Rápido de Reforma

API que recebe a descrição de uma reforma em texto livre e devolve um orçamento preliminar por item.

**Regra principal:** a IA só interpreta o texto (itens, quantidades, unidades). O preço vem sempre do código, consultando a tabela SINAPI. A IA nunca inventa preço.

## Status

| Etapa | Situação |
|---|---|
| Estrutura da API, validação e testes | Pronto |
| Integração com Gemini (extração de itens) | Pronto |
| Preços da tabela SINAPI (DuckDB), busca de candidatos e escolha pelo modelo | Pronto, sem testes próprios ainda |
| Composições da SINAPI (serviços com mão de obra) | Pendente |
| Testes de `buscar_candidatos` e `escolher_codigos` | Pendente |
| Front-end (React) e deploy | Pendente |

A IA extrai itens, quantidades e unidades. O código busca candidatos na tabela SINAPI, o modelo escolhe um código entre eles sem ver preço e o preço vem do CSV. O modelo padrão é `gemini-3.8-flash` (`GEMINI_MODEL` no `.env`). Falha da IA responde 502, sem detalhe interno.

## Como rodar

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Preencha GEMINI_API_KEY no arquivo .env. GEMINI_MODEL já vem com gemini-3.8-flash.
uvicorn app.main:app --reload
```

Documentação interativa: http://127.0.0.1:8000/docs

## Endpoint

`POST /orcamento`

```json
{ "descricao": "banheiro de 6 m², trocar piso, revestir paredes até 2,10 m, trocar louças" }
```

Resposta: `itens` (com `descricao_sinapi`, `classificacao`, preço e total), `nao_orcados` (com o motivo), `total_estimado` e `todos_itens_precificados`. Descrição vazia ou com mais de 2000 caracteres retorna 422.

## Como testar

```powershell
python -m pytest
```

## Estrutura

- `app/main.py`: FastAPI e endpoint `POST /orcamento`
- `app/schemas.py`: modelos Pydantic de entrada e saída
- `app/servico_ia.py`: extração de itens do texto e escolha do código SINAPI entre candidatos, com Gemini (o modelo nunca vê preço)
- `app/servico_sinapi.py`: carrega o CSV no DuckDB, busca candidatos por descrição e unidade e devolve o preço por código
- `app/servico_orcamento.py`: busca candidatos, pede a escolha ao modelo, valida que o código está entre os candidatos e lê o preço da tabela
- `data/insumos_limpos.csv`: insumos da SINAPI (Bahia, referência 2026-09, sem desoneração)
- `tests/`: testes com Pytest; a chamada ao Gemini é simulada e há um CSV pequeno em `tests/fixtures/`
- `avaliacao.py`: script que roda descrições de exemplo no endpoint, para a avaliação manual
- `SPEC.md`: especificação do projeto

## Desenvolvimento com IA

Projeto construído com Cursor, a partir do `SPEC.md`. Li cada alteração antes de aceitar. Os testes cobrem a extração, o tratamento de erros e o endpoint; a busca de candidatos e a escolha pelo modelo ainda não têm testes próprios (veja Limitações).

Correções e problemas que resolvi:
- O comando de teste gerado (`pytest`) falhava com `ModuleNotFoundError`; troquei por `python -m pytest`.
- A API devolvia 502 e a mensagem genérica (de propósito, para não vazar detalhes) escondia a causa. Escrevi um script de diagnóstico que chamava a extração direto e mostrava o erro real: 503 de alta demanda em um modelo e 404 de modelo descontinuado em outro.
- Testei os modelos disponíveis na minha conta e troquei o modelo pela variável de ambiente `GEMINI_MODEL`, sem mexer no código. Depois atualizei o modelo padrão.
- O `.env` só é lido ao iniciar o servidor; o `--reload` não o recarrega. Precisei reiniciar o uvicorn para a troca valer.

## Como investiguei o 502

**Sintoma:** o endpoint devolvia 502 com uma mensagem genérica. Isso é de propósito: o erro real do Gemini não deve vazar para quem chama a API (há um teste para isso, `test_endpoint_502_nao_vaza_detalhes`). Mas escondia a causa de mim também.

**Como achei a causa:** escrevi o `diagnostico.py`, que chama `extrair_itens` direto, sem passar pela API, e imprime a exceção original (`__cause__`) da falha.

**O que encontrei:**
- Um modelo com alta demanda (503).
- Outro modelo que tinha sido descontinuado (404).

**O que mudei:** o modelo passou a vir da variável de ambiente `GEMINI_MODEL`, sem alterar código.

**Pegadinha:** o `--reload` do uvicorn recarrega o código, mas não o `.env`. Depois de mudar o modelo é preciso reiniciar o servidor.

Para rodar o diagnóstico: `python diagnostico.py`

## Limitações

**O que o projeto faz hoje:** um levantamento preliminar de **materiais** com preços da SINAPI (Bahia, referência 2026-09, sem desoneração). Não é um orçamento de obra.

**A tabela usada é de insumos, não de composições.** Os preços vêm do arquivo de insumos da SINAPI. Um insumo é um material, uma mão de obra ou um equipamento avulso. Um serviço como "trocar piso" depende de composições (material + mão de obra + equipamento por unidade de serviço), que ainda não estão no projeto. Por isso, o `total_estimado` é **parcial**: não inclui demolição, mão de obra, acessórios nem perdas.

**O que significa `todos_itens_precificados`.** O campo é `true` quando todos os itens extraídos do texto receberam um código SINAPI. Não significa que a obra está coberta: "trocar porta" pode vir como `true` só com o preço da folha da porta.

**Avaliação manual (8 descrições, 11/11/2026).** Testei o endpoint com 8 descrições que eu mesmo escrevi (banheiro, cozinha, pintura, elétrica, hidráulica, forro, porta e um texto sem sentido) e li a descrição oficial de cada código escolhido:

- 12 itens extraídos: 8 orçados e 4 não orçados (revestimento de parede, louças, bancada de granito e pintura).
- Dos 8 orçados, 4 são o item certo como material (tomada, interruptor, torneira, chuveiro) e 4 são só uma parte do serviço pedido (dois pisos, forro de gesso "sem colocação" e a folha da porta).
- Nenhum item foi precificado como serviço, com mão de obra.
- Uma das 8 chamadas retornou 502 na primeira tentativa e funcionou na repetição; não investiguei a causa, mas já vi 503 de alta demanda do modelo neste projeto.

É uma amostra pequena e a classificação é minha. Serve para mostrar o tipo de erro, não para medir precisão.

**Outras limitações conhecidas**
- O modelo escolhe variantes sem que o usuário peça (por exemplo, cerâmica em vez de porcelanato).
- Unidades incompatíveis (como "2 metros" para uma bancada vendida em m² ou un) levam o item para "não orçado", e isso é intencional: prefiro não orçar a orçar errado.
- Só existem preços da Bahia.
- A busca de candidatos e a escolha pelo modelo ainda não têm testes próprios.
