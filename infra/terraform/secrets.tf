resource "random_password" "jwt" {
  length  = 48
  special = false
}

locals {
  # aiomysql DSN. Traffic to RDS stays inside the VPC (private subnets), so TLS
  # is deferred to a follow-up (see spec). Password is generated URL-safe.
  database_url = "mysql+aiomysql://${var.db_username}:${random_password.db.result}@${aws_db_instance.mysql.address}:3306/${var.db_name}"
}

resource "aws_secretsmanager_secret" "openai_api_key" {
  name = "${var.project}/openai_api_key"
}
resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name = "${var.project}/jwt_secret"
}
resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt.result
}

resource "aws_secretsmanager_secret" "database_url" {
  name = "${var.project}/database_url"
}
resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = local.database_url
}
