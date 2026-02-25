"""
Configuration and environment variable validation.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """Application configuration with environment validation."""
    
    def __init__(self):
        self.validate_environment()
        
        # Application settings
        self.app_name = "Crop Recommendation ML API"
        self.version = "4.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Server settings
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "7860"))
        self.workers = int(os.getenv("WORKERS", "4"))
        
        # Model settings
        self.model_registry_path = os.getenv("MODEL_REGISTRY_PATH", "model_registry.json")
        self.nutrients_path = os.getenv("NUTRIENTS_PATH", "Nutrient.csv")
        
        # Logging settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.structured_logging = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
        
        # Performance settings
        self.max_requests = int(os.getenv("MAX_REQUESTS", "1000"))
        self.max_requests_jitter = int(os.getenv("MAX_REQUESTS_JITTER", "100"))
        self.timeout = int(os.getenv("TIMEOUT", "120"))
        
        # Monitoring (optional)
        self.sentry_dsn = os.getenv("SENTRY_DSN")
        
        logger.info(f"Configuration loaded. Debug: {self.debug}, Workers: {self.workers}")
    
    def validate_environment(self):
        """Validate critical environment variables."""
        required_files = [
            "model_registry.json",
            "Nutrient.csv"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            error_msg = f"Missing required files: {', '.join(missing_files)}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Validate model registry exists and is valid JSON
        try:
            import json
            with open("model_registry.json", "r") as f:
                registry = json.load(f)
                
            # Check required structure
            required_sections = ["models", "crop_mappings", "version"]
            for section in required_sections:
                if section not in registry:
                    raise ValueError(f"Invalid model registry: missing section '{section}'")
                    
            logger.info("Environment validation passed")
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid model registry JSON: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Environment validation failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)


# Global config instance
config = Config()
