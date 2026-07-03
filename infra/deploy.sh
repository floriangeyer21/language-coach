#!/usr/bin/env bash
# Steady-state redeploy: rebuild & push images, trigger App Runner rolling deploy.
# Infra (RDS, networking, secrets) is NOT touched here — use terraform for that.
#
# Usage:
#   infra/deploy.sh both   # default: api + web
#   infra/deploy.sh api
#   infra/deploy.sh web
set -euo pipefail

TARGET="${1:-both}"
cd "$(dirname "$0")/terraform"
REPO_ROOT="$(cd ../.. && pwd)"

REGION="$(terraform output -raw region)"
API_REPO="$(terraform output -raw ecr_api_repo_url)"
WEB_REPO="$(terraform output -raw ecr_web_repo_url)"
API_URL="$(terraform output -raw api_url)"
API_ARN="$(terraform output -raw api_service_arn)"
WEB_ARN="$(terraform output -raw web_service_arn)"
REGISTRY="${API_REPO%/*}"

aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

if [[ "$TARGET" == "api" || "$TARGET" == "both" ]]; then
  echo "==> API image"
  docker build --platform linux/amd64 -t "$API_REPO:latest" "$REPO_ROOT/app/Server"
  docker push "$API_REPO:latest"
  aws apprunner start-deployment --region "$REGION" --service-arn "$API_ARN"
fi

if [[ "$TARGET" == "web" || "$TARGET" == "both" ]]; then
  echo "==> WEB image"
  docker build --platform linux/amd64 \
    --build-arg "NEXT_PUBLIC_API_BASE_URL=$API_URL" \
    -t "$WEB_REPO:latest" "$REPO_ROOT/app/Web"
  docker push "$WEB_REPO:latest"
  aws apprunner start-deployment --region "$REGION" --service-arn "$WEB_ARN"
fi

echo "Deploy triggered."
