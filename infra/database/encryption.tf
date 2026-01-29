# RDS Encryption Configuration
# Enables encryption at rest for PostgreSQL database

# KMS key for RDS encryption
resource "aws_kms_key" "rds" {
  description             = "RDS encryption key for YT Video Creator"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  tags = {
    Name        = "yt-video-creator-rds-key"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "rds" {
  name          = "alias/yt-video-creator-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# Update RDS instance to enable encryption
resource "aws_db_instance" "postgres_encrypted" {
  identifier = "yt-video-creator-postgres"
  
  # Engine
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.r6g.large"
  
  # Storage
  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"
  storage_encrypted     = true  # Enable encryption
  kms_key_id           = aws_kms_key.rds.arn
  
  # Database
  db_name  = "yt_video_creator"
  username = var.db_master_username
  password = var.db_master_password
  
  # Network
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  
  # Backup
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"
  
  # Encryption
  storage_encrypted = true
  kms_key_id       = aws_kms_key.rds.arn
  
  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = 60
  monitoring_role_arn            = aws_iam_role.rds_monitoring.arn
  
  # Protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "yt-video-creator-final-snapshot"
  
  tags = {
    Name        = "yt-video-creator-postgres"
    Environment = var.environment
    Encrypted   = "true"
  }
}

# Aurora Global Database with Encryption
resource "aws_rds_global_cluster" "postgres_global_encrypted" {
  global_cluster_identifier = "yt-video-creator-global"
  engine                    = "aurora-postgresql"
  engine_version            = "15.3"
  database_name             = "yt_video_creator"
  storage_encrypted         = true
}

# Primary Aurora cluster (us-east-1) with encryption
resource "aws_rds_cluster" "postgres_primary_encrypted" {
  cluster_identifier        = "yt-video-creator-primary"
  engine                    = "aurora-postgresql"
  engine_version            = "15.3"
  database_name             = "yt_video_creator"
  master_username           = var.db_master_username
  master_password           = var.db_master_password
  
  global_cluster_identifier = aws_rds_global_cluster.postgres_global_encrypted.id
  
  # Encryption
  storage_encrypted = true
  kms_key_id       = aws_kms_key.rds.arn
  
  # Network
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  # Backup
  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  
  # Protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "yt-video-creator-primary-final-snapshot"
  
  tags = {
    Name        = "yt-video-creator-primary"
    Region      = "us-east-1"
    Encrypted   = "true"
  }
}

# Secondary Aurora cluster (us-west-2) with encryption
resource "aws_rds_cluster" "postgres_secondary_encrypted" {
  provider = aws.us_west_2
  
  cluster_identifier        = "yt-video-creator-secondary"
  engine                    = "aurora-postgresql"
  engine_version            = "15.3"
  
  global_cluster_identifier = aws_rds_global_cluster.postgres_global_encrypted.id
  
  # Encryption (uses same global cluster encryption)
  storage_encrypted = true
  kms_key_id       = aws_kms_key.rds_west.arn
  
  # Network
  db_subnet_group_name   = aws_db_subnet_group.postgres_west.name
  vpc_security_group_ids = [aws_security_group.rds_west.id]
  
  # Protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "yt-video-creator-secondary-final-snapshot"
  
  tags = {
    Name        = "yt-video-creator-secondary"
    Region      = "us-west-2"
    Encrypted   = "true"
  }
}

# KMS key for us-west-2
resource "aws_kms_key" "rds_west" {
  provider = aws.us_west_2
  
  description             = "RDS encryption key for YT Video Creator (us-west-2)"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  tags = {
    Name        = "yt-video-creator-rds-key-west"
    Environment = var.environment
    Region      = "us-west-2"
  }
}

# Outputs
output "rds_kms_key_id" {
  description = "KMS key ID for RDS encryption"
  value       = aws_kms_key.rds.key_id
}

output "rds_kms_key_arn" {
  description = "KMS key ARN for RDS encryption"
  value       = aws_kms_key.rds.arn
}

output "database_encrypted" {
  description = "Database encryption status"
  value       = aws_db_instance.postgres_encrypted.storage_encrypted
}
