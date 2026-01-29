# AWS IAM Roles for Service Accounts (IRSA)
# Enables pods to assume IAM roles without storing credentials

# OIDC Provider for EKS (required for IRSA)
data "tls_certificate" "eks" {
  url = module.eks.cluster_oidc_issuer_url
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = module.eks.cluster_oidc_issuer_url
  
  tags = {
    Name = "yt-video-creator-eks-oidc"
  }
}

# IAM Role for API Service
resource "aws_iam_role" "api_pod_role" {
  name = "yt-video-creator-api-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks.arn
      }
      Condition = {
        StringEquals = {
          "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:sub" = "system:serviceaccount:production:api-service-account"
          "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
  
  tags = {
    Name = "api-pod-role"
  }
}

# S3 Access Policy for API (read/write media files)
resource "aws_iam_role_policy" "api_s3_access" {
  name = "s3-media-access"
  role = aws_iam_role.api_pod_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "arn:aws:s3:::yt-video-creator-media/*"
      },
      {
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = "arn:aws:s3:::yt-video-creator-media"
      }
    ]
  })
}

# SES Access for API (send emails)
resource "aws_iam_role_policy" "api_ses_access" {
  name = "ses-send-access"
  role = aws_iam_role.api_pod_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ]
      Resource = "*"
      Condition = {
        StringEquals = {
          "ses:FromAddress" = "noreply@ytvideocreator.com"
        }
      }
    }]
  })
}

# IAM Role for Worker Service
resource "aws_iam_role" "worker_pod_role" {
  name = "yt-video-creator-worker-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks.arn
      }
      Condition = {
        StringEquals = {
          "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:sub" = "system:serviceaccount:production:worker-service-account"
          "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
  
  tags = {
    Name = "worker-pod-role"
  }
}

# S3 Access for Workers (full access for video processing)
resource "aws_iam_role_policy" "worker_s3_access" {
  name = "s3-full-access"
  role = aws_iam_role.worker_pod_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::yt-video-creator-media/*",
          "arn:aws:s3:::yt-video-creator-temp/*"
        ]
      },
      {
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::yt-video-creator-media",
          "arn:aws:s3:::yt-video-creator-temp"
        ]
      }
    ]
  })
}

# CloudWatch Logs Access for Workers
resource "aws_iam_role_policy" "worker_cloudwatch_access" {
  name = "cloudwatch-logs-access"
  role = aws_iam_role.worker_pod_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "arn:aws:logs:*:*:log-group:/aws/eks/yt-video-creator/*"
    }]
  })
}

# Outputs
output "api_pod_role_arn" {
  description = "ARN of IAM role for API pods"
  value       = aws_iam_role.api_pod_role.arn
}

output "worker_pod_role_arn" {
  description = "ARN of IAM role for worker pods"
  value       = aws_iam_role.worker_pod_role.arn
}
