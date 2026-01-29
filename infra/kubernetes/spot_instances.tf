# Spot Instance Node Group Configuration for Cost Optimization

variable "spot_instance_types" {
  description = "Instance types for spot instances"
  type        = list(string)
  default     = ["c5.xlarge", "c5a.xlarge", "c5n.xlarge", "c5d.xlarge"]
}

# Add spot node group to existing EKS module
resource "aws_eks_node_group" "spot_workers" {
  cluster_name    = module.eks.cluster_name
  node_group_name = "${var.cluster_name}-spot-workers"
  node_role_arn   = aws_iam_role.spot_node_role.arn
  subnet_ids      = module.vpc.private_subnets

  scaling_config {
    desired_size = 0    # Start with 0, scale with Cluster Autoscaler
    max_size     = 50   # Max 50 spot instances
    min_size     = 0
  }

  instance_types = var.spot_instance_types
  capacity_type  = "SPOT"

  labels = {
    role              = "worker"
    workload          = "batch-processing"
    cost-optimization = "spot"
    "k8s.io/cluster-autoscaler/enabled"                      = "true"
    "k8s.io/cluster-autoscaler/yt-video-creator-prod"        = "owned"
  }

  taints {
    key    = "workload"
    value  = "batch"
    effect = "NO_SCHEDULE"
  }

  update_config {
    max_unavailable = 1
  }

  # Ensure proper dependencies
  depends_on = [
    aws_iam_role_policy_attachment.spot_node_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.spot_node_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.spot_node_AmazonEC2ContainerRegistryReadOnly,
  ]

  tags = merge(var.tags, {
    Name                                                     = "${var.cluster_name}-spot-workers"
    "k8s.io/cluster-autoscaler/enabled"                      = "true"
    "k8s.io/cluster-autoscaler/yt-video-creator-prod"        = "owned"
  })
}

# IAM role for spot nodes
resource "aws_iam_role" "spot_node_role" {
  name = "${var.cluster_name}-spot-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "spot_node_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.spot_node_role.name
}

resource "aws_iam_role_policy_attachment" "spot_node_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.spot_node_role.name
}

resource "aws_iam_role_policy_attachment" "spot_node_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.spot_node_role.name
}

output "spot_node_group_name" {
  description = "Name of the spot instance node group"
  value       = aws_eks_node_group.spot_workers.node_group_name
}
