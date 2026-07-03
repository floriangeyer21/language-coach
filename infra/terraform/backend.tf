# Remote state in S3 so the deploy is reproducible and tear-down-able across
# runs (CI or local). Bucket/key/region are supplied at `terraform init` time via
# -backend-config (see the bootstrap workflow / runbook).
terraform {
  backend "s3" {}
}
