"""
Performance Analysis Script.
Analyzes production performance and suggests optimizations.
"""
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict
import requests
import json


class PerformanceAnalyzer:
    """Analyze production performance and identify optimization opportunities."""
    
    def __init__(self, db_config: Dict, prometheus_url: str = "http://prometheus:9090"):
        self.db_config = db_config
        self.prometheus_url = prometheus_url
        self.recommendations = []
    
    def connect_db(self):
        """Connect to PostgreSQL."""
        return psycopg2.connect(**self.db_config)
    
    def analyze_slow_queries(self, threshold_ms: int = 100) -> List[Dict]:
        """
        Find queries slower than threshold.
        
        Args:
            threshold_ms: Threshold in milliseconds
            
        Returns:
            List of slow queries with stats
        """
        conn = self.connect_db()
        cur = conn.cursor()
        
        query = """
        SELECT 
            query,
            calls,
            total_exec_time,
            mean_exec_time,
            min_exec_time,
            max_exec_time,
            stddev_exec_time
        FROM pg_stat_statements
        WHERE mean_exec_time > %s
        ORDER BY mean_exec_time DESC
        LIMIT 20;
        """
        
        cur.execute(query, (threshold_ms,))
        results = []
        
        for row in cur.fetchall():
            results.append({
                "query": row[0],
                "calls": row[1],
                "total_time_ms": round(row[2], 2),
                "mean_time_ms": round(row[3], 2),
                "min_time_ms": round(row[4], 2),
                "max_time_ms": round(row[5], 2),
                "stddev_ms": round(row[6], 2)
            })
        
        cur.close()
        conn.close()
        
        return results
    
    def analyze_missing_indexes(self) -> List[Dict]:
        """Suggest missing indexes based on sequential scans."""
        conn = self.connect_db()
        cur = conn.cursor()
        
        query = """
        SELECT
            schemaname,
            tablename,
            seq_scan,
            seq_tup_read,
            idx_scan,
            seq_tup_read / seq_scan as avg_seq_read
        FROM pg_stat_user_tables
        WHERE seq_scan > 0
        ORDER BY seq_scan DESC, seq_tup_read DESC
        LIMIT 20;
        """
        
        cur.execute(query)
        results = []
        
        for row in cur.fetchall():
            if row[2] > 1000:  # More than 1000 sequential scans
                results.append({
                    "schema": row[0],
                    "table": row[1],
                    "seq_scans": row[2],
                    "seq_tuples_read": row[3],
                    "index_scans": row[4] or 0,
                    "avg_seq_read": round(row[5], 2) if row[5] else 0,
                    "recommendation": f"Consider adding index to {row[1]}"
                })
        
        cur.close()
        conn.close()
        
        return results
    
    def analyze_table_bloat(self) -> List[Dict]:
        """Check for table bloat."""
        conn = self.connect_db()
        cur = conn.cursor()
        
        query = """
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            n_dead_tup,
            n_live_tup,
            CASE 
                WHEN n_live_tup > 0 
                THEN round(100.0 * n_dead_tup / n_live_tup, 2)
                ELSE 0
            END as dead_tuple_pct
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 1000
        ORDER BY n_dead_tup DESC
        LIMIT 10;
        """
        
        cur.execute(query)
        results = []
        
        for row in cur.fetchall():
            results.append({
                "schema": row[0],
                "table": row[1],
                "size": row[2],
                "dead_tuples": row[3],
                "live_tuples": row[4],
                "dead_pct": row[5]
            })
        
        cur.close()
        conn.close()
        
        return results
    
    def analyze_slow_endpoints(self) -> List[Dict]:
        """Find slow API endpoints from Prometheus."""
        query = '''
        topk(20,
            histogram_quantile(0.95,
                rate(http_request_duration_seconds_bucket[24h])
            ) * 1000
        ) by (endpoint, method)
        '''
        
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get("data", {}).get("result", []):
                    metric = item["metric"]
                    value = float(item["value"][1])
                    
                    results.append({
                        "endpoint": metric.get("endpoint", "unknown"),
                        "method": metric.get("method", "unknown"),
                        "p95_latency_ms": round(value, 2)
                    })
                
                return sorted(results, key=lambda x: x["p95_latency_ms"], reverse=True)
        
        except Exception as e:
            print(f"Error querying Prometheus: {e}")
            return []
    
    def analyze_cache_hit_rate(self) -> Dict:
        """Analyze Redis cache hit rate."""
        query = 'rate(redis_keyspace_hits_total[24h]) / (rate(redis_keyspace_hits_total[24h]) + rate(redis_keyspace_misses_total[24h]))'
        
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("data", {}).get("result", [])
                
                if results:
                    hit_rate = float(results[0]["value"][1])
                    return {
                        "hit_rate": round(hit_rate * 100, 2),
                        "status": "good" if hit_rate > 0.8 else "needs_improvement"
                    }
        
        except Exception as e:
            print(f"Error analyzing cache: {e}")
        
        return {"hit_rate": 0, "status": "unknown"}
    
    def analyze_connection_pool(self) -> Dict:
        """Analyze database connection pool usage."""
        conn = self.connect_db()
        cur = conn.cursor()
        
        # Current connections
        cur.execute("SELECT count(*) FROM pg_stat_activity;")
        current_connections = cur.fetchone()[0]
        
        # Max connections
        cur.execute("SHOW max_connections;")
        max_connections = int(cur.fetchone()[0])
        
        # Connection states
        cur.execute("""
            SELECT state, count(*) 
            FROM pg_stat_activity 
            GROUP BY state;
        """)
        
        states = {}
        for row in cur.fetchall():
            states[row[0] or 'unknown'] = row[1]
        
        cur.close()
        conn.close()
        
        usage_pct = (current_connections / max_connections) * 100
        
        return {
            "current": current_connections,
            "max": max_connections,
            "usage_pct": round(usage_pct, 2),
            "states": states,
            "status": "critical" if usage_pct > 80 else "warning" if usage_pct > 60 else "ok"
        }
    
    def generate_recommendations(self, analysis: Dict):
        """Generate optimization recommendations."""
        recommendations = []
        
        # Slow queries
        if analysis["slow_queries"]:
            for query in analysis["slow_queries"][:5]:
                recommendations.append({
                    "type": "Database Query",
                    "priority": "HIGH" if query["mean_time_ms"] > 500 else "MEDIUM",
                    "issue": f"Query averaging {query['mean_time_ms']}ms",
                    "recommendation": "Optimize query or add indexes",
                    "details": query
                })
        
        # Missing indexes
        if analysis["missing_indexes"]:
            for table in analysis["missing_indexes"][:3]:
                if table["seq_scans"] > 10000:
                    recommendations.append({
                        "type": "Database Index",
                        "priority": "HIGH",
                        "issue": f"Table {table['table']} has {table['seq_scans']} sequential scans",
                        "recommendation": f"Add index to frequently queried columns in {table['table']}",
                        "details": table
                    })
        
        # Table bloat
        if analysis["table_bloat"]:
            for table in analysis["table_bloat"]:
                if table["dead_pct"] > 20:
                    recommendations.append({
                        "type": "Database Maintenance",
                        "priority": "MEDIUM",
                        "issue": f"Table {table['table']} has {table['dead_pct']}% dead tuples",
                        "recommendation": f"Run VACUUM on {table['table']}",
                        "details": table
                    })
        
        # Slow endpoints
        if analysis["slow_endpoints"]:
            for endpoint in analysis["slow_endpoints"][:5]:
                if endpoint["p95_latency_ms"] > 200:
                    recommendations.append({
                        "type": "API Performance",
                        "priority": "HIGH" if endpoint["p95_latency_ms"] > 500 else "MEDIUM",
                        "issue": f"Endpoint {endpoint['endpoint']} p95: {endpoint['p95_latency_ms']}ms",
                        "recommendation": "Profile and optimize endpoint, consider caching",
                        "details": endpoint
                    })
        
        # Cache hit rate
        cache = analysis["cache_hit_rate"]
        if cache["hit_rate"] < 80:
            recommendations.append({
                "type": "Caching",
                "priority": "MEDIUM",
                "issue": f"Cache hit rate is {cache['hit_rate']}%",
                "recommendation": "Identify cacheable endpoints, tune TTLs",
                "details": cache
            })
        
        # Connection pool
        pool = analysis["connection_pool"]
        if pool["status"] in ["warning", "critical"]:
            recommendations.append({
                "type": "Connection Pool",
                "priority": "HIGH" if pool["status"] == "critical" else "MEDIUM",
                "issue": f"Connection pool usage at {pool['usage_pct']}%",
                "recommendation": "Increase pool size or fix connection leaks",
                "details": pool
            })
        
        return recommendations
    
    def generate_report(self) -> Dict:
        """Generate comprehensive performance report."""
        print("Analyzing performance...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "slow_queries": self.analyze_slow_queries(),
            "missing_indexes": self.analyze_missing_indexes(),
            "table_bloat": self.analyze_table_bloat(),
            "slow_endpoints": self.analyze_slow_endpoints(),
            "cache_hit_rate": self.analyze_cache_hit_rate(),
            "connection_pool": self.analyze_connection_pool()
        }
        
        recommendations = self.generate_recommendations(analysis)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "analysis": analysis,
            "recommendations": recommendations,
            "summary": {
                "total_issues": len(recommendations),
                "high_priority": len([r for r in recommendations if r["priority"] == "HIGH"]),
                "medium_priority": len([r for r in recommendations if r["priority"] == "MEDIUM"]),
                "low_priority": len([r for r in recommendations if r["priority"] == "LOW"])
            }
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print human-readable report."""
        print("\n" + "="*80)
        print("PERFORMANCE ANALYSIS REPORT")
        print("="*80)
        print(f"Generated: {report['generated_at']}")
        print()
        
        summary = report['summary']
        print(f"Total Issues: {summary['total_issues']}")
        print(f"  - HIGH priority: {summary['high_priority']}")
        print(f"  - MEDIUM priority: {summary['medium_priority']}")
        print(f"  - LOW priority: {summary['low_priority']}")
        print()
        
        if report['recommendations']:
            print("TOP RECOMMENDATIONS:")
            print("-" * 80)
            
            for i, rec in enumerate(report['recommendations'][:10], 1):
                print(f"\n{i}. [{rec['priority']}] {rec['type']}")
                print(f"   Issue: {rec['issue']}")
                print(f"   Recommendation: {rec['recommendation']}")
        else:
            print("✅ No performance issues detected!")
        
        print("\n" + "="*80)
    
    def save_report(self, report: Dict, filename: str = None):
        """Save report to JSON file."""
        if filename is None:
            filename = f"reports/performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: {filename}")


if __name__ == "__main__":
    # Configuration
    db_config = {
        "host": "postgres-0.postgres.production.svc.cluster.local",
        "port": 5432,
        "database": "ytvideocreator",
        "user": "postgres",
        "password": "your-password"  # Use from env var
    }
    
    analyzer = PerformanceAnalyzer(db_config)
    report = analyzer.generate_report()
    analyzer.print_report(report)
    analyzer.save_report(report)
