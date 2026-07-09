# Production Deployment

This deployment runs:

- PostgreSQL with pgvector, private Docker network only
- Redis with append-only persistence, private Docker network only
- FastAPI backend on the private Docker network
- Static React build served by Nginx on `STANDARD_OPS_HTTP_PORT`

## Server Prerequisites

- Linux server with Docker Engine and Docker Compose plugin
- Ports 80/443 opened as needed
- A domain pointed to the server if HTTPS is required

## First Deploy

```bash
git clone https://github.com/wangzirin/kefu.git
cd kefu
cp deploy/production.env.example deploy/production.env
```

Edit `deploy/production.env` on the server:

- Set `STANDARD_OPS_ALLOWED_ORIGINS` to the public origin, for example `https://kefu.example.com`
- Set a long random `STANDARD_OPS_POSTGRES_PASSWORD`
- Keep `STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false`
- Keep `OUTBOX_EXTERNAL_WRITE_ENABLED=false` until real channel sending is approved
- Fill model provider API keys only on the server

Start the stack:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/production.env up -d --build
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/production.env ps
curl -fsS http://127.0.0.1/health
```

The backend runs `alembic upgrade head` before starting.

## Update Deploy

```bash
cd kefu
git pull
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/production.env up -d --build
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/production.env ps
```

## HTTPS

The included compose file serves HTTP. For HTTPS, put Caddy, Nginx Proxy Manager, a cloud load balancer, or another TLS reverse proxy in front of `STANDARD_OPS_HTTP_PORT`.

## Optional Worker

The trusted inbound worker is disabled by default. Start it only after tenant/user ownership and real inbound boundaries are confirmed:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/production.env --profile worker up -d --build
```

## Backups

Back up the Docker volumes before updates:

- `standard_ops_prod_postgres`
- `standard_ops_prod_redis`
- `standard_ops_prod_backend_data`

## Known Dependency Risk

`npm audit` currently reports high-severity advisories for `xlsx` with no patched npm release available. Treat spreadsheet imports as trusted-operator-only until the dependency is replaced or patched upstream.
