variable "aws_region" {
  description = "AWS region used by the provider"
  type        = string
  default     = "us-east-1"
}

variable "github_repository" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
}

variable "role_name" {
  description = "IAM role name for GitHub Actions deploys"
  type        = string
  default     = "github-actions-twin-deploy"
}
