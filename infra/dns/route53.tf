# Route53 Global Load Balancing with Latency-Based Routing
# Routes users to nearest region for optimal performance

# Hosted Zone
resource "aws_route53_zone" "main" {
  name = "ytvideocreator.com"
  
  tags = {
    Name        = "ytvideocreator-hosted-zone"
    Environment = "production"
  }
}

# Health Check for us-east-1
resource "aws_route53_health_check" "us_east_1" {
  fqdn              = aws_lb.us_east_1.dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
  
  measure_latency = true
  
  tags = {
    Name   = "us-east-1-health-check"
    Region = "us-east-1"
  }
}

# Health Check for us-west-2
resource "aws_route53_health_check" "us_west_2" {
  fqdn              = aws_lb.us_west_2.dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
  
  measure_latency = true
  
  tags = {
    Name   = "us-west-2-health-check"
    Region = "us-west-2"
  }
}

# CloudWatch Alarm for us-east-1 health
resource "aws_cloudwatch_metric_alarm" "us_east_1_health" {
  provider = aws.us-east-1
  
  alarm_name          = "route53-health-us-east-1"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "This metric monitors us-east-1 health check"
  
  dimensions = {
    HealthCheckId = aws_route53_health_check.us_east_1.id
  }
}

# CloudWatch Alarm for us-west-2 health
resource "aws_cloudwatch_metric_alarm" "us_west_2_health" {
  provider = aws.us-west-2
  
  alarm_name          = "route53-health-us-west-2"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "This metric monitors us-west-2 health check"
  
  dimensions = {
    HealthCheckId = aws_route53_health_check.us_west_2.id
  }
}

# API Endpoint - us-east-1 (Latency-based routing)
resource "aws_route53_record" "api_primary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.ytvideocreator.com"
  type    = "A"
  
  set_identifier = "us-east-1"
  
  # Latency-based routing
  latency_routing_policy {
    region = "us-east-1"
  }
  
  # Alias to Network Load Balancer
  alias {
    name                   = aws_lb.us_east_1.dns_name
    zone_id                = aws_lb.us_east_1.zone_id
    evaluate_target_health = true
  }
  
  health_check_id = aws_route53_health_check.us_east_1.id
}

# API Endpoint - us-west-2 (Latency-based routing)
resource "aws_route53_record" "api_secondary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.ytvideocreator.com"
  type    = "A"
  
  set_identifier = "us-west-2"
  
  # Latency-based routing
  latency_routing_policy {
    region = "us-west-2"
  }
  
  # Alias to Network Load Balancer
  alias {
    name                   = aws_lb.us_west_2.dns_name
    zone_id                = aws_lb.us_west_2.zone_id
    evaluate_target_health = true
  }
  
  health_check_id = aws_route53_health_check.us_west_2.id
}

# Regional endpoints (for direct access)
resource "aws_route53_record" "api_east_direct" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api-east.ytvideocreator.com"
  type    = "A"
  
  alias {
    name                   = aws_lb.us_east_1.dns_name
    zone_id                = aws_lb.us_east_1.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "api_west_direct" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api-west.ytvideocreator.com"
  type    = "A"
  
  alias {
    name                   = aws_lb.us_west_2.dns_name
    zone_id                = aws_lb.us_west_2.zone_id
    evaluate_target_health = true
  }
}

# Outputs
output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "hosted_zone_name_servers" {
  description = "Route53 hosted zone name servers"
  value       = aws_route53_zone.main.name_servers
}

output "api_endpoint" {
  description = "Global API endpoint (latency-based routing)"
  value       = "https://api.ytvideocreator.com"
}

output "api_east_endpoint" {
  description = "Direct us-east-1 API endpoint"
  value       = "https://api-east.ytvideocreator.com"
}

output "api_west_endpoint" {
  description = "Direct us-west-2 API endpoint"
  value       = "https://api-west.ytvideocreator.com"
}
