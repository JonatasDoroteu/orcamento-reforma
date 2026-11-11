from fastapi.testclient import TestClient

from app.main import app

CASOS = [
    "banheiro de 6 m², trocar piso, revestir paredes até 2,10 m, trocar louças",
    "cozinha de 10 m², trocar piso porcelanato e instalar bancada de granito de 2 metros",
    "pintar parede de sala de 20 m² com tinta acrílica",
    "trocar 5 tomadas e 3 interruptores",
    "instalar torneira de cozinha e chuveiro elétrico",
    "forro de gesso em 12 m² de quarto",
    "trocar porta de madeira de 80 cm",
    "oi, tudo bem?",
]

with TestClient(app) as client:
    for texto in CASOS:
        r = client.post("/orcamento", json={"descricao": texto})
        print("\n=== ", texto, "->", r.status_code)
        if r.status_code != 200:
            continue
        corpo = r.json()
        for i in corpo["itens"]:
            print(f"  ORÇADO  {i['descricao']} | {i['quantidade']} {i['unidade']}")
            print(f"          SINAPI {i['codigo_sinapi']}: {i['descricao_sinapi']}")
        for n in corpo["nao_orcados"]:
            print(f"  NÃO ORÇADO  {n['descricao']} | {n['motivo']}")
            print("  todos precificados:", corpo["todos_itens_precificados"])