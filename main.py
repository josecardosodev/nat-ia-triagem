"""
main.py

API REST (FastAPI) que expõe o serviço de classificação de chamados por IA.

Como rodar:
    uvicorn main:app --reload --port 8000

Documentação automática (Swagger):
    http://localhost:8000/docs
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from claude_client import classificar_chamado, ClaudeClientError
from database import buscar_chamado_por_id, salvar_classificacao, DatabaseError

app = FastAPI(
    title="NAT IA Triagem",
    description="Serviço de classificação automática de chamados técnicos via Claude",
    version="1.0.0",
)


class DescricaoRequest(BaseModel):
    descricao: str


@app.get("/")
def status():
    return {"status": "ok", "servico": "NAT IA Triagem"}


@app.post("/classificar")
def classificar(request: DescricaoRequest):
    """
    Recebe uma descrição de chamado em texto livre e retorna a
    classificação sugerida pela IA (categoria, prioridade, resumo,
    informação faltante). Não depende do banco de dados.
    """
    try:
        return classificar_chamado(request.descricao)
    except ClaudeClientError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/classificar/{chamado_id}")
def classificar_do_banco(chamado_id: int, salvar: bool = False):
    """
    Busca um chamado existente no PostgreSQL pelo ID, classifica a
    descrição com o Claude e, opcionalmente (?salvar=true), grava o
    resultado de volta no banco.
    """
    try:
        chamado = buscar_chamado_por_id(chamado_id)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if chamado is None:
        raise HTTPException(status_code=404, detail=f"Chamado {chamado_id} não encontrado")

    try:
        resultado = classificar_chamado(chamado["descricao"])
    except ClaudeClientError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if salvar:
        try:
            salvar_classificacao(chamado_id, resultado["categoria"], resultado["prioridade"])
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {"chamado": chamado, "classificacao": resultado}
