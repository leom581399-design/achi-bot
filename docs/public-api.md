# API Pública

A API pública é o serviço `artifacts/api-server`, exposto sob `/api`. Ela lê o mesmo PostgreSQL usado pelas migrations PHP e exige um bearer token.

## Configuração

Defina o secret `PUBLIC_API_TOKEN` com um valor longo e aleatório. O token não possui valor padrão e nunca deve ser commitado.

```bash
curl -X POST /api/auth/verify \
  -H 'content-type: application/json' \
  -d '{"token":"SEU_TOKEN"}'
```

Todas as rotas protegidas usam:

```text
Authorization: Bearer SEU_TOKEN
```

## Endpoints

- `GET /api/healthz` — saúde do serviço, sem autenticação.
- `POST /api/auth/verify` — valida o token.
- `GET /api/overview` — totais e atividade recente.
- `GET /api/groups` — grupos gerenciados.
- `GET /api/bans` / `DELETE /api/bans/:id` — bans.
- `GET /api/warns` / `DELETE /api/warns/:id` — advertências.
- `GET /api/notes` / `DELETE /api/notes/:id` — notas.
- `GET /api/stats` — atividade de mensagens e ranking.
- `GET /api/fedbans` — bans de federação.
- `GET /api/modules` — módulos disponíveis.

## Plugins Composer

Um pacote externo pode declarar:

```json
{
  "type": "telegram-bot-module",
  "extra": {
    "telegram-bot-module": "Vendor\\Package\\PackageModule"
  }
}
```

A classe deve implementar `App\Core\Contracts\ModuleInterface`. Após `composer install`, o módulo é descoberto automaticamente. Para adicionar comandos CLI opcionais, a classe pode expor `getConsoleCommands(): array<string, class-string>`.