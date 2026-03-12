"""
Structured JSON logging configuration.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """Structured JSON logger with prediction metrics."""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create JSON formatter
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_prediction(self, 
                      mode: str, 
                      latency_ms: float, 
                      cache_hit: bool = False,
                      error_type: Optional[str] = None,
                      additional_data: Optional[Dict[str, Any]] = None):
        """Log prediction with metrics."""
        log_data = {
            "event": "prediction",
            "mode": mode,
            "latency_ms": round(latency_ms, 2),
            "cache_hit": cache_hit,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if error_type:
            log_data["error_type"] = error_type
            self.logger.error(json.dumps(log_data))
        else:
            if additional_data:
                log_data.update(additional_data)
            self.logger.info(json.dumps(log_data))
    
    def log_model_load(self, mode: str, load_time_ms: float, model_file: str):
        """Log model loading event."""
        log_data = {
            "event": "model_load",
            "mode": mode,
            "load_time_ms": round(load_time_ms, 2),
            "model_file": model_file,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.logger.info(json.dumps(log_data))
    
    def log_health_check(self, status: str, details: Optional[Dict[str, Any]] = None):
        """Log health check event."""
        log_data = {
            "event": "health_check",
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if details:
            log_data.update(details)
            
        if status == "healthy":
            self.logger.info(json.dumps(log_data))
        else:
            self.logger.warning(json.dumps(log_data))
    
    def log_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """Log error with context."""
        log_data = {
            "event": "error",
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if context:
            log_data.update(context)
            
        self.logger.error(json.dumps(log_data))


# Prediction timing decorator
def log_prediction_time(logger: StructuredLogger, mode: str):
    """Decorator to log prediction execution time."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error_type = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_type = type(e).__name__
                raise
            finally:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                logger.log_prediction(
                    mode=mode,
                    latency_ms=latency_ms,
                    error_type=error_type
                )
        
        return wrapper
    return decorator


# Initialize structured logger
structured_logger = StructuredLogger("ml_api_v4")
