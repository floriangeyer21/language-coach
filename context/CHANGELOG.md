# Project Change Log

A running, high-level record of what has been done to this project — planning,
feature work, infra, and tooling. Newest entries at the top. Keep entries short
(one line each); this is a memory aid for future work, not a detailed history.
For the *why* and *how*, consult the specs under `context/spec/`.

## 2026-07-03

- **AWS deployment (planned + scaffolded)** — Wrote deploy spec
  (`features/new/aws-deployment.md`) and all artifacts: Dockerfiles (API +
  Next.js standalone web), Terraform for App Runner ×2 + RDS MySQL (private,
  encrypted, backed up) + ECR + Secrets Manager + VPC/NAT + IAM, a
  `bootstrap.sh`/`deploy.sh`, GitHub Actions push-to-deploy, and a runbook
  (`infra/README.md`). Not yet provisioned (awaiting local tooling + OpenAI key).
- **AWS deploy config** — Chose region `eu-central-1`, dropped the NAT gateway to
  save cost (RDS now publicly accessible, credential-protected — see spec
  tradeoff), and stored AWS creds locally under the `languagecoach` profile.
- **CI-driven bootstrap** — Local Docker/Terraform blocked (macOS CLT install
  failing), so added a GitHub Actions `bootstrap.yml` that provisions everything
  on the runner with S3 remote state; set repo secrets/vars. Deploy workflow
  guarded to no-op until bootstrap runs.
- **Git & GitHub** — Initialized git repo, added `.gitignore` (excludes `.env`
  secrets, `node_modules`, `.data/`), made the initial commit, installed `gh`
  CLI, and pushed to a public GitHub repo (`language-coach`).
- **MySQL datasource** — Wrote spec (`spec/data/mysql.md`) and implemented the
  MySQL storage backend (SQLAlchemy Core + aiomysql) behind the same
  `StorageBackend` interface as the file backend; verified end-to-end incl.
  durability across restart.
- **Implementation** — Built the full app from spec: FastAPI backend
  (auth/chat/memory/vocabulary), file storage backend, tiered AI memory,
  OpenAI integration, and the Next.js dark-themed web client. Verified in the
  browser. (AI chat blocked externally by OpenAI account quota.)
- **Specs** — Wrote all v1 specs: overview, API (auth/chat/memory/vocabulary),
  config/env layer, web design (dark theme), and four feature specs
  (user management, memory management, chat-with-AI, vocabulary).
- **Project setup** — Established the spec-driven structure: `context/spec/`,
  the `features/new` → `features/existing` lifecycle, and `app/` as the sole
  code location. Recorded these rules in `CLAUDE.md`.
