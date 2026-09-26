"""
classificar_exemplos.py

Roda a classificação contra alguns chamados de exemplo, chamando a API real
do Claude. Serve para validar a integração antes de conectar no banco.

Requer ANTHROPIC_API_KEY no .env (consome créditos da API).

Rodar a partir da raiz do projeto:
    python scripts/classificar_exemplos.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_client import ClaudeClientError, classificar_chamado  # noqa: E402

CHAMADOS_EXEMPLO = [
    "Projetor da sala 204 não liga, prova é amanhã de manhã",
    "Preciso resetar a senha do Office 365 de um professor",
    "Câmera do laboratório travou durante a gravação da aula híbrida",
    "Som do auditório está com chiado, evento institucional começa em 2 horas",
    "Aluno reportou que o ar condicionado da sala 301 não está gelando",
]

if __name__ == "__main__":
    for descricao in CHAMADOS_EXEMPLO:
        print("=" * 70)
        print(f"Descrição: {descricao}")
        try:
            resultado = classificar_chamado(descricao)
            print(json.dumps(resultado, indent=2, ensure_ascii=False))
        except ClaudeClientError as e:
            print(f"ERRO: {e}")
        print()
