output "github_actions_role_arn" {
  description = "The ARN of the GitHub Actions deploy role"
  value       = aws_iam_role.github_actions.arn
}

output "github_oidc_provider_arn" {
  description = "The ARN of the GitHub OIDC provider"
  value       = aws_iam_openid_connect_provider.github.arn
}
