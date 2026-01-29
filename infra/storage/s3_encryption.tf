# S3 Bucket Encryption Configuration
# Enforces encryption at rest for all S3 buckets

# KMS key for S3 encryption
resource "aws_kms_key" "s3" {
  description             = "S3 encryption key for YT Video Creator"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow S3 to use the key"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = {
    Name        = "yt-video-creator-s3-key"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "s3" {
  name          = "alias/yt-video-creator-s3"
  target_key_id = aws_kms_key.s3.key_id
}

# Media bucket with encryption
resource "aws_s3_bucket" "media" {
  bucket = "yt-video-creator-media-${var.environment}"
  
  tags = {
    Name        = "yt-video-creator-media"
    Environment = var.environment
    Encrypted   = "true"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true  # Reduces KMS API costs by 99%
  }
}

# Enforce encryption (deny unencrypted uploads)
resource "aws_s3_bucket_policy" "media_enforce_encryption" {
  bucket = aws_s3_bucket.media.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnencryptedObjectUploads"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.media.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "aws:kms"
          }
        }
      },
      {
        Sid    = "DenyIncorrectKMSKey"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.media.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption-aws-kms-key-id" = aws_kms_key.s3.arn
          }
        }
      }
    ]
  })
}

# Enable versioning (for data protection)
resource "aws_s3_bucket_versioning" "media" {
  bucket = aws_s3_bucket.media.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Public access block (no public access)
resource "aws_s3_bucket_public_access_block" "media" {
  bucket = aws_s3_bucket.media.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Temp bucket with encryption
resource "aws_s3_bucket" "temp" {
  bucket = "yt-video-creator-temp-${var.environment}"
  
  tags = {
    Name        = "yt-video-creator-temp"
    Environment = var.environment
    Encrypted   = "true"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "temp" {
  bucket = aws_s3_bucket.temp.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

# Lifecycle rule for temp bucket (delete after 7 days)
resource "aws_s3_bucket_lifecycle_configuration" "temp" {
  bucket = aws_s3_bucket.temp.id
  
  rule {
    id     = "delete-old-temp-files"
    status = "Enabled"
    
    expiration {
      days = 7
    }
  }
}

# Backup bucket with encryption
resource "aws_s3_bucket" "backup" {
  bucket = "yt-video-creator-backup-${var.environment}"
  
  tags = {
    Name        = "yt-video-creator-backup"
    Environment = var.environment
    Encrypted   = "true"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

# Enable versioning for backup
resource "aws_s3_bucket_versioning" "backup" {
  bucket = aws_s3_bucket.backup.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle rule for backup (transition to Glacier after 30 days)
resource "aws_s3_bucket_lifecycle_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id
  
  rule {
    id     = "transition-to-glacier"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "GLACIER"
    }
    
    transition {
      days          = 90
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

# Outputs
output "s3_kms_key_id" {
  description = "KMS key ID for S3 encryption"
  value       = aws_kms_key.s3.key_id
}

output "media_bucket_name" {
  description = "Media bucket name"
  value       = aws_s3_bucket.media.id
}

output "media_bucket_encrypted" {
  description = "Media bucket encryption status"
  value       = "KMS encrypted with ${aws_kms_key.s3.arn}"
}
