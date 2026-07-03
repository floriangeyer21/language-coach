# Feature: AWS Deployment (App Runner + RDS MySQL)

Deploy LanguageCoach to AWS so the API and web run remotely with a safely-stored
managed database, and any code change can be shipped by pushing to git.

Status: planned. Move to `features/existing/` once the first successful deploy is
verified live.

## Goals

- **Remote, always-on** API and web, served over HTTPS with no server management.
- **Managed, private, backed-up** MySQL (the app's production datasource — see
  `context/spec/data/mysql.md`).
- **No secrets in the repo.** All secrets live in AWS Secrets Manager.
- **Push-to-deploy** updates for any part of the app via GitHub Actions.
- **Reproducible / tear-downable** infra defined as code (Terraform).

## Architecture

```
Browser ──HTTPS──▶ App Runner: web (Next.js standalone, port 3000)
                        │  (NEXT_PUBLIC_API_BASE_URL baked at build time)
                        ▼
                   App Runner: api (uvicorn, port 8000)
                        │  via VPC Connector (egress into private subnets)
                        ▼
                   RDS MySQL 8 (private subnets, encrypted, auto-backups)

   ECR: languagecoach-api, languagecoach-web  (image registry)
   Secrets Manager: openai_api_key, jwt_secret, database_url
```

### Components

- **ECR** — two private repos hold the built container images.
- **RDS MySQL 8.0** — `db.t4g.micro` (smallest), single-AZ for v1, storage
  encrypted (KMS), automated backups (7-day retention), **not publicly
  accessible**. Lives in private subnets of the deployment VPC.
- **App Runner (API)** — pulls `languagecoach-api:latest` from ECR, listens on
  8000. Reaches RDS through a **VPC Connector** (App Runner egress into the VPC).
  Reads runtime config from Secrets Manager + plain env vars.
- **App Runner (web)** — pulls `languagecoach-web:latest`, listens on 3000.
  Public. Its public URL is the app entry point.
- **Secrets Manager** — `OPENAI_API_KEY`, `JWT_SECRET`, `DATABASE_URL` (full
  `mysql+aiomysql://user:pass@rds-endpoint:3306/languagecoach`). App Runner
  injects these as env vars via `RuntimeEnvironmentSecrets`.
- **IAM** — App Runner *access role* (pull from ECR) and *instance role* (read
  the three secrets). A deploy user/role for CI with least-privilege push+deploy.

### Networking (cost-optimized, no NAT)

- A dedicated VPC with 2 **public** subnets across 2 AZs (RDS subnet group needs
  two AZs).
- **RDS is publicly accessible**, protected by a strong generated password (and,
  as a follow-up, TLS). App Runner's **default public egress** reaches both
  OpenAI and the RDS endpoint — so there is **no NAT gateway and no VPC
  connector**, saving ~$32/mo.
- Tradeoff: RDS port 3306 is reachable network-wide (App Runner egress IPs are
  not fixed, so it can't be pinned by security group). This is the deliberate
  cost/isolation tradeoff chosen for v1. To restore full isolation later,
  reintroduce private subnets + NAT + an App Runner VPC connector and set RDS
  `publicly_accessible = false`.
- Both App Runner services are public; CORS restricts the API to the web origin.

## Configuration mapping

App-level config is unchanged (`context/spec/config.md`); only the *source* of
values changes — Secrets Manager / App Runner env instead of `.env`:

| Variable | Source in AWS | Value |
|----------|---------------|-------|
| `STORAGE_BACKEND` | App Runner env | `mysql` |
| `DATABASE_URL` | Secrets Manager | RDS endpoint DSN |
| `OPENAI_API_KEY` | Secrets Manager | rotated key |
| `JWT_SECRET` | Secrets Manager | fresh 32+ byte random |
| `OPENAI_CHAT_MODEL` / `OPENAI_MEMORY_MODEL` | App Runner env | as today |
| `JWT_ALGORITHM` / `ACCESS_TOKEN_TTL_MIN` | App Runner env | as today |
| `CORS_ORIGINS` | App Runner env | web App Runner HTTPS URL |
| `NEXT_PUBLIC_API_BASE_URL` (web) | build arg | api App Runner HTTPS URL |

Schema is created automatically: on startup the API runs `metadata.create_all`
(idempotent) — no migration step for v1 (see `data/mysql.md`).

## Build & image contract

- **API image** (`app/Server/Dockerfile`): `python:3.12-slim`, install
  `requirements.txt`, run `uvicorn main:app --host 0.0.0.0 --port 8000`.
- **Web image** (`app/Web/Dockerfile`): multi-stage Node 20 build producing a
  Next.js **standalone** server (`output: "standalone"`), run `node server.js`
  on port 3000. `NEXT_PUBLIC_API_BASE_URL` is a **build arg** (baked in), so the
  API URL must be known at web-build time.

## Deploy ordering (chicken-and-egg)

`NEXT_PUBLIC_API_BASE_URL` is baked into the web image, but the API's URL only
exists after the API service is created. Resolution:

1. `terraform apply` creates ECR, RDS, secrets, IAM, VPC connector, and the
   **API** App Runner service (from a placeholder/first image).
2. Read the API service URL (Terraform output).
3. Build & push the **web** image with `--build-arg NEXT_PUBLIC_API_BASE_URL=<api url>`.
4. Create/deploy the **web** App Runner service.
5. Set the API's `CORS_ORIGINS` to the web URL (second apply) and redeploy API.

CI encodes this: the workflow passes the API URL (a Terraform output / known
custom domain) as the web build arg.

## Update / redeploy workflow (push-to-deploy)

`.github/workflows/deploy.yml`, triggered on push to `main`:

1. Configure AWS creds from GitHub secrets (`AWS_ACCESS_KEY_ID`,
   `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`).
2. `docker build` + `docker push` the API and web images to ECR
   (tagged with the commit SHA **and** `latest`).
3. `aws apprunner start-deployment` for each changed service (App Runner can also
   auto-deploy on new `latest` push; explicit start-deployment is used for
   determinism).

Infra changes (RDS size, new env var, etc.) are applied by re-running
`terraform apply` — locally or in a separate manual workflow — not on every push.

## Cost & lifecycle

- Rough idle cost (no NAT): RDS `db.t4g.micro` (~$15/mo + storage) + 2 App Runner
  services (~$5–10/mo each idle + per-request compute) ≈ **$25–35/mo**. Not
  free-tier overall.
- `terraform destroy` tears everything down. RDS `deletion_protection` is ON in
  prod; a final snapshot is taken on destroy unless explicitly skipped.

## Security requirements

- Repo never contains real secrets; `.gitignore` already excludes `.env`.
- The previously-pasted OpenAI key is compromised and MUST be rotated before it
  is placed in Secrets Manager.
- `JWT_SECRET` is regenerated for the deployed environment (dev value not reused).
- RDS is private, encrypted at rest, TLS in transit (aiomysql SSL connect args).
- CI uses a least-privilege IAM principal (ECR push + App Runner deploy +
  read the deploy state), not root account keys.

## Out of scope (v1)

- Custom domain + ACM certificate (App Runner default `*.awsapprunner.com` URLs
  are used first; custom domain is a follow-up).
- Multi-AZ RDS / read replicas / autoscaling tuning.
- Migration framework (schema is create_all for now).
- Blue/green or canary deploys beyond App Runner's built-in rolling deploy.
