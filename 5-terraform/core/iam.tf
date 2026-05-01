# Identity and Access Management (IAM) Policies

# Grant read access to EKS service account for Secrets Manager
resource "aws_secretsmanager_secret_policy" "ecommerce_access" {
  secret_arn = aws_secretsmanager_secret.database_url.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEKSServiceAccountAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/ecommerce-external-secrets-role"
        }
        Action   = "secretsmanager:GetSecretValue"
        Resource = "*"
        Condition = {
          StringEquals = {
            "secretsmanager:VersionStage" = "AWSCURRENT"
          }
        }
      }
    ]
  })
}
