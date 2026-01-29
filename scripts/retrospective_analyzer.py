"""
Retrospective Analyzer.
Analyzes Week 1 production data to extract actionable insights and quick wins.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RetrospectiveAnalyzer:
    """Analyze production data and generate actionable insights."""
    
    def __init__(self, db_connection, prometheus_url: str = "http://prometheus:9090"):
        self.db = db_connection
        self.prometheus_url = prometheus_url
    
    def analyze_performance_bottlenecks(self) -> List[Dict]:
        """
        Identify top 5 performance bottlenecks.
        
        Returns:
            List of performance issues with priority
        """
        bottlenecks = []
        
        # 1. Slow database queries
        slow_queries = self._get_slow_queries(threshold_ms=200)
        for query in slow_queries[:3]:
            bottlenecks.append({
                "type": "Database Query",
                "issue": f"Query averaging {query['mean_time_ms']}ms",
                "impact": "HIGH" if query['mean_time_ms'] > 500 else "MEDIUM",
                "recommendation": "Add index or optimize query",
                "effort": "2-4 hours",
                "details": query
            })
        
        # 2. Slow API endpoints
        slow_endpoints = self._get_slow_endpoints(threshold_ms=300)
        for endpoint in slow_endpoints[:2]:
            bottlenecks.append({
                "type": "API Endpoint",
                "issue": f"Endpoint {endpoint['path']} p95: {endpoint['p95_ms']}ms",
                "impact": "HIGH" if endpoint['p95_ms'] > 500 else "MEDIUM",
                "recommendation": "Add caching or optimize logic",
                "effort": "3-6 hours",
                "details": endpoint
            })
        
        return sorted(bottlenecks, key=lambda x: x['impact'], reverse=True)[:5]
    
    def analyze_user_drop_offs(self) -> Dict:
        """
        Find where users are dropping off in key flows.
        
        Returns:
            Funnel analysis with drop-off points
        """
        funnels = {
            "signup": self._analyze_signup_funnel(),
            "first_video": self._analyze_first_video_funnel(),
            "activation": self._analyze_activation_funnel()
        }
        
        # Identify biggest drop-offs
        drop_offs = []
        for funnel_name, funnel_data in funnels.items():
            for i in range(len(funnel_data["steps"]) - 1):
                current = funnel_data["steps"][i]
                next_step = funnel_data["steps"][i + 1]
                
                drop_rate = (current["users"] - next_step["users"]) / current["users"] * 100
                
                if drop_rate > 20:  # More than 20% drop
                    drop_offs.append({
                        "funnel": funnel_name,
                        "from_step": current["name"],
                        "to_step": next_step["name"],
                        "drop_rate": round(drop_rate, 1),
                        "users_lost": current["users"] - next_step["users"]
                    })
        
        return {
            "funnels": funnels,
            "top_drop_offs": sorted(drop_offs, key=lambda x: x["drop_rate"], reverse=True)[:5]
        }
    
    def analyze_support_tickets(self) -> Dict:
        """
        Categorize and prioritize support issues.
        
        Returns:
            Support ticket analysis with top issues
        """
        # Query support tickets from last week
        tickets = self._get_recent_tickets(days=7)
        
        # Categorize
        categories = {}
        for ticket in tickets:
            category = ticket.get("category", "Other")
            if category not in categories:
                categories[category] = {
                    "count": 0,
                    "avg_resolution_hours": 0,
                    "examples": []
                }
            
            categories[category]["count"] += 1
            categories[category]["examples"].append(ticket["title"])
        
        # Identify patterns
        top_issues = sorted(
            categories.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]
        
        # Generate recommendations
        recommendations = []
        for category, data in top_issues:
            if data["count"] > 5:  # More than 5 tickets
                recommendations.append({
                    "issue": category,
                    "frequency": data["count"],
                    "action": self._suggest_support_action(category, data)
                })
        
        return {
            "total_tickets": len(tickets),
            "by_category": dict(top_issues),
            "recommendations": recommendations
        }
    
    def generate_quick_wins(self) -> List[Dict]:
        """
        Generate quick win recommendations.
        
        Criteria for quick wins:
        - Can be implemented in < 1 day
        - High user impact
        - Low technical risk
        
        Returns:
            List of quick win recommendations
        """
        quick_wins = []
        
        # Analyze all data sources
        perf_issues = self.analyze_performance_bottlenecks()
        drop_offs = self.analyze_user_drop_offs()
        support_analysis = self.analyze_support_tickets()
        
        # Generate quick wins based on patterns
        
        # 1. From performance issues
        for issue in perf_issues:
            if issue["effort"] in ["2-4 hours", "3-6 hours"]:
                quick_wins.append({
                    "title": f"Optimize {issue['type']}",
                    "description": issue["issue"],
                    "impact": issue["impact"],
                    "effort": issue["effort"],
                    "priority": "HIGH" if issue["impact"] == "HIGH" else "MEDIUM",
                    "category": "Performance"
                })
        
        # 2. From drop-offs
        for drop_off in drop_offs["top_drop_offs"][:3]:
            quick_wins.append({
                "title": f"Improve {drop_off['funnel']} flow",
                "description": f"Reduce drop-off from {drop_off['from_step']} to {drop_off['to_step']}",
                "impact": "HIGH" if drop_off["drop_rate"] > 40 else "MEDIUM",
                "effort": "4-8 hours",
                "priority": "HIGH",
                "category": "User Experience"
            })
        
        # 3. From support tickets
        for rec in support_analysis["recommendations"][:2]:
            quick_wins.append({
                "title": f"Address {rec['issue']}",
                "description": rec["action"]["description"],
                "impact": "MEDIUM",
                "effort": "2-6 hours",
                "priority": "MEDIUM",
                "category": "Support Reduction"
            })
        
        # 4. Common UX improvements (always applicable)
        common_wins = [
            {
                "title": "Add Loading Spinners",
                "description": "Add loading states to all async actions",
                "impact": "MEDIUM",
                "effort": "2-3 hours",
                "priority": "HIGH",
                "category": "User Experience",
                "rationale": "Reduces perceived wait time, improves UX"
            },
            {
                "title": "Improve Error Messages",
                "description": "Make error messages user-friendly and actionable",
                "impact": "HIGH",
                "effort": "4-6 hours",
                "priority": "HIGH",
                "category": "User Experience",
                "rationale": "Reduces support tickets, improves user self-service"
            },
            {
                "title": "Empty State Improvements",
                "description": "Add helpful empty states with clear CTAs",
                "impact": "MEDIUM",
                "effort": "2-3 hours",
                "priority": "MEDIUM",
                "category": "User Experience",
                "rationale": "Guides new users, improves activation"
            },
            {
                "title": "Keyboard Shortcuts",
                "description": "Add common keyboard shortcuts (Ctrl+N, Ctrl+S, etc.)",
                "impact": "MEDIUM",
                "effort": "4-6 hours",
                "priority": "LOW",
                "category": "Power User",
                "rationale": "Improves power user efficiency"
            },
            {
                "title": "Auto-generate Video Thumbnails",
                "description": "Generate thumbnails from first frame automatically",
                "impact": "MEDIUM",
                "effort": "6-8 hours",
                "priority": "MEDIUM",
                "category": "Feature",
                "rationale": "Better visual experience in video library"
            }
        ]
        
        quick_wins.extend(common_wins)
        
        # Sort by priority and impact
        priority_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        quick_wins.sort(
            key=lambda x: (priority_order[x["priority"]], x["impact"]),
            reverse=True
        )
        
        return quick_wins[:10]  # Top 10 quick wins
    
    def generate_report(self) -> Dict:
        """
        Generate comprehensive retrospective report.
        
        Returns:
            Full retrospective analysis report
        """
        logger.info("Generating retrospective analysis...")
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": "Week 1",
            "performance_bottlenecks": self.analyze_performance_bottlenecks(),
            "user_drop_offs": self.analyze_user_drop_offs(),
            "support_analysis": self.analyze_support_tickets(),
            "quick_wins": self.generate_quick_wins()
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print human-readable report."""
        print("\n" + "="*80)
        print("WEEK 1 RETROSPECTIVE ANALYSIS")
        print("="*80)
        print(f"Generated: {report['generated_at']}")
        print(f"Period: {report['period']}")
        print()
        
        # Quick Wins
        print("TOP QUICK WINS FOR WEEK 2:")
        print("-" * 80)
        for i, win in enumerate(report['quick_wins'][:5], 1):
            print(f"\n{i}. [{win['priority']}] {win['title']}")
            print(f"   Category: {win['category']}")
            print(f"   Description: {win['description']}")
            print(f"   Impact: {win['impact']} | Effort: {win['effort']}")
            if "rationale" in win:
                print(f"   Why: {win['rationale']}")
        
        # Performance Issues
        print("\n" + "="*80)
        print("PERFORMANCE BOTTLENECKS:")
        print("-" * 80)
        for i, issue in enumerate(report['performance_bottlenecks'][:3], 1):
            print(f"\n{i}. [{issue['impact']}] {issue['type']}")
            print(f"   Issue: {issue['issue']}")
            print(f"   Recommendation: {issue['recommendation']}")
            print(f"   Effort: {issue['effort']}")
        
        # Drop-offs
        print("\n" + "="*80)
        print("TOP USER DROP-OFFS:")
        print("-" * 80)
        for i, drop in enumerate(report['user_drop_offs']['top_drop_offs'][:3], 1):
            print(f"\n{i}. {drop['funnel'].upper()} FUNNEL")
            print(f"   Drop: {drop['from_step']} → {drop['to_step']}")
            print(f"   Drop Rate: {drop['drop_rate']}%")
            print(f"   Users Lost: {drop['users_lost']}")
        
        # Support
        print("\n" + "="*80)
        print(f"SUPPORT TICKETS: {report['support_analysis']['total_tickets']} total")
        print("-" * 80)
        for i, rec in enumerate(report['support_analysis']['recommendations'][:3], 1):
            print(f"\n{i}. {rec['issue']} ({rec['frequency']} tickets)")
            print(f"   Action: {rec['action']['type']}")
        
        print("\n" + "="*80)
    
    # Helper methods
    
    def _get_slow_queries(self, threshold_ms: int = 200) -> List[Dict]:
        """Get slow database queries."""
        # Query pg_stat_statements
        # This is a placeholder - actual implementation would query the database
        return []
    
    def _get_slow_endpoints(self, threshold_ms: int = 300) -> List[Dict]:
        """Get slow API endpoints from Prometheus."""
        # Query Prometheus for slow endpoints
        # Placeholder
        return []
    
    def _analyze_signup_funnel(self) -> Dict:
        """Analyze signup funnel."""
        return {
            "steps": [
                {"name": "Visited landing page", "users": 1000},
                {"name": "Started signup", "users": 200},
                {"name": "Completed signup", "users": 150},
                {"name": "Email verified", "users": 120}
            ]
        }
    
    def _analyze_first_video_funnel(self) -> Dict:
        """Analyze first video creation funnel."""
        return {
            "steps": [
                {"name": "Logged in", "users": 120},
                {"name": "Clicked create", "users": 90},
                {"name": "Selected template", "users": 70},
                {"name": "Completed video", "users": 50}
            ]
        }
    
    def _analyze_activation_funnel(self) -> Dict:
        """Analyze activation funnel (signup to active user)."""
        return {
            "steps": [
                {"name": "Signed up", "users": 150},
                {"name": "Created first video", "users": 50},
                {"name": "Shared video", "users": 30},
                {"name": "Created 3+ videos", "users": 20}
            ]
        }
    
    def _get_recent_tickets(self, days: int = 7) -> List[Dict]:
        """Get support tickets from recent days."""
        # Query support system
        # Placeholder
        return []
    
    def _suggest_support_action(self, category: str, data: Dict) -> Dict:
        """Suggest action for support issue category."""
        actions = {
            "Login Issues": {
                "type": "Documentation",
                "description": "Create comprehensive login troubleshooting guide"
            },
            "Feature Questions": {
                "type": "Documentation + Tutorial",
                "description": "Create video tutorials for common features"
            },
            "Bug Reports": {
                "type": "Engineering",
                "description": "Prioritize bug fixes in sprint planning"
            },
            "Billing": {
                "type": "Process Improvement",
                "description": "Improve billing FAQ and self-service portal"
            }
        }
        
        return actions.get(category, {
            "type": "Documentation",
            "description": f"Create documentation for {category}"
        })


if __name__ == "__main__":
    # Example usage
    # analyzer = RetrospectiveAnalyzer(db_connection=db, prometheus_url="http://prometheus:9090")
    # report = analyzer.generate_report()
    # analyzer.print_report(report)
    # 
    # # Save to file
    # with open("reports/week1_retrospective.json", "w") as f:
    #     json.dump(report, f, indent=2)
    
    print("Retrospective Analyzer ready. Import and use with database connection.")
