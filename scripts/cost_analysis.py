"""
AWS cost analysis script.
Analyzes cloud costs and identifies optimization opportunities.
"""
import boto3
from datetime import datetime, timedelta
from typing import Dict, List
import json


class CostAnalyzer:
    """Analyze AWS costs and identify savings opportunities."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize cost analyzer."""
        self.ce = boto3.client('ce', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
    
    def get_monthly_costs(self, months: int = 3) -> List[Dict]:
        """
        Get monthly costs for the last N months.
        
        Args:
            months: Number of months to analyze
            
        Returns:
            List of cost data by month
        """
        end = datetime.now().date()
        start = end - timedelta(days=30 * months)
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start.strftime('%Y-%m-%d'),
                'End': end.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost', 'UsageQuantity'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        monthly_costs = []
        for result in response['ResultsByTime']:
            month_data = {
                'period': result['TimePeriod']['Start'],
                'total': 0,
                'services': {}
            }
            
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                month_data['services'][service] = cost
                month_data['total'] += cost
            
            monthly_costs.append(month_data)
        
        return monthly_costs
    
    def get_cost_by_service(self, days: int = 30) -> Dict[str, float]:
        """
        Get cost breakdown by AWS service.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary of service costs
        """
        end = datetime.now().date()
        start = end - timedelta(days=days)
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start.strftime('%Y-%m-%d'),
                'End': end.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        costs = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                costs[service] = costs.get(service, 0) + cost
        
        return costs
    
    def get_cost_by_tag(self, tag_key: str, days: int = 30) -> Dict[str, float]:
        """
        Get cost breakdown by tag.
        
        Args:
            tag_key: Tag key to group by (e.g., 'Environment')
            days: Number of days to analyze
            
        Returns:
            Dictionary of tag costs
        """
        end = datetime.now().date()
        start = end - timedelta(days=days)
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start.strftime('%Y-%m-%d'),
                'End': end.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'TAG', 'Key': tag_key}
            ]
        )
        
        costs = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                tag_value = group['Keys'][0].replace(f"{tag_key}$", "")
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                costs[tag_value] = costs.get(tag_value, 0) + cost
        
        return costs
    
    def identify_savings_opportunities(self) -> List[Dict]:
        """
        Identify cost savings opportunities.
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for idle resources
        # (This is a simplified example - production would be more comprehensive)
        
        # 1. Check for stopped instances
        ec2_response = self.ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}]
        )
        
        stopped_count = 0
        for reservation in ec2_response['Reservations']:
            stopped_count += len(reservation['Instances'])
        
        if stopped_count > 0:
            recommendations.append({
                'type': 'idle_resources',
                'resource': 'EC2 Instances',
                'count': stopped_count,
                'recommendation': f'Terminate {stopped_count} stopped instances',
                'potential_savings': '$50-200/month'
            })
        
        # 2. Check for old snapshots
        snapshot_response = self.ec2.describe_snapshots(OwnerIds=['self'])
        old_snapshots = []
        
        cutoff_date = datetime.now() - timedelta(days=90)
        for snapshot in snapshot_response['Snapshots']:
            if snapshot['StartTime'].replace(tzinfo=None) < cutoff_date:
                old_snapshots.append(snapshot)
        
        if old_snapshots:
            recommendations.append({
                'type': 'old_resources',
                'resource': 'EBS Snapshots',
                'count': len(old_snapshots),
                'recommendation': f'Delete {len(old_snapshots)} snapshots >90 days old',
                'potential_savings': f'${len(old_snapshots) * 0.05}/month'
            })
        
        return recommendations
    
    def print_cost_report(self):
        """Print comprehensive cost report."""
        print("\n" + "="*60)
        print("AWS Cost Analysis Report")
        print("="*60 + "\n")
        
        # Monthly costs
        print("Monthly Costs (Last 3 Months):")
        monthly = self.get_monthly_costs(3)
        for month in monthly:
            print(f"  {month['period']}: ${month['total']:.2f}")
        print()
        
        # Cost by service
        print("Cost by Service (Last 30 Days):")
        services = self.get_cost_by_service(30)
        for service, cost in sorted(services.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {service}: ${cost:.2f}")
        print()
        
        # Cost by environment
        print("Cost by Environment (Last 30 Days):")
        try:
            environments = self.get_cost_by_tag('Environment', 30)
            for env, cost in sorted(environments.items(), key=lambda x: x[1], reverse=True):
                print(f"  {env}: ${cost:.2f}")
        except:
            print("  (No environment tags found)")
        print()
        
        # Savings opportunities
        print("Savings Opportunities:")
        recommendations = self.identify_savings_opportunities()
        if recommendations:
            for rec in recommendations:
                print(f"  • {rec['recommendation']}")
                print(f"    Potential savings: {rec['potential_savings']}")
        else:
            print("  No immediate opportunities identified")
        print()
        
        print("="*60 + "\n")


if __name__ == "__main__":
    analyzer = CostAnalyzer()
    analyzer.print_cost_report()
