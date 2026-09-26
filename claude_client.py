"""
claude_client.py

Camada de integração com a API da Anthropic (Claude).

Transforma a descrição livre de um chamado (do jeito que o usuário realmente
digita) em dados estruturados que o sistema consegue usar programaticamente:
categoria, prioridade, resumo e informações faltantes.
"""
import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

CATEGORIAS_VALIDAS = [
    "Audiovisual",
    "Laboratório",
    "TI/Infraestrutura",
    "Provas",
    "Manutenção",
    "Eventos",
]

PRIORIDADES_VALIDAS = ["Baixa", "Média", "Alta"]

CAMPOS_ESPERADOS = {"categoria", "prioridade", "resumo", "info_faltante"}

TAMANHO_MAXIMO_DESCRICAO = 4000

PROMPT_TEMPLATE = """Você é um assistente de triagem de chamados técnicos de uma equipe de
suporte audiovisual, laboratório e TI.

Categorias válidas: {categorias}
Prioridades válidas: {prioridades}

Analise a descrição do chamado abaixo e responda SOMENTE com um JSON válido
(sem texto antes ou depois, sem markdown, sem ```), contendo exatamente estes campos:

- "categoria": uma das categorias válidas listadas acima
- "prioridade": uma das prioridades válidas listadas acima
- "resumo": uma frase curta e objetiva do problema
- "info_faltante": o que falta para o analista entender o chamado, ou "nenhuma"

Descrição do chamado:
\"\"\"{descricao}\"\"\"
"""

_CERCA_MARKDOWN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class ClaudeClientError(Exception):
    """Erro ao chamar a API do Claude ou ao interpretar a resposta."""


def montar_prompt(descricao: str) -> str:
    """Monta o prompt enviado ao modelo a partir da descrição do chamado."""
    return PROMPT_TEMPLATE.format(
        categorias=", ".join(CATEGORIAS_VALIDAS),
        prioridades=", ".join(PRIORIDADES_VALIDAS),
        descricao=descricao.strip(),
    )


def interpretar_resposta(texto: str) -> dict:
    """
    Converte o texto devolvido pelo modelo em dicionário e valida o conteúdo.

    Tolera a resposta vir envolta em bloco de código markdown (```json ... ```),
    o que às vezes acontece mesmo pedindo o contrário no prompt.
    """
    limpo = _CERCA_MARKDOWN.sub("", texto.strip()).strip()

    try:
        resultado = json.loads(limpo)
    except json.JSONDecodeError as e:
        raise ClaudeClientError(f"Resposta do Claude não veio em JSON válido: {texto}") from e

    if not isinstance(resultado, dict):
        raise ClaudeClientError(f"Resposta do Claude não é um objeto JSON: {resultado}")

    faltando = CAMPOS_ESPERADOS - resultado.keys()
    if faltando:
        raise ClaudeClientError(f"Resposta do Claude incompleta, faltam: {sorted(faltando)}")

    if resultado["categoria"] not in CATEGORIAS_VALIDAS:
        raise ClaudeClientError(f"Categoria inválida retornada: {resultado['categoria']!r}")

    if resultado["prioridade"] not in PRIORIDADES_VALIDAS:
        raise ClaudeClientError(f"Prioridade inválida retornada: {resultado['prioridade']!r}")

    return {campo: resultado[campo] for campo in CAMPOS_ESPERADOS}


def classificar_chamado(descricao: str) -> dict:
    """
    Envia a descrição de um chamado para o Claude e retorna um dicionário
    com categoria, prioridade, resumo e informação faltante.

    Levanta ClaudeClientError se a chave de API não estiver configurada,
    se a descrição for inválida, se a chamada falhar, ou se a resposta
    não vier no formato esperado.
    """
    if not descricao or not descricao.strip():
        raise ClaudeClientError("Descrição do chamado vazia.")

    if len(descricao) > TAMANHO_MAXIMO_DESCRICAO:
        raise ClaudeClientError(
            f"Descrição muito longa (máximo {TAMANHO_MAXIMO_DESCRICAO} caracteres)."
        )

    if not ANTHROPIC_API_KEY:
        raise ClaudeClientError("ANTHROPIC_API_KEY não configurada. Verifique seu arquivo .env.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        resposta = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": montar_prompt(descricao)}],
        )
    except anthropic.APIError as e:
        raise ClaudeClientError(f"Erro ao chamar a API do Claude: {e}") from e

    return interpretar_resposta(resposta.content[0].text)


if __name__ == "__main__":
    # Teste rápido manual: python claude_client.py
    exemplo = "Projetor da sala 204 não liga, prova é amanhã de manhã"
    print(f"Descrição: {exemplo}\n")
    print(json.dumps(classificar_chamado(exemplo), indent=2, ensure_ascii=False))
