#!/usr/bin/env bash
# First-time AWS deploy for LanguageCoach. Handles the build-order dependency:
# the web image bakes in the API URL, which only exists after the API service.
#
# Prereqs: aws CLI (configured), terraform, docker (or colima), and
# TF_VAR_openai_api_key exported (rotated key).
#
# Usage:  cd infra && ./bootstrap.sh
set -euo pipefail

cd "$(dirname "$0")/terraform"
REPO_ROOT="$(cd ../.. && pwd)"

: "${TF_VAR_openai_api_key:?export TF_VAR_openai_api_key with your rotated OpenAI key}"

REGION="$(terraform console <<<'var.region' 2>/dev/null | tr -d '"' || echo eu-central-1)"

echo "==> terraform init"
terraform init

echo "==> Phase 1: create ECR repos"
terraform apply -auto-approve \
  -target=aws_ecr_repository.api \
  -target=aws_ecr_repository.web

API_REPO="$(terraform output -raw ecr_api_repo_url)"
WEB_REPO="$(terraform output -raw ecr_web_repo_url)"
REGISTRY="${API_REPO%/*}"

echo "==> Docker login to ECR ($REGISTRY)"
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

echo "==> Phase 2: build & push API image"
docker build --platform linux/amd64 -t "$API_REPO:latest" "$REPO_ROOT/app/Server"
docker push "$API_REPO:latest"

echo "==> Phase 3: create RDS, secrets, IAM, VPC connector, API service"
terraform apply -auto-approve \
  -target=aws_apprunner_service.api

API_URL="$(terraform output -raw api_url)"
echo "    API is at: $API_URL"

echo "==> Phase 4: build & push WEB image (baking in API URL)"
docker build --platform linux/amd64 \
  --build-arg "NEXT_PUBLIC_API_BASE_URL=$API_URL" \
  -t "$WEB_REPO:latest" "$REPO_ROOT/app/Web"
docker push "$WEB_REPO:latest"

echo "==> Phase 5: create web service + full apply"
terraform apply -auto-approve

WEB_URL="$(terraform output -raw web_url)"

echo "==> Phase 6: lock CORS to the web origin and redeploy API"
terraform apply -auto-approve -var "cors_origins=$WEB_URL"

echo
echo "Done."
echo "  Web: $WEB_URL"
echo "  API: $API_URL"
