# API Pokemon

API REST desenvolvida com FastAPI (Python 3.10) que consome dados da PokeAPI com cache local e Redis opcional, além de CRUD local persistido em SQLite via SQLAlchemy.

## Funcionalidades

- Consumo da PokeAPI: https://pokeapi.co/api/v2/pokemon/
- Endpoints:
  - `GET /pokemons?page=1&size=20`
  - `GET /pokemons/{id}`
  - `GET /pokemons/name/{name}`
  - `GET /pokemons/type/{type}?page=1&size=20`
  - `GET /pokemons/local?page=1&size=20`
  - `POST /pokemons`
  - `PUT /pokemons/{id}`
  - `DELETE /pokemons/{id}`
- Paginação com metadados: total, page, size, next, previous
- Cache em memória + Redis opcional com fallback
- Persistência relacional local com SQLite e SQLAlchemy async
- Tratamento de exceções personalizado
- Autenticação simples via API key (`x-api-key`)
- Logs estruturados em JSON
- Validação com Pydantic
- Testes com pytest e relatório de cobertura (pytest-cov)
- Docker + Docker Compose
- CI/CD com GitHub Actions + deploy automático no Render

## Resposta JSON (exemplo)

```json
{
  "name": "pikachu",
  "id": 25,
  "height": 4,
  "weight": 60,
  "types": ["electric"],
  "sprites": {
    "front_default": "https://...",
    "back_default": "https://..."
  }
}
```

## Paginação (exemplo)

```json
{
  "data": [
    {
      "name": "pikachu",
      "id": 25,
      "height": 4,
      "weight": 60,
      "types": ["electric"],
      "sprites": {
        "front_default": "https://...",
        "back_default": "https://..."
      }
    }
  ],
  "pagination": {
    "total": 1302,
    "page": 1,
    "size": 20,
    "next": "/pokemons?page=2&size=20",
    "previous": null
  }
}
```

## CRUD local

Os endpoints `POST`, `PUT` e `DELETE` operam sobre registros persistidos localmente no banco configurado em `DATABASE_URL`.

Exemplo de criação:

```bash
curl -X POST "http://localhost:8000/pokemons" \
  -H "x-api-key: 123456789" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "testmon",
    "height": 10,
    "weight": 99,
    "types": ["normal"],
    "sprites": {
      "front_default": "https://img/testmon-front.png",
      "back_default": "https://img/testmon-back.png"
    }
  }'
```

Exemplo de atualização parcial:

```bash
curl -X PUT "http://localhost:8000/pokemons/1" \
  -H "x-api-key: 123456789" \
  -H "Content-Type: application/json" \
  -d '{"name": "testmon-updated", "weight": 150}'
```

Exemplo de remoção:

```bash
curl -X DELETE "http://localhost:8000/pokemons/1" \
  -H "x-api-key: 123456789"
```

## Como rodar localmente (sem Docker)

1. Crie e ative ambiente virtual.
2. Instale dependências:

```bash
pip install -r requirements/base.txt
```

3. Copie `.env.example` para `.env` e ajuste os valores.
4. Inicie a API:

```bash
uvicorn app.main:app --reload
```

## Como rodar com Docker

1. Crie arquivo `.env` a partir de `.env.example`.
2. Suba os containers:

```bash
docker compose up --build
```

### Banco local

O valor padrão de `DATABASE_URL` é `sqlite+aiosqlite:///./pokemon.db`. Se quiser trocar para outro banco, ajuste a variável de ambiente antes de subir a aplicação.

## Testes e cobertura

Instale dependências de teste:

```bash
pip install -r requirements/test.txt
```

Execute testes com cobertura:

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

## Autenticação

Os endpoints de API em `/pokemons*` exigem header:

```http
x-api-key: <SUA_API_KEY>
```

Passo a passo:

1. Copie `.env.example` para `.env`.
2. Defina `API_KEY` no `.env`, por exemplo: `API_KEY=123456789`.
3. Reinicie a aplicação após alterar `.env`.
4. Para testar no Swagger (`/docs`):
  - clique em **Authorize**
  - informe a chave no campo `x-api-key`
  - execute os endpoints `/pokemons*`

Exemplo com curl:

```bash
curl -H "x-api-key: 123456789" "http://localhost:8000/pokemons?page=1&size=20"
```

## Documentação automática

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`

## CI/CD

- Workflow de CI em `.github/workflows/ci.yml`
  - Instala dependências
  - Executa lint
  - Executa testes
  - Valida cobertura
- Workflow de deploy em `.github/workflows/deploy.yml`
  - Disparado por push na `main`
  - Aciona Deploy Hook do Render
  - Executa health check pós-deploy

## Deploy no Render

Configure secrets no GitHub Actions:

- `RENDER_DEPLOY_HOOK_URL`
- `RENDER_APP_URL`
- `RENDER_API_KEY_FOR_HEALTH`

## Link de produção

- Definir após publicar no Render: `https://api-pokemon-1mfb.onrender.com`
