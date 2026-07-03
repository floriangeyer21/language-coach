# AWS Deployment Runbook

Deploys LanguageCoach to AWS: App Runner (API + web), RDS MySQL (private,
encrypted, backed up), ECR, Secrets Manager — all via Terraform. See the spec:
`context/spec/features/new/aws-deployment.md`.

## Layout

```
infra/
  terraform/        # all infrastructure as code
  bootstrap.sh      # first-time ordered deploy (run once)
  deploy.sh         # manual redeploy of images (steady state)
.github/workflows/deploy.yml   # push-to-deploy CI/CD
app/Server/Dockerfile
app/Web/Dockerfile
```

---

## Part A — one-time setup (you)

### 1. Install tooling (macOS)

```bash
xcode-select --install       # Command Line Tools (required by Homebrew on Sequoia)
brew install hashicorp/tap/terraform awscli
brew install colima docker   # lightweight Docker without Docker Desktop
colima start                 # starts the Docker daemon
```

### 2. Create an IAM deploy user

In the AWS console → IAM → Users → create `languagecoach-deployer` with
programmatic access. Attach an inline policy (least-privilege for this stack):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": [
        "ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage",
        "ecr:PutImage", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload", "ecr:CreateRepository",
        "ecr:DescribeRepositories", "ecr:PutLifecyclePolicy" ],
      "Resource": "*" },
    { "Effect": "Allow", "Action": [
        "apprunner:*", "rds:*", "ec2:*", "secretsmanager:*",
        "iam:CreateRole", "iam:DeleteRole", "iam:GetRole", "iam:PassRole",
        "iam:AttachRolePolicy", "iam:DetachRolePolicy",
        "iam:PutRolePolicy", "iam:DeleteRolePolicy",
        "iam:ListRolePolicies", "iam:ListAttachedRolePolicies",
        "iam:CreateServiceLinkedRole" ],
      "Resource": "*" }
  ]
}
```

> This is broad for first setup convenience. Tighten `*` to specific ARNs once
> the stack exists if you want. For CI, the same user is fine.

Generate an **access key** for this user and keep the key + secret.

### 3. Configure the CLI locally

```bash
aws configure           # paste the access key, secret, region (e.g. eu-central-1)
aws sts get-caller-identity   # verify
```

### 4. Rotate the OpenAI key

Generate a fresh key at platform.openai.com (the previously-pasted one is
compromised). Export it for Terraform:

```bash
export TF_VAR_openai_api_key="sk-proj-...NEW..."
```

### 5. (For CI/CD) add GitHub repo secrets & variables

Repo → Settings → Secrets and variables → Actions:

- **Secrets:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- **Variables:** `AWS_REGION` (e.g. `eu-central-1`), `PROJECT` (`languagecoach`)

---

## Part B — first deploy (once)

### Option 1 — GitHub Actions (no local tooling; recommended)

Runs the entire ordered bootstrap on GitHub's runners. State is kept in an S3
bucket the workflow creates (`<project>-tfstate-<account-id>`).

1. Add repo secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
   `OPENAI_API_KEY`. Add variables `AWS_REGION`, `PROJECT`.
2. Trigger it: Actions tab → **Bootstrap AWS (first deploy)** → Run workflow,
   or `gh workflow run bootstrap.yml`.
3. The run summary prints the live **Web** and **API** URLs.

### Option 2 — locally

Requires local tooling from Part A + Terraform state config. Uses local state
unless you add `-backend-config` for S3.

```bash
cd infra
cp terraform/terraform.tfvars.example terraform/terraform.tfvars   # optional edits
export TF_VAR_openai_api_key="sk-proj-...NEW..."
./bootstrap.sh
```

`bootstrap.sh` runs the ordered phases (ECR → push API image → create RDS +
secrets + API service → push web image with the API URL baked in → create web
service → lock CORS to the web origin). It prints the final **Web** and **API**
URLs. Open the Web URL — the app is live.

First run takes ~10–15 min (RDS provisioning dominates).

---

## Part C — updates (steady state)

**Option 1 — push to deploy (recommended):** commit and push to `main`. The
GitHub Action rebuilds only the changed service (API and/or web), pushes to ECR,
and triggers an App Runner rolling deploy.

**Option 2 — manual:**

```bash
infra/deploy.sh both   # or: api | web
```

**Infra changes** (DB size, add an env var, etc.): edit `infra/terraform/*.tf`
and run `terraform apply` from `infra/terraform`.

---

## Teardown

```bash
cd infra/terraform
terraform apply -var db_deletion_protection=false   # allow DB delete
terraform destroy -var db_skip_final_snapshot=true  # skip snapshot for throwaway
```

RDS takes a final snapshot unless `db_skip_final_snapshot=true`.

---

## Notes / follow-ups

- **Cost:** not free-tier. Rough idle (no NAT): RDS db.t4g.micro (~$15/mo) +
  2 App Runner services (~$5–10/mo each idle) ≈ **$25–35/mo**.
- **Security tradeoff:** to save the ~$32/mo NAT gateway, RDS is **publicly
  accessible** (protected by a strong generated password). Port 3306 is open
  network-wide because App Runner egress IPs aren't fixed. To fully isolate the
  DB later, reintroduce private subnets + NAT + a VPC connector and set
  `publicly_accessible = false`.
- **DB TLS in transit** is a recommended follow-up (needs aiomysql `connect_args`
  in `mysql_store.py`) — especially important given the public endpoint.
- **Custom domain + HTTPS cert** (ACM) is out of scope for v1; App Runner's
  default `*.awsapprunner.com` URLs are used.
