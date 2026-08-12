"""
claude_client.py

Camada de integração com a API da Anthropic (Claude).
Responsável por transformar a descrição livre de um chamado em dados
estruturados (categoria, prioridade, resumo, informações faltantes).

Este é o núcleo de "IA Generativa aplicada a automação de processos"
do projeto: pega texto não estruturado (como um analista realmente digita
um chamado) e devolve algo que o sistema consegue usar programaticamente.
"""
import json
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

PROMPT_TEMPLATE = """Você é um assistente de triagem de chamados técnicos de uma equipe de
suporte audiovisual, laboratório e TI.

Categorias válidas: {categorias}

Analise a descrição do chamado abaixo e responda SOMENTE com um JSON válido
(sem texto antes ou depois, sem markdown, sem ```), contendo exatamente estes campos:

- "categoria": uma das categorias válidas listadas acima
- "prioridade": "Baixa", "Média" ou "Alta"
- "resumo": uma frase curta e objetiva do problema
- "info_faltante": o que falta para o analista entender o chamado, ou "nenhuma"

Descrição do chamado:
\"\"\"{descricao}\"\"\"
"""


class ClaudeClientError(Exception):
    """Erro ao chamar a API do Claude ou ao interpretar a resposta."""


def _montar_prompt(descricao: str) -> str:
    return PROMPT_TEMPLATE.format(
        categorias=", ".join(CATEGORIAS_VALIDAS),
        descricao=descricao.strip(),
    )


def classificar_chamado(descricao: str) -> dict:
    """
    Envia a descrição de um chamado para o Claude e retorna um dicionário
    estruturado com categoria, prioridade, resumo e informação faltante.

    Levanta ClaudeClientError se a chave de API não estiver configurada,
    se a chamada falhar, ou se a resposta não vier em JSON válido.
    """
    if not ANTHROPIC_API_KEY:
        raise ClaudeClientError(
            "ANTHROPIC_API_KEY não configurada. Verifique seu arquivo .env."
        )

    if not descricao or not descricao.strip():
        raise ClaudeClientError("Descrição do chamado vazia.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        resposta = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": _montar_prompt(descricao)}],
        )
    except anthropic.APIError as e:
        raise ClaudeClientError(f"Erro ao chamar a API do Claude: {e}") from e

    texto = resposta.content[0].text.strip()

    try:
        resultado = json.loads(texto)
    except json.JSONDecodeError as e:
        raise ClaudeClientError(
            f"Resposta do Claude não veio em JSON válido: {texto}"
        ) from e

    # Validação simples do formato de resposta
    campos_esperados = {"categoria", "prioridade", "resumo", "info_faltante"}
    if not campos_esperados.issubset(resultado.keys()):
        raise ClaudeClientError(f"Resposta do Claude incompleta: {resultado}")

    return resultado


if __name__ == "__main__":
    # Teste rápido manual: python claude_client.py
    exemplo = "Projetor da sala PA-S45 não liga, prova é amanhã de manhã"
    print(f"Descrição: {exemplo}\n")
    print(json.dumps(classificar_chamado(exemplo), indent=2, ensure_ascii=False))
