variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "eu-central-1"
}

variable "project" {
  description = "Name prefix for all resources."
  type        = string
  default     = "languagecoach"
}

# ---- App config (non-secret) ----
variable "openai_chat_model" {
  type    = string
  default = "gpt-4o"
}

variable "openai_memory_model" {
  type    = string
  default = "gpt-4o-mini"
}

variable "jwt_algorithm" {
  type    = string
  default = "HS256"
}

variable "access_token_ttl_min" {
  type    = number
  default = 60
}

# Set to the web service URL (https://...) after it exists, then re-apply so the
# API restricts CORS to the real origin. Defaults to "*" for the bootstrap phase.
variable "cors_origins" {
  type    = string
  default = "*"
}

# ---- Secrets (supplied at apply time; never committed) ----
variable "openai_api_key" {
  description = "Rotated OpenAI API key. Pass via TF_VAR_openai_api_key or -var."
  type        = string
  sensitive   = true
}

# ---- Images ----
variable "image_tag" {
  description = "ECR image tag the App Runner services deploy."
  type        = string
  default     = "latest"
}

# ---- Database ----
variable "db_name" {
  type    = string
  default = "languagecoach"
}

variable "db_username" {
  type    = string
  default = "lcadmin"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

# RDS is public (no NAT); App Runner egress IPs are not fixed, so this defaults
# open on 3306 and access is gated by credentials. Narrow it if you pin egress.
variable "db_allowed_cidr" {
  type    = string
  default = "0.0.0.0/0"
}

variable "db_allocated_storage" {
  type    = number
  default = 20
}

variable "db_deletion_protection" {
  type    = bool
  default = true
}

variable "db_skip_final_snapshot" {
  description = "Skip the final snapshot on destroy (set true only for throwaway envs)."
  type        = bool
  default     = false
}

# ---- App Runner sizing ----
variable "apprunner_cpu" {
  type    = string
  default = "1024" # 1 vCPU
}

variable "apprunner_memory" {
  type    = string
  default = "2048" # 2 GB
}
