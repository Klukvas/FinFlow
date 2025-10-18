"""
Log Enrichment Service

This service provides log enrichment capabilities to add metadata,
correlation IDs, and contextual information to log entries.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
import os

@dataclass
class EnrichmentContext:
    """Context for log enrichment"""
    request_id: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    service_name: str = ""
    environment: str = "development"
    version: str = "1.0.0"
    hostname: str = ""
    ip_address: Optional[str] = None

class LogEnricher:
    """Service for enriching log entries with additional metadata"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.user_cache = {}
        self.geo_cache = {}
        self.correlation_cache = {}
        
    def enrich_log_entry(self, log_entry: Dict[str, Any], context: EnrichmentContext) -> Dict[str, Any]:
        """Enrich a single log entry with additional metadata"""
        enriched = log_entry.copy()
        
        # Add basic context
        enriched.update({
            "request_id": context.request_id,
            "service_name": context.service_name,
            "environment": context.environment,
            "version": context.version,
            "hostname": context.hostname,
            "enrichment_timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Add user context if available
        if context.user_id:
            enriched["user_id"] = context.user_id
            enriched.update(self._get_user_context(context.user_id))
        
        # Add session context if available
        if context.session_id:
            enriched["session_id"] = context.session_id
        
        # Add IP geolocation if available
        if context.ip_address:
            enriched["ip_address"] = context.ip_address
            enriched.update(self._get_geo_context(context.ip_address))
        
        # Add correlation information
        enriched.update(self._get_correlation_context(context))
        
        # Add business context
        enriched.update(self._get_business_context(log_entry, context))
        
        return enriched
    
    def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get user context information"""
        if user_id in self.user_cache:
            return self.user_cache[user_id]
        
        try:
            # In a real implementation, this would call the user service
            # For now, we'll return basic information
            user_context = {
                "user_email": f"user{user_id}@example.com",
                "user_role": "user",
                "user_status": "active"
            }
            
            # Cache for 5 minutes
            self.user_cache[user_id] = user_context
            return user_context
            
        except Exception as e:
            return {"user_context_error": str(e)}
    
    def _get_geo_context(self, ip_address: str) -> Dict[str, Any]:
        """Get geolocation context for IP address"""
        if ip_address in self.geo_cache:
            return self.geo_cache[ip_address]
        
        try:
            # In a real implementation, this would call a geolocation service
            # For now, we'll return mock data
            geo_context = {
                "country": "Unknown",
                "region": "Unknown",
                "city": "Unknown",
                "timezone": "UTC"
            }
            
            # Cache for 1 hour
            self.geo_cache[ip_address] = geo_context
            return geo_context
            
        except Exception as e:
            return {"geo_context_error": str(e)}
    
    def _get_correlation_context(self, context: EnrichmentContext) -> Dict[str, Any]:
        """Get correlation context for request tracing"""
        correlation_id = f"{context.service_name}_{context.request_id}"
        
        if correlation_id in self.correlation_cache:
            return self.correlation_cache[correlation_id]
        
        correlation_context = {
            "correlation_id": correlation_id,
            "trace_id": str(uuid.uuid4()),
            "span_id": str(uuid.uuid4())[:8],
            "parent_span_id": None  # Would be set by parent service
        }
        
        # Cache for 1 hour
        self.correlation_cache[correlation_id] = correlation_context
        return correlation_context
    
    def _get_business_context(self, log_entry: Dict[str, Any], context: EnrichmentContext) -> Dict[str, Any]:
        """Get business-specific context based on log content"""
        business_context = {}
        
        # Extract business metrics from log message
        message = log_entry.get("message", "")
        
        # Check for expense-related logs
        if "expense" in message.lower():
            business_context["business_domain"] = "expense_management"
            business_context["entity_type"] = "expense"
        
        # Check for user-related logs
        elif "user" in message.lower():
            business_context["business_domain"] = "user_management"
            business_context["entity_type"] = "user"
        
        # Check for authentication logs
        elif "auth" in message.lower() or "login" in message.lower():
            business_context["business_domain"] = "authentication"
            business_context["entity_type"] = "auth_event"
        
        # Check for API logs
        elif "api" in message.lower():
            business_context["business_domain"] = "api_management"
            business_context["entity_type"] = "api_request"
        
        # Add performance metrics if available
        if "duration" in log_entry:
            business_context["performance_metric"] = "duration"
            business_context["performance_value"] = log_entry["duration"]
        
        return business_context
    
    def batch_enrich_logs(self, log_entries: List[Dict[str, Any]], context: EnrichmentContext) -> List[Dict[str, Any]]:
        """Enrich a batch of log entries"""
        return [self.enrich_log_entry(entry, context) for entry in log_entries]
    
    def clear_caches(self):
        """Clear all caches"""
        self.user_cache.clear()
        self.geo_cache.clear()
        self.correlation_cache.clear()

class LogCorrelator:
    """Service for correlating logs across services and time"""
    
    def __init__(self):
        self.correlation_store = {}
        self.time_window = 300  # 5 minutes in seconds
    
    def correlate_logs(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Correlate logs by request_id, session_id, and other identifiers"""
        correlated_logs = []
        
        # Group logs by correlation identifiers
        correlation_groups = self._group_by_correlation(log_entries)
        
        for group_id, group_logs in correlation_groups.items():
            # Add correlation metadata to each log in the group
            for log_entry in group_logs:
                log_entry["correlation_group"] = group_id
                log_entry["correlation_count"] = len(group_logs)
                log_entry["correlation_services"] = list(set(
                    log.get("service_name", "unknown") for log in group_logs
                ))
                correlated_logs.append(log_entry)
        
        return correlated_logs
    
    def _group_by_correlation(self, log_entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group logs by correlation identifiers"""
        groups = {}
        
        for log_entry in log_entries:
            # Try different correlation identifiers
            correlation_id = (
                log_entry.get("request_id") or
                log_entry.get("session_id") or
                log_entry.get("transaction_id") or
                f"fallback_{int(time.time())}"
            )
            
            if correlation_id not in groups:
                groups[correlation_id] = []
            
            groups[correlation_id].append(log_entry)
        
        return groups

class LogAnalyzer:
    """Service for analyzing log patterns and extracting insights"""
    
    def __init__(self):
        self.patterns = {
            "error_patterns": [
                r"ERROR.*",
                r"Exception.*",
                r"Failed.*",
                r"Timeout.*"
            ],
            "performance_patterns": [
                r"duration.*ms",
                r"slow.*query",
                r"timeout.*"
            ],
            "security_patterns": [
                r"Security.*",
                r"Unauthorized.*",
                r"Failed.*login",
                r"Invalid.*token"
            ]
        }
    
    def analyze_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single log entry for patterns and insights"""
        analysis = {
            "patterns_detected": [],
            "severity_score": 0,
            "category": "unknown",
            "insights": []
        }
        
        message = log_entry.get("message", "").lower()
        level = log_entry.get("level", "").lower()
        
        # Detect error patterns
        if any(pattern.lower() in message for pattern in self.patterns["error_patterns"]):
            analysis["patterns_detected"].append("error")
            analysis["severity_score"] += 3
        
        # Detect performance patterns
        if any(pattern.lower() in message for pattern in self.patterns["performance_patterns"]):
            analysis["patterns_detected"].append("performance")
            analysis["severity_score"] += 1
        
        # Detect security patterns
        if any(pattern.lower() in message for pattern in self.patterns["security_patterns"]):
            analysis["patterns_detected"].append("security")
            analysis["severity_score"] += 4
        
        # Categorize based on level and patterns
        if level == "error" or "error" in analysis["patterns_detected"]:
            analysis["category"] = "error"
        elif level == "warning" or "security" in analysis["patterns_detected"]:
            analysis["category"] = "warning"
        elif "performance" in analysis["patterns_detected"]:
            analysis["category"] = "performance"
        else:
            analysis["category"] = "info"
        
        # Generate insights
        if analysis["severity_score"] > 5:
            analysis["insights"].append("High severity event detected")
        
        if "security" in analysis["patterns_detected"]:
            analysis["insights"].append("Security-related event")
        
        if "performance" in analysis["patterns_detected"]:
            analysis["insights"].append("Performance issue detected")
        
        return analysis

# Factory functions for easy integration
def create_enricher(config: Dict[str, Any] = None) -> LogEnricher:
    """Create a log enricher instance"""
    return LogEnricher(config)

def create_correlator() -> LogCorrelator:
    """Create a log correlator instance"""
    return LogCorrelator()

def create_analyzer() -> LogAnalyzer:
    """Create a log analyzer instance"""
    return LogAnalyzer()

# Example usage
if __name__ == "__main__":
    # Create services
    enricher = create_enricher()
    correlator = create_correlator()
    analyzer = create_analyzer()
    
    # Example log entry
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR",
        "message": "Database connection failed",
        "service": "user_service"
    }
    
    # Create context
    context = EnrichmentContext(
        request_id="req_123",
        user_id=456,
        service_name="user_service",
        hostname="server-01"
    )
    
    # Enrich log
    enriched_log = enricher.enrich_log_entry(log_entry, context)
    print("Enriched log:", json.dumps(enriched_log, indent=2))
    
    # Analyze log
    analysis = analyzer.analyze_log_entry(enriched_log)
    print("Analysis:", json.dumps(analysis, indent=2))
