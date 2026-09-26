"""Testes da camada de integração com o Claude (sem chamar a API real)."""
from types import SimpleNamespace

import anthropic
import pytest

import claude_client
from claude_client import (
    ClaudeClientError,
    classificar_chamado,
    interpretar_resposta,
    montar_prompt,
)

RESPOSTA_OK = (
    '{"categoria": "Provas", "prioridade": "Alta", '
    '"resumo": "Projetor com defeito em sala de prova", "info_faltante": "nenhuma"}'
)


class FakeAnthropic:
    """Substitui anthropic.Anthropic nos testes, devolvendo um texto fixo."""

    def __init__(self, texto=RESPOSTA_OK, erro=None):
        self.texto = texto
        self.erro = erro
        self.chamadas = []
        self.messages = SimpleNamespace(create=self._create)

    def __call__(self, api_key):
        return self

    def _create(self, **kwargs):
        self.chamadas.append(kwargs)
        if self.erro:
            raise self.erro
        return SimpleNamespace(content=[SimpleNamespace(text=self.texto)])


@pytest.fixture
def fake_api(monkeypatch):
    fake = FakeAnthropic()
    monkeypatch.setattr(claude_client, "ANTHROPIC_API_KEY", "chave-de-teste")
    monkeypatch.setattr(claude_client.anthropic, "Anthropic", fake)
    return fake


# --- montar_prompt -----------------------------------------------------------

def test_prompt_inclui_descricao_e_categorias():
    prompt = montar_prompt("  Impressora sem toner  ")
    assert "Impressora sem toner" in prompt
    for categoria in claude_client.CATEGORIAS_VALIDAS:
        assert categoria in prompt


# --- interpretar_resposta ------------------------------------------------------

def test_interpreta_json_valido():
    resultado = interpretar_resposta(RESPOSTA_OK)
    assert resultado["categoria"] == "Provas"
    assert resultado["prioridade"] == "Alta"


def test_aceita_json_dentro_de_bloco_markdown():
    resultado = interpretar_resposta(f"```json\n{RESPOSTA_OK}\n```")
    assert resultado["categoria"] == "Provas"


def test_descarta_campos_extras():
    texto = RESPOSTA_OK[:-1] + ', "extra": "x"}'
    assert "extra" not in interpretar_resposta(texto)


@pytest.mark.parametrize(
    "texto",
    [
        "isso não é json",
        "[1, 2, 3]",
        '{"categoria": "Provas"}',
        RESPOSTA_OK.replace("Provas", "Culinária"),
        RESPOSTA_OK.replace("Alta", "Urgentíssima"),
    ],
    ids=["texto-livre", "lista", "incompleto", "categoria-invalida", "prioridade-invalida"],
)
def test_rejeita_respostas_invalidas(texto):
    with pytest.raises(ClaudeClientError):
        interpretar_resposta(texto)


# --- classificar_chamado -----------------------------------------------------

def test_classifica_chamado_com_api_simulada(fake_api):
    resultado = classificar_chamado("Projetor não liga")
    assert resultado["categoria"] == "Provas"
    assert len(fake_api.chamadas) == 1
    assert "Projetor não liga" in fake_api.chamadas[0]["messages"][0]["content"]


@pytest.mark.parametrize("descricao", ["", "   ", None])
def test_rejeita_descricao_vazia(fake_api, descricao):
    with pytest.raises(ClaudeClientError, match="vazia"):
        classificar_chamado(descricao)
    assert fake_api.chamadas == []


def test_rejeita_descricao_muito_longa(fake_api):
    with pytest.raises(ClaudeClientError, match="muito longa"):
        classificar_chamado("x" * (claude_client.TAMANHO_MAXIMO_DESCRICAO + 1))


def test_exige_chave_de_api(monkeypatch):
    monkeypatch.setattr(claude_client, "ANTHROPIC_API_KEY", None)
    with pytest.raises(ClaudeClientError, match="ANTHROPIC_API_KEY"):
        classificar_chamado("Projetor não liga")


def test_converte_erro_da_api(fake_api):
    fake_api.erro = anthropic.APIError("falha simulada", request=None, body=None)
    with pytest.raises(ClaudeClientError, match="Erro ao chamar a API"):
        classificar_chamado("Projetor não liga")
