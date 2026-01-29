# Multi-AZ EKS Node Group Configuration

# Update to existing eks_cluster.tf to add multi-AZ support

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# Update VPC module to use all 3 AZs
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = var.availability_zones
  private_subnets = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]

  enable_nat_gateway     = true
  one_nat_gateway_per_az = true  # HA: One NAT Gateway per AZ
  enable_dns_hostnames   = true
  enable_dns_support     = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = merge(var.tags, {
    "HighAvailability" = "true"
  })
}

# Multi-AZ Node Groups
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets  # Spans all 3 AZs

  # Control plane logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Cluster access
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # Multi-AZ Node Groups
  eks_managed_node_groups = {
    # General purpose nodes - distributed across all AZs
    general = {
      name = "${var.cluster_name}-general"
      
      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"
      
      min_size     = 3   # At least 1 per AZ
      max_size     = 12  # 4 per AZ max
      desired_size = 3
      
      # Ensure distribution across AZs
      subnet_ids = module.vpc.private_subnets
      
      labels = {
        role = "general"
        ha   = "true"
      }
      
      taints = []
      
      tags = merge(var.tags, {
        NodeGroup = "general"
        HA        = "true"
      })
    }
    
    # Compute optimized nodes - for video processing
    compute = {
      name = "${var.cluster_name}-compute"
      
      instance_types = ["c5.xlarge"]
      capacity_type  = "SPOT"  # Cost optimization
      
      min_size     = 0
      max_size     = 30  # 10 per AZ max
      desired_size = 3
      
      # Ensure distribution across AZs
      subnet_ids = module.vpc.private_subnets
      
      labels = {
        role     = "compute"
        workload = "video-processing"
        ha       = "true"
      }
      
      taints = [{
        key    = "workload"
        value  = "compute-intensive"
        effect = "NO_SCHEDULE"
      }]
      
      tags = merge(var.tags, {
        NodeGroup = "compute"
        HA        = "true"
      })
    }
  }

  # AWS Auth
  manage_aws_auth_configmap = true

  tags = merge(var.tags, {
    HighAvailability = "true"
  })
}

# Outputs
output "node_groups" {
  description = "EKS node groups"
  value = {
    general = module.eks.eks_managed_node_groups["general"]
    compute = module.eks.eks_managed_node_groups["compute"]
  }
}

output "availability_zones" {
  description = "Availability zones used"
  value       = var.availability_zones
}
