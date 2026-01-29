# Aurora Global Database for Cross-Region Replication
# Primary: us-east-1, Secondary: us-west-2

# Global Database Cluster
resource "aws_rds_global_cluster" "global" {
  global_cluster_identifier = "yt-video-creator-global"
  engine                    = "aurora-postgresql"
  engine_version            = "15.3"
  database_name             = "yt_video_creator"
  
  # Enable global write forwarding (writes can happen on secondary)
  enable_global_write_forwarding = true
  
  # Storage encryption
  storage_encrypted = true
}

# Primary Aurora Cluster (us-east-1)
resource "aws_rds_cluster" "primary" {
  provider = aws.us-east-1
  
  cluster_identifier        = "yt-video-creator-primary"
  engine                    = "aurora-postgresql"
  engine_version            = "15.3"
  database_name             = "yt_video_creator"
  master_username           = var.db_username
  master_password           = var.db_password
  
  # Link to global cluster
  global_cluster_identifier = aws_rds_global_cluster.global.id
  
  # Multi-AZ deployment
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  
  # Backup configuration
  backup_retention_period      = 7
  preferred_backup_window      = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  
  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  # Performance
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.primary.name
  
  # Security
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds_east.arn
  
  # Skip final snapshot for testing (set to false in production)
  skip_final_snapshot = false
  final_snapshot_identifier = "yt-video-creator-primary-final-snapshot"
  
  tags = {
    Name   = "yt-video-creator-primary"
    Region = "primary"
    Role   = "read-write"
  }
}

# Primary cluster instances
resource "aws_rds_cluster_instance" "primary" {
  provider = aws.us-east-1
  
  count = 3  # 3 instances across 3 AZs
  
  identifier         = "yt-video-creator-primary-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.primary.id
  instance_class     = "db.r6g.large"
  engine             = aws_rds_cluster.primary.engine
  engine_version     = aws_rds_cluster.primary.engine_version
  
  # Performance Insights
  performance_insights_enabled = true
  
  tags = {
    Name   = "primary-instance-${count.index + 1}"
    Region = "us-east-1"
  }
}

# Secondary Aurora Cluster (us-west-2) - Read Replica
resource "aws_rds_cluster" "secondary" {
  provider = aws.us-west-2
  
  cluster_identifier        = "yt-video-creator-secondary"
  engine                    = "aurora-postgresql"
  engine_version            = "15.3"
  
  # Link to global cluster (becomes read replica)
  global_cluster_identifier = aws_rds_global_cluster.global.id
  
  # Multi-AZ deployment
  availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
  
  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  # Performance
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.secondary.name
  
  # Security
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds_west.arn
  
  # Skip final snapshot for testing
  skip_final_snapshot = false
  final_snapshot_identifier = "yt-video-creator-secondary-final-snapshot"
  
  tags = {
    Name   = "yt-video-creator-secondary"
    Region = "secondary"
    Role   = "read-only"
  }
  
  depends_on = [aws_rds_cluster.primary]
}

# Secondary cluster instances
resource "aws_rds_cluster_instance" "secondary" {
  provider = aws.us-west-2
  
  count = 2  # 2 instances (smaller than primary)
  
  identifier         = "yt-video-creator-secondary-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.secondary.id
  instance_class     = "db.r6g.large"
  engine             = aws_rds_cluster.secondary.engine
  engine_version     = aws_rds_cluster.secondary.engine_version
  
  # Performance Insights
  performance_insights_enabled = true
  
  tags = {
    Name   = "secondary-instance-${count.index + 1}"
    Region = "us-west-2"
  }
}

# Parameter groups
resource "aws_rds_cluster_parameter_group" "primary" {
  provider = aws.us-east-1
  
  name   = "yt-video-creator-primary-params"
  family = "aurora-postgresql15"
  
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }
  
  parameter {
    name  = "log_statement"
    value = "all"
  }
}

resource "aws_rds_cluster_parameter_group" "secondary" {
  provider = aws.us-west-2
  
  name   = "yt-video-creator-secondary-params"
  family = "aurora-postgresql15"
  
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }
}

# KMS keys for encryption
resource "aws_kms_key" "rds_east" {
  provider = aws.us-east-1
  
  description             = "KMS key for RDS encryption (us-east-1)"
  deletion_window_in_days = 10
  
  tags = {
    Name   = "rds-encryption-key-east"
    Region = "us-east-1"
  }
}

resource "aws_kms_key" "rds_west" {
  provider = aws.us-west-2
  
  description             = "KMS key for RDS encryption (us-west-2)"
  deletion_window_in_days = 10
  
  tags = {
    Name   = "rds-encryption-key-west"
    Region = "us-west-2"
  }
}

# Outputs
output "primary_cluster_endpoint" {
  description = "Primary cluster endpoint (us-east-1)"
  value       = aws_rds_cluster.primary.endpoint
}

output "primary_cluster_reader_endpoint" {
  description = "Primary cluster reader endpoint (us-east-1)"
  value       = aws_rds_cluster.primary.reader_endpoint
}

output "secondary_cluster_endpoint" {
  description = "Secondary cluster endpoint (us-west-2)"
  value       = aws_rds_cluster.secondary.endpoint
}

output "global_cluster_id" {
  description = "Global cluster identifier"
  value       = aws_rds_global_cluster.global.id
}
