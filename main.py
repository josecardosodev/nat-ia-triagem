"""
main.py

API REST (FastAPI) que expõe o serviço de classificação de chamados por IA.

Como rodar:
    uvicorn main:app --reload --port 8000

Documentação automática (Swagger):
    http://localhost:8000/docs
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from claude_client import TAMANHO_MAXIMO_DESCRICAO, ClaudeClientError, classificar_chamado
from database import DatabaseError, buscar_chamado_por_id, salvar_classificacao

app = FastAPI(
    title="IA Triagem de Chamados",
    description="Serviço de classificação automática de chamados técnicos via Claude (Anthropic)",
    version="1.1.0",
)


class DescricaoRequest(BaseModel):
    descricao: str = Field(
        ...,
        min_length=1,
        max_length=TAMANHO_MAXIMO_DESCRICAO,
        examples=["Projetor da sala 204 não liga, prova é amanhã"],
    )


class Classificacao(BaseModel):
    categoria: str
    prioridade: str
    resumo: str
    info_faltante: str


@app.get("/")
def status():
    return {"status": "ok", "servico": "IA Triagem de Chamados"}


@app.post("/classificar", response_model=Classificacao)
def classificar(request: DescricaoRequest):
    """
    Recebe uma descrição de chamado em texto livre e retorna a
    classificação sugerida pela IA. Não depende do banco de dados.
    """
    try:
        return classificar_chamado(request.descricao)
    except ClaudeClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


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
        raise HTTPException(status_code=500, detail=str(e)) from e

    if chamado is None:
        raise HTTPException(status_code=404, detail=f"Chamado {chamado_id} não encontrado")

    try:
        resultado = classificar_chamado(chamado["descricao"])
    except ClaudeClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    if salvar:
        try:
            salvar_classificacao(chamado_id, resultado["categoria"], resultado["prioridade"])
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    return {"chamado": chamado, "classificacao": resultado}
