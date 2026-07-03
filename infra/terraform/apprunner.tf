# ---- API service ----
# Uses App Runner's default public egress to reach both OpenAI and the public
# RDS endpoint (no VPC connector / NAT — see network.tf tradeoff note).
resource "aws_apprunner_service" "api" {
  service_name = "${var.project}-api"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access.arn
    }
    auto_deployments_enabled = true
    image_repository {
      image_identifier      = "${aws_ecr_repository.api.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"
      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          STORAGE_BACKEND      = "mysql"
          OPENAI_CHAT_MODEL    = var.openai_chat_model
          OPENAI_MEMORY_MODEL  = var.openai_memory_model
          JWT_ALGORITHM        = var.jwt_algorithm
          ACCESS_TOKEN_TTL_MIN = tostring(var.access_token_ttl_min)
          CORS_ORIGINS         = var.cors_origins
        }
        runtime_environment_secrets = {
          OPENAI_API_KEY = aws_secretsmanager_secret.openai_api_key.arn
          JWT_SECRET     = aws_secretsmanager_secret.jwt_secret.arn
          DATABASE_URL   = aws_secretsmanager_secret.database_url.arn
        }
      }
    }
  }

  instance_configuration {
    cpu               = var.apprunner_cpu
    memory            = var.apprunner_memory
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  health_check_configuration {
    protocol = "TCP"
  }

  depends_on = [aws_db_instance.mysql]
}

# ---- Web service ----
# The image is built with NEXT_PUBLIC_API_BASE_URL = api service URL, so this
# service is created only after the API URL is known and the web image pushed.
resource "aws_apprunner_service" "web" {
  service_name = "${var.project}-web"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access.arn
    }
    auto_deployments_enabled = true
    image_repository {
      image_identifier      = "${aws_ecr_repository.web.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"
      image_configuration {
        port = "3000"
      }
    }
  }

  instance_configuration {
    cpu    = var.apprunner_cpu
    memory = var.apprunner_memory
  }

  health_check_configuration {
    protocol = "TCP"
  }
}
