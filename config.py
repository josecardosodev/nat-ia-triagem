"""
Configurações do projeto — IA Triagem de Chamados

Todas as credenciais vêm de variáveis de ambiente (nunca hardcoded no código).
Crie um arquivo .env na raiz do projeto (veja .env.example) e nunca o suba pro Git.
"""
import os

from dotenv import load_dotenv

load_dotenv()

# --- API Anthropic (Claude) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# --- PostgreSQL do sistema de chamados ---
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "chamados"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# Nome da tabela de chamados. Ajuste para o nome real do seu schema.
TABELA_CHAMADOS = os.getenv("TABELA_CHAMADOS", "chamados")
