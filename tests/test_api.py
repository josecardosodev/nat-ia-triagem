"""Testes dos endpoints da API REST (Claude e banco simulados)."""
import pytest
from fastapi.testclient import TestClient

import main
from claude_client import ClaudeClientError
from database import DatabaseError

CLASSIFICACAO = {
    "categoria": "Audiovisual",
    "prioridade": "Média",
    "resumo": "Som do auditório com chiado",
    "info_faltante": "nenhuma",
}

CHAMADO = {"id": 42, "descricao": "Som do auditório com chiado"}


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def ia_ok(monkeypatch):
    monkeypatch.setattr(main, "classificar_chamado", lambda descricao: CLASSIFICACAO)


def test_status(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_classificar_texto(client, ia_ok):
    resposta = client.post("/classificar", json={"descricao": "Som com chiado"})
    assert resposta.status_code == 200
    assert resposta.json() == CLASSIFICACAO


def test_classificar_texto_vazio_retorna_422(client, ia_ok):
    resposta = client.post("/classificar", json={"descricao": ""})
    assert resposta.status_code == 422


def test_erro_da_ia_retorna_502(client, monkeypatch):
    def falha(descricao):
        raise ClaudeClientError("API fora do ar")

    monkeypatch.setattr(main, "classificar_chamado", falha)
    resposta = client.post("/classificar", json={"descricao": "Som com chiado"})
    assert resposta.status_code == 502
    assert "API fora do ar" in resposta.json()["detail"]


def test_classificar_do_banco(client, ia_ok, monkeypatch):
    salvos = []
    monkeypatch.setattr(main, "buscar_chamado_por_id", lambda chamado_id: CHAMADO)
    monkeypatch.setattr(main, "salvar_classificacao", lambda *args: salvos.append(args))

    resposta = client.post("/classificar/42")
    assert resposta.status_code == 200
    assert resposta.json() == {"chamado": CHAMADO, "classificacao": CLASSIFICACAO}
    assert salvos == []  # sem ?salvar=true não grava nada


def test_classificar_do_banco_e_salvar(client, ia_ok, monkeypatch):
    salvos = []
    monkeypatch.setattr(main, "buscar_chamado_por_id", lambda chamado_id: CHAMADO)
    monkeypatch.setattr(main, "salvar_classificacao", lambda *args: salvos.append(args))

    resposta = client.post("/classificar/42?salvar=true")
    assert resposta.status_code == 200
    assert salvos == [(42, "Audiovisual", "Média")]


def test_chamado_inexistente_retorna_404(client, ia_ok, monkeypatch):
    monkeypatch.setattr(main, "buscar_chamado_por_id", lambda chamado_id: None)
    resposta = client.post("/classificar/999")
    assert resposta.status_code == 404


def test_erro_de_banco_retorna_500(client, ia_ok, monkeypatch):
    def falha(chamado_id):
        raise DatabaseError("conexão recusada")

    monkeypatch.setattr(main, "buscar_chamado_por_id", falha)
    resposta = client.post("/classificar/42")
    assert resposta.status_code == 500
