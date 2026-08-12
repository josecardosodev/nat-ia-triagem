"""
test_manual.py

Teste manual rápido — roda a classificação contra alguns chamados de
exemplo (baseados nas categorias reais do NAT) para validar que a
integração com o Claude está funcionando antes de conectar no banco.

Rodar:
    python tests/test_manual.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_client import classificar_chamado, ClaudeClientError

CHAMADOS_EXEMPLO = [
    "Projetor da sala PA-S45 não liga, prova é amanhã de manhã",
    "Preciso resetar a senha do Office 365 do professor Carlos",
    "Câmera do laboratório LEPI-501 travou durante a gravação da aula híbrida",
    "Som do auditório está com chiado, evento institucional começa em 2 horas",
    "Aluno reportou que o ar condicionado da sala ITA-S201 não está gelando",
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
