# Configuração de Variáveis de Ambiente

Este projeto usa variáveis de ambiente para configurar conexões com banco de dados e outras configurações sensíveis.

## Configuração Local

1. Copie o arquivo `env.example` para `.env`:
   ```bash
   cp env.example .env
   ```

2. Edite o arquivo `.env` com suas configurações locais:
   ```env
   # Para desenvolvimento local
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=altalocal
   DB_USER=postgres
   DB_PASSWORD=sua_senha_local
   DB_HOST=localhost
   DB_PORT=5432
   ```

## Configuração no Render (Produção)

No painel do Render, configure as seguintes variáveis de ambiente:

### Banco de Dados
- `DB_ENGINE`: `django.db.backends.postgresql`
- `DB_NAME`: `alta_db_prod_2`
- `DB_USER`: `alta_db_prod_2_user`
- `DB_PASSWORD`: `3rp700XExUxgrfqCIPgvChVMOwWUyQUB`
- `DB_HOST`: `dpg-d088hrfdiees7391qrc0-a.oregon-postgres.render.com`
- `DB_PORT`: `5432`

### Outras Configurações
- `DJANGO_SECRET_KEY`: Sua chave secreta do Django
- `OPENAI_API_KEY`: Sua chave da API OpenAI
- `EMAIL_HOST_USER`: `ricardo.pasqualino@gmail.com`
- `EMAIL_HOST_PASSWORD`: Senha de app do Gmail
- `DEFAULT_FROM_EMAIL`: `ricardo.pasqualino@gmail.com`
- `RENDER_EXTERNAL_URL`: `alta-env.onrender.com`

## Segurança

- O arquivo `.env` está no `.gitignore` e não será versionado
- Nunca commite senhas ou chaves de API no código
- Use sempre variáveis de ambiente em produção

## Como Funciona

O projeto usa `python-decouple` para carregar as variáveis do arquivo `.env` localmente e das variáveis de ambiente do sistema em produção.

Exemplo de uso no código:
```python
from decouple import config

DATABASE_NAME = config('DB_NAME', default='default_name')
``` 