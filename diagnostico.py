"""Script de diagnóstico: chama a extração de itens direto, sem passar pela API,
e mostra o erro real do Gemini (503, 404 etc.) que o endpoint esconde
atrás de uma mensagem genérica de 502."""

import os

from dotenv import load_dotenv

load_dotenv()

from app.servico_ia import ErroExtracaoIA, extrair_itens

print("Modelo em uso:", os.environ.get("GEMINI_MODEL") or "(vazio, usa o padrão do código)")

try:
    itens = extrair_itens(
        "cozinha de 10 m², trocar piso e instalar bancada de granito de 2 metros"
    )
    print("Funcionou:")
    for item in itens:
        print(" -", item)
except ErroExtracaoIA as erro:
    causa = erro.__cause__
    print("Causa real:", type(causa).__name__, causa)