"""
Monitoring and Metrics System for Crop Recommendation System
===========================================================
Provides structured logging, performance metrics, and health monitoring.
"""

import time
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)

@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    method: str
    path: str
    status_code: int
    duration: float
    timestamp: datetime
    ip_address: str
    user_agent: str

@dataclass
class ModelMetrics:
    """Metrics for model predictions."""
    model_type: str
    mode: str
    prediction_count: int
    avg_confidence: float
    avg_duration: float
    error_count: int
    timestamp: datetime

class MetricsCollector:
    """Collects and manages application metrics."""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.request_metrics: deque = deque(maxlen=max_history)
        self.model_metrics: deque = deque(maxlen=max_history)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.performance_stats: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_request(self, method: str, path: str, status_code: int, 
                      duration: float, ip_address: str, user_agent: str):
        """Record a request metric."""
        metric = RequestMetrics(
            method=method,
            path=path,
            status_code=status_code,
            duration=duration,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        with self._lock:
            self.request_metrics.append(metric)
            self.performance_stats[f"{method} {path}"].append(duration)
            
            # Keep only recent performance stats
            if len(self.performance_stats[f"{method} {path}"]) > 1000:
                self.performance_stats[f"{method} {path}"] = self.performance_stats[f"{method} {path}"][-1000:]
        
        # Log slow requests
        if duration > 5.0:  # 5 second threshold
            logger.warning(f"Slow request: {method} {path} took {duration:.3f}s")
    
    def record_model_prediction(self, model_type: str, mode: str, 
                              confidence: float, duration: float, 
                              success: bool = True):
        """Record a model prediction metric."""
        metric = ModelMetrics(
            model_type=model_type,
            mode=mode,
            prediction_count=1,
            avg_confidence=confidence,
            avg_duration=duration,
            error_count=0 if success else 1,
            timestamp=datetime.now()
        )
        
        with self._lock:
            self.model_metrics.append(metric)
            
            if not success:
                error_key = f"{model_type}_{mode}"
                self.error_counts[error_key] += 1
    
    def record_error(self, error_type: str, details: str):
        """Record an error occurrence."""
        with self._lock:
            self.error_counts[error_type] += 1
        
        logger.error(f"Error recorded: {error_type} - {details}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        with self._lock:
            # Request statistics
            total_requests = len(self.request_metrics)
            recent_requests = [r for r in self.request_metrics 
                             if r.timestamp > datetime.now() - timedelta(hours=1)]
            
            # Calculate averages and percentiles
            avg_response_time = 0
            p95_response_time = 0
            error_rate = 0
            
            if recent_requests:
                durations = [r.duration for r in recent_requests]
                avg_response_time = sum(durations) / len(durations)
                sorted_durations = sorted(durations)
                p95_response_time = sorted_durations[int(len(sorted_durations) * 0.95)]
                
                error_count = sum(1 for r in recent_requests if r.status_code >= 400)
                error_rate = (error_count / len(recent_requests)) * 100
            
            # Model statistics
            model_stats = defaultdict(lambda: {'count': 0, 'avg_confidence': 0, 'avg_duration': 0})
            for metric in self.model_metrics:
                key = f"{metric.model_type}_{metric.mode}"
                model_stats[key]['count'] += metric.prediction_count
                model_stats[key]['avg_confidence'] += metric.avg_confidence
                model_stats[key]['avg_duration'] += metric.avg_duration
            
            # Calculate averages for model stats
            for stats in model_stats.values():
                if stats['count'] > 0:
                    stats['avg_confidence'] /= stats['count']
                    stats['avg_duration'] /= stats['count']
            
            return {
                'timestamp': datetime.now().isoformat(),
                'requests': {
                    'total': total_requests,
                    'last_hour': len(recent_requests),
                    'avg_response_time': round(avg_response_time, 3),
                    'p95_response_time': round(p95_response_time, 3),
                    'error_rate': round(error_rate, 2)
                },
                'models': dict(model_stats),
                'errors': dict(self.error_counts),
                'performance': {
                    endpoint: {
                        'avg_duration': round(sum(durations) / len(durations), 3),
                        'max_duration': round(max(durations), 3),
                        'min_duration': round(min(durations), 3),
                        'request_count': len(durations)
                    }
                    for endpoint, durations in self.performance_stats.items()
                    if durations
                }
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        summary = self.get_summary()
        
        # Determine health status
        status = "healthy"
        issues = []
        
        # Check error rate
        if summary['requests']['error_rate'] > 10:
            status = "unhealthy"
            issues.append(f"High error rate: {summary['requests']['error_rate']}%")
        elif summary['requests']['error_rate'] > 5:
            status = "degraded"
            issues.append(f"Elevated error rate: {summary['requests']['error_rate']}%")
        
        # Check response times
        if summary['requests']['avg_response_time'] > 10:
            status = "unhealthy"
            issues.append(f"Very slow response time: {summary['requests']['avg_response_time']}s")
        elif summary['requests']['avg_response_time'] > 5:
            status = "degraded"
            issues.append(f"Slow response time: {summary['requests']['avg_response_time']}s")
        
        # Check for recent errors
        recent_errors = sum(1 for r in self.request_metrics 
                          if r.status_code >= 500 and 
                          r.timestamp > datetime.now() - timedelta(minutes=5))
        
        if recent_errors > 10:
            status = "unhealthy"
            issues.append(f"Many recent server errors: {recent_errors}")
        elif recent_errors > 5:
            status = "degraded"
            issues.append(f"Some recent server errors: {recent_errors}")
        
        return {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'issues': issues,
            'metrics': summary
        }
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self.request_metrics.clear()
            self.model_metrics.clear()
            self.error_counts.clear()
            self.performance_stats.clear()

# Global metrics collector
metrics = MetricsCollector()

class StructuredLogger:
    """Structured logger for consistent log formatting."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_request(self, method: str, path: str, status_code: int, 
                   duration: float, ip_address: str, user_agent: str):
        """Log a request with structured format."""
        self.logger.info(json.dumps({
            'event': 'request',
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration': duration,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.now().isoformat()
        }))
    
    def log_prediction(self, model_type: str, mode: str, confidence: float, 
                      duration: float, crop: str, success: bool = True):
        """Log a prediction with structured format."""
        self.logger.info(json.dumps({
            'event': 'prediction',
            'model_type': model_type,
            'mode': mode,
            'confidence': confidence,
            'duration': duration,
            'predicted_crop': crop,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }))
    
    def log_error(self, error_type: str, error_message: str, 
                 context: Optional[Dict[str, Any]] = None):
        """Log an error with structured format."""
        log_data = {
            'event': 'error',
            'error_type': error_type,
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        
        if context:
            log_data['context'] = context
        
        self.logger.error(json.dumps(log_data))
    
    def log_performance(self, operation: str, duration: float, 
                       metadata: Optional[Dict[str, Any]] = None):
        """Log performance metrics."""
        log_data = {
            'event': 'performance',
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        if metadata:
            log_data['metadata'] = metadata
        
        self.logger.info(json.dumps(log_data))

def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    return metrics

def get_logger(name: str) -> StructuredLogger:
    """Get structured logger."""
    return StructuredLogger(name)
