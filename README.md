# NAT IA Triagem

Serviço de classificação automática de chamados técnicos usando a API do
Claude (Anthropic), integrado ao banco PostgreSQL do sistema NAT (FGV).

Projeto pessoal de estudo/portfólio, inspirado num problema real do dia a
dia de suporte: chamados chegam com descrição em texto livre, e a triagem
manual (definir categoria, prioridade e identificar informação faltante)
consome tempo do analista. Este serviço usa IA generativa para sugerir
essa triagem automaticamente.

## O que o projeto faz

1. Recebe a descrição de um chamado (via texto direto ou buscando por ID
   no banco do NAT)
2. Envia para a API do Claude com um prompt estruturado
3. Recebe de volta: categoria, prioridade, resumo e informações faltantes
4. Expõe tudo isso como uma API REST (FastAPI), pronta para ser chamada
   por outro sistema — como o próprio NAT, no momento de abertura do
   chamado

## Stack

- **Python 3.11+**
- **FastAPI** — API REST
- **Anthropic SDK** — chamadas ao Claude
- **PostgreSQL** (psycopg2) — mesmo banco do sistema NAT
- **python-dotenv** — configuração via variáveis de ambiente

## Como rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# edite o .env com sua chave da Anthropic e dados do PostgreSQL

# 3. Testar a integração com o Claude (sem precisar do banco)
python tests/test_manual.py

# 4. Subir a API
uvicorn main:app --reload --port 8000
```

Documentação interativa da API (Swagger): `http://localhost:8000/docs`

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Status do serviço |
| POST | `/classificar` | Classifica uma descrição de chamado enviada diretamente no corpo da requisição |
| POST | `/classificar/{chamado_id}` | Busca o chamado no PostgreSQL pelo ID, classifica e, opcionalmente, salva o resultado de volta no banco (`?salvar=true`) |

### Exemplo de uso

```bash
curl -X POST http://localhost:8000/classificar \
  -H "Content-Type: application/json" \
  -d '{"descricao": "Projetor da sala PA-S45 não liga, prova é amanhã"}'
```

Resposta:
```json
{
  "categoria": "Provas",
  "prioridade": "Alta",
  "resumo": "Projetor com defeito na sala de prova agendada para o dia seguinte",
  "info_faltante": "nenhuma"
}
```

## Status e próximos passos

- [x] Classificação via Claude funcionando isoladamente
- [x] API REST com FastAPI
- [x] Integração com PostgreSQL para buscar chamados reais
- [ ] Ajustar nomes de tabela/colunas no `database.py` para bater com o
      schema exato de produção do NAT
- [ ] Testes automatizados (pytest) além do script manual
- [ ] Autenticação na API antes de expor em rede
- [ ] Adicionar endpoint para classificar chamados em lote

## Observação sobre credenciais

Nenhuma chave de API ou senha de banco está no código — tudo vem de
variáveis de ambiente via `.env` (arquivo local, nunca commitado — veja
`.gitignore`). Use `.env.example` como referência.
