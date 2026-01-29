# AWS Security Groups (Terraform)
# Implements least-privilege network access

# Security group for EKS nodes
resource "aws_security_group" "eks_nodes" {
  name        = "yt-video-creator-eks-nodes"
  description = "Security group for EKS worker nodes"
  vpc_id      = module.vpc.vpc_id
  
  # Allow nodes to communicate with each other
  ingress {
    description = "Allow node to node communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "-1"
    self        = true
  }
  
  # Allow control plane to communicate with nodes
  ingress {
    description     = "Allow control plane to nodes"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }
  
  # Allow kubelet API
  ingress {
    description = "Allow kubelet API"
    from_port   = 10250
    to_port     = 10250
    protocol    = "tcp"
    self        = true
  }
  
  # Egress to internet (for image pulls, AWS APIs)
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "yt-video-creator-eks-nodes"
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
  }
}

# Security group for RDS (PostgreSQL)
resource "aws_security_group" "rds" {
  name        = "yt-video-creator-rds"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = module.vpc.vpc_id
  
  # Allow PostgreSQL from EKS nodes only
  ingress {
    description     = "PostgreSQL from EKS nodes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }
  
  # Allow from other RDS instances (replication)
  ingress {
    description = "PostgreSQL replication"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    self        = true
  }
  
  # No egress needed for RDS
  egress {
    description = "Allow outbound for updates"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "yt-video-creator-rds"
  }
}

# Security group for ElastiCache (Redis)
resource "aws_security_group" "elasticache" {
  name        = "yt-video-creator-elasticache"
  description = "Security group for ElastiCache Redis"
  vpc_id      = module.vpc.vpc_id
  
  # Allow Redis from EKS nodes only
  ingress {
    description     = "Redis from EKS nodes"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }
  
  # Allow from other Redis nodes (Sentinel)
  ingress {
    description = "Redis replication"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    self        = true
  }
  
  tags = {
    Name = "yt-video-creator-elasticache"
  }
}

# Security group for Load Balancer
resource "aws_security_group" "alb" {
  name        = "yt-video-creator-alb"
  description = "Security group for Application Load Balancer"
  vpc_id      = module.vpc.vpc_id
  
  # Allow HTTP from internet
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Allow HTTPS from internet
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Egress to EKS nodes
  egress {
    description     = "To EKS nodes"
    from_port       = 0
    to_port         = 65535
    protocol        = "-1"
    security_groups = [aws_security_group.eks_nodes.id]
  }
  
  tags = {
    Name = "yt-video-creator-alb"
  }
}

# Update EKS nodes to allow traffic from ALB
resource "aws_security_group_rule" "eks_from_alb" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "-1"
  source_security_group_id = aws_security_group.alb.id
  security_group_id        = aws_security_group.eks_nodes.id
  description              = "Allow traffic from ALB"
}

# Security group for Bastion (SSH access)
resource "aws_security_group" "bastion" {
  name        = "yt-video-creator-bastion"
  description = "Security group for bastion host"
  vpc_id      = module.vpc.vpc_id
  
  # Allow SSH from specific IPs only
  ingress {
    description = "SSH from office/VPN"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.bastion_allowed_ips  # Define in variables
  }
  
  # Egress to EKS nodes
  egress {
    description     = "SSH to EKS nodes"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }
  
  # Egress to internet (for package updates)
  egress {
    description = "Internet access"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "yt-video-creator-bastion"
  }
}

# Allow SSH from bastion to EKS nodes
resource "aws_security_group_rule" "eks_from_bastion" {
  type                     = "ingress"
  from_port                = 22
  to_port                  = 22
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.bastion.id
  security_group_id        = aws_security_group.eks_nodes.id
  description              = "SSH from bastion"
}

# Outputs
output "eks_nodes_sg_id" {
  value = aws_security_group.eks_nodes.id
}

output "rds_sg_id" {
  value = aws_security_group.rds.id
}

output "elasticache_sg_id" {
  value = aws_security_group.elasticache.id
}

output "alb_sg_id" {
  value = aws_security_group.alb.id
}
