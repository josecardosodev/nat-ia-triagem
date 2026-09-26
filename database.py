"""
database.py

Camada de acesso ao PostgreSQL do sistema de chamados.

Os nomes de colunas abaixo ("id", "descricao", ...) são um ponto de partida.
Ajuste as queries para bater com o schema real do seu banco antes de usar
em produção. O nome da tabela vem da variável de ambiente TABELA_CHAMADOS.
"""
import psycopg2
import psycopg2.extras
from psycopg2 import sql

from config import DB_CONFIG, TABELA_CHAMADOS


class DatabaseError(Exception):
    """Erro de conexão ou consulta ao banco."""


def _tabela() -> sql.Identifier:
    # sql.Identifier escapa o nome da tabela corretamente, evitando SQL
    # injection caso a variável de ambiente contenha algo inesperado.
    return sql.Identifier(TABELA_CHAMADOS)


def _conectar():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        raise DatabaseError(f"Não foi possível conectar ao PostgreSQL: {e}") from e


def buscar_chamado_por_id(chamado_id: int) -> dict | None:
    """
    Busca um chamado pelo ID e retorna seus dados como dicionário.
    Retorna None se o chamado não existir.
    """
    query = sql.SQL(
        "SELECT id, descricao, setor, tipo, local, equipamento, data_abertura "
        "FROM {tabela} WHERE id = %s"
    ).format(tabela=_tabela())

    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (chamado_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except psycopg2.Error as e:
        raise DatabaseError(f"Erro ao consultar chamado {chamado_id}: {e}") from e
    finally:
        conn.close()


def salvar_classificacao(chamado_id: int, categoria: str, prioridade: str) -> None:
    """
    Grava o resultado da classificação da IA de volta no chamado.

    Requer as colunas 'categoria_sugerida' e 'prioridade_sugerida' na tabela:
        ALTER TABLE chamados ADD COLUMN categoria_sugerida TEXT,
                             ADD COLUMN prioridade_sugerida TEXT;
    """
    query = sql.SQL(
        "UPDATE {tabela} SET categoria_sugerida = %s, prioridade_sugerida = %s WHERE id = %s"
    ).format(tabela=_tabela())

    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(query, (categoria, prioridade, chamado_id))
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Erro ao salvar classificação: {e}") from e
    finally:
        conn.close()
