data "aws_caller_identity" "current" {}

# ---- App Runner access role: pull images from ECR ----
data "aws_iam_policy_document" "apprunner_build_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apprunner_access" {
  name               = "${var.project}-apprunner-access"
  assume_role_policy = data.aws_iam_policy_document.apprunner_build_assume.json
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr" {
  role       = aws_iam_role.apprunner_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# ---- App Runner instance role: read secrets at runtime ----
data "aws_iam_policy_document" "apprunner_tasks_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apprunner_instance" {
  name               = "${var.project}-apprunner-instance"
  assume_role_policy = data.aws_iam_policy_document.apprunner_tasks_assume.json
}

data "aws_iam_policy_document" "read_secrets" {
  statement {
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_secretsmanager_secret.openai_api_key.arn,
      aws_secretsmanager_secret.jwt_secret.arn,
      aws_secretsmanager_secret.database_url.arn,
    ]
  }
}

resource "aws_iam_role_policy" "instance_read_secrets" {
  name   = "${var.project}-read-secrets"
  role   = aws_iam_role.apprunner_instance.id
  policy = data.aws_iam_policy_document.read_secrets.json
}

# App Runner validates the access/instance roles at service-create time, which
# can beat IAM's global propagation and fail with "Invalid Access Role". Wait a
# bit after the roles/policies exist before creating the services.
resource "time_sleep" "wait_iam" {
  depends_on = [
    aws_iam_role.apprunner_access,
    aws_iam_role_policy_attachment.apprunner_ecr,
    aws_iam_role.apprunner_instance,
    aws_iam_role_policy.instance_read_secrets,
  ]
  create_duration = "45s"
}
