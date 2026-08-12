"""
database.py

Camada de acesso ao PostgreSQL — reutiliza o mesmo banco do sistema NAT.

IMPORTANTE: os nomes de tabela/colunas abaixo (TABELA_CHAMADOS, "id",
"descricao") são um ponto de partida razoável baseado no NAT_RESUMO.md.
Ajuste as queries para bater exatamente com o schema real do banco em
produção antes de rodar contra o PostgreSQL de verdade.
"""
import psycopg2
import psycopg2.extras
from config import DB_CONFIG, TABELA_CHAMADOS


class DatabaseError(Exception):
    """Erro de conexão ou consulta ao banco."""


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
    query = f"""
        SELECT id, descricao, setor, tipo, local, equipamento, data_abertura
        FROM {TABELA_CHAMADOS}
        WHERE id = %s
    """
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
    Assume colunas 'categoria_sugerida' e 'prioridade_sugerida' — crie-as
    no schema do NAT (ALTER TABLE) antes de usar esta função em produção.
    """
    query = f"""
        UPDATE {TABELA_CHAMADOS}
        SET categoria_sugerida = %s,
            prioridade_sugerida = %s
        WHERE id = %s
    """
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
