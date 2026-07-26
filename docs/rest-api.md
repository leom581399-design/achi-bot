# API REST — Telegram Group Manager V15

A API REST permite a integração de sistemas externos com o bot, fornecendo acesso a estatísticas, listas de banimentos, grupos e notas.

## Autenticação

A API utiliza autenticação baseada em **Bearer Token**.

- **Header:** `Authorization: Bearer <seu_token>`
- **Como obter o token:** O token é o hash MD5 da variável `DASHBOARD_PASSWORD_HASH` configurada no ambiente.

```bash
# Exemplo de geração de token via PHP
php -r "echo md5(getenv('DASHBOARD_PASSWORD_HASH'));"
```

## Endpoints

Todos os endpoints retornam JSON e seguem o formato:
```json
{
  "status": "ok",
  "timestamp": 1690000000,
  "data": [...]
}
```

### 1. Estatísticas Gerais
`GET /api.php/stats`
Retorna o total de grupos, utilizadores únicos, total de mensagens e os top grupos.

### 2. Lista de Banimentos
`GET /api.php/bans?q=pesquisa`
Retorna os últimos 50 banimentos. O parâmetro opcional `q` permite filtrar por User ID ou motivo.

### 3. Lista de Grupos
`GET /api.php/groups`
Retorna a lista de todos os grupos onde o bot está presente.

### 4. Notas
`GET /api.php/notes?chat_id=12345`
Retorna as notas guardadas. O parâmetro opcional `chat_id` filtra as notas de um grupo específico.

## Exemplos de Uso

### Curl
```bash
curl -X GET "https://seu-bot.com/api.php/stats" \
     -H "Authorization: Bearer <seu_token>"
```

### Python
```python
import requests

headers = {"Authorization": "Bearer <seu_token>"}
response = requests.get("https://seu-bot.com/api.php/stats", headers=headers)
print(response.json())
```
