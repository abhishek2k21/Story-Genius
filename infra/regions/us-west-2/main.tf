# Secondary Region (us-west-2) EKS Cluster
# Smaller deployment for failover and global reach

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  alias  = "us-west-2"
  region = "us-west-2"
}

variable "cluster_name_west" {
  description = "EKS cluster name for us-west-2"
  type        = string
  default     = "yt-video-creator-west"
}

# VPC for us-west-2 (different CIDR to avoid conflicts)
module "vpc_west" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  providers = {
    aws = aws.us-west-2
  }

  name = "${var.cluster_name_west}-vpc"
  cidr = "10.1.0.0/16"  # Different from us-east-1 (10.0.0.0/16)

  azs             = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets = ["10.1.11.0/24", "10.1.12.0/24", "10.1.13.0/24"]
  public_subnets  = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]

  enable_nat_gateway     = true
  one_nat_gateway_per_az = true
  enable_dns_hostnames   = true
  enable_dns_support     = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = {
    Region      = "secondary"
    Environment = "production"
    Failover    = "true"
  }
}

# EKS Cluster for us-west-2
module "eks_west" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  providers = {
    aws = aws.us-west-2
  }

  cluster_name    = var.cluster_name_west
  cluster_version = "1.28"

  vpc_id     = module.vpc_west.vpc_id
  subnet_ids = module.vpc_west.private_subnets

  # Control plane logging
  cluster_enabled_log_types = ["api", "audit", "authenticator"]

  # Cluster access
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # Smaller node groups for secondary region
  eks_managed_node_groups = {
    general = {
      name = "${var.cluster_name_west}-general"
      
      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"
      
      min_size     = 2   # Smaller than primary
      max_size     = 8
      desired_size = 2
      
      subnet_ids = module.vpc_west.private_subnets
      
      labels = {
        role   = "general"
        region = "us-west-2"
      }
      
      tags = {
        NodeGroup = "general"
        Region    = "secondary"
      }
    }
    
    # Spot instances for flexible workloads
    spot = {
      name = "${var.cluster_name_west}-spot"
      
      instance_types = ["c5.xlarge", "c5a.xlarge"]
      capacity_type  = "SPOT"
      
      min_size     = 0
      max_size     = 20
      desired_size = 0
      
      subnet_ids = module.vpc_west.private_subnets
      
      labels = {
        role     = "worker"
        region   = "us-west-2"
        workload = "batch"
      }
      
      taints = [{
        key    = "workload"
        value  = "batch"
        effect = "NO_SCHEDULE"
      }]
      
      tags = {
        NodeGroup = "spot"
        Region    = "secondary"
      }
    }
  }

  # AWS Auth
  manage_aws_auth_configmap = true

  tags = {
    Region      = "secondary"
    Environment = "production"
  }
}

# Outputs
output "cluster_name_west" {
  description = "EKS cluster name (us-west-2)"
  value       = module.eks_west.cluster_name
}

output "cluster_endpoint_west" {
  description = "EKS cluster endpoint (us-west-2)"
  value       = module.eks_west.cluster_endpoint
}

output "vpc_id_west" {
  description = "VPC ID (us-west-2)"
  value       = module.vpc_west.vpc_id
}
