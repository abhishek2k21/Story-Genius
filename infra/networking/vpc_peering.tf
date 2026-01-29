# Cross-Region VPC Peering
# Allows communication between us-east-1 and us-west-2

# VPC Peering Connection (initiated from us-east-1)
resource "aws_vpc_peering_connection" "east_to_west" {
  provider = aws.us-east-1
  
  vpc_id      = module.vpc_east.vpc_id  # us-east-1 VPC
  peer_vpc_id = module.vpc_west.vpc_id  # us-west-2 VPC
  peer_region = "us-west-2"
  
  auto_accept = false
  
  tags = {
    Name        = "east-west-peering"
    Description = "VPC peering between us-east-1 and us-west-2"
  }
}

# Accept peering connection in us-west-2
resource "aws_vpc_peering_connection_accepter" "west" {
  provider                  = aws.us-west-2
  vpc_peering_connection_id = aws_vpc_peering_connection.east_to_west.id
  auto_accept               = true
  
  tags = {
    Name   = "east-west-peering-accepter"
    Region = "us-west-2"
  }
}

# Route from us-east-1 to us-west-2
resource "aws_route" "east_to_west_private" {
  provider = aws.us-east-1
  
  count = length(module.vpc_east.private_route_table_ids)
  
  route_table_id            = module.vpc_east.private_route_table_ids[count.index]
  destination_cidr_block    = "10.1.0.0/16"  # us-west-2 CIDR
  vpc_peering_connection_id = aws_vpc_peering_connection.east_to_west.id
}

# Route from us-west-2 to us-east-1
resource "aws_route" "west_to_east_private" {
  provider = aws.us-west-2
  
  count = length(module.vpc_west.private_route_table_ids)
  
  route_table_id            = module.vpc_west.private_route_table_ids[count.index]
  destination_cidr_block    = "10.0.0.0/16"  # us-east-1 CIDR
  vpc_peering_connection_id = aws_vpc_peering_connection.east_to_west.id
}

# Security group rules to allow cross-region traffic
resource "aws_security_group_rule" "allow_west_to_east" {
  provider = aws.us-east-1
  
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "-1"
  cidr_blocks       = ["10.1.0.0/16"]  # Allow from us-west-2
  security_group_id = module.eks_east.cluster_security_group_id
  description       = "Allow traffic from us-west-2"
}

resource "aws_security_group_rule" "allow_east_to_west" {
  provider = aws.us-west-2
  
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "-1"
  cidr_blocks       = ["10.0.0.0/16"]  # Allow from us-east-1
  security_group_id = module.eks_west.cluster_security_group_id
  description       = "Allow traffic from us-east-1"
}

# Test connectivity (optional - for validation)
output "peering_connection_id" {
  description = "VPC peering connection ID"
  value       = aws_vpc_peering_connection.east_to_west.id
}

output "peering_status" {
  description = "VPC peering connection status"
  value       = aws_vpc_peering_connection.east_to_west.accept_status
}
