output "region" {
  value = var.region
}

output "ecr_api_repo_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ecr_web_repo_url" {
  value = aws_ecr_repository.web.repository_url
}

output "api_url" {
  description = "Public HTTPS URL of the API service. Use as NEXT_PUBLIC_API_BASE_URL when building the web image."
  value       = "https://${aws_apprunner_service.api.service_url}"
}

output "web_url" {
  description = "Public HTTPS URL of the web app. Set cors_origins to this value and re-apply."
  value       = "https://${aws_apprunner_service.web.service_url}"
}

output "rds_endpoint" {
  value = aws_db_instance.mysql.address
}

output "api_service_arn" {
  value = aws_apprunner_service.api.arn
}

output "web_service_arn" {
  value = aws_apprunner_service.web.arn
}
