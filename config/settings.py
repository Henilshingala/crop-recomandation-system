"""
Centralized Configuration System for Crop Recommendation System
==============================================================
Provides unified configuration management across all components.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

class Config:
    """Centralized configuration class with environment variable support."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.environ.get('CONFIG_FILE', 'config.json')
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment variables."""
        config = {
            # Default configuration
            'app': {
                'name': 'Crop Recommendation System',
                'version': '4.0',
                'debug': False,
                'log_level': 'INFO'
            },
            'database': {
                'url': None,  # Will be set from DATABASE_URL env var
                'engine': 'postgresql',
                'pool_size': 10,
                'max_overflow': 20
            },
            'ml_models': {
                'ensemble': {
                    'type': 'stacked-ensemble-v3',
                    'features': ['n', 'p', 'k', 'temperature', 'humidity', 'ph', 'rainfall', 'season', 'soil_type', 'irrigation', 'moisture'],
                    'temperature': 1.0,
                    'entropy_threshold': 0.4,
                    'dominance_penalty': 0.15,
                    'confidence_threshold': 0.3
                },
                'synthetic': {
                    'type': 'random-forest-v1',
                    'n_estimators': 200,
                    'max_depth': 20
                },
                'hybrid': {
                    'type': 'hybrid-v4',
                    'blend_weights': {
                        'real': 0.7,
                        'synthetic': 0.3
                    }
                }
            },
            'api': {
                'rate_limits': {
                    '/api/predict/': {'requests': 10, 'window': 60},
                    '/api/health/': {'requests': 60, 'window': 60},
                    '/api/crops/': {'requests': 30, 'window': 60},
                    'default': {'requests': 100, 'window': 60}
                },
                'timeouts': {
                    'default': 15,
                    'prediction': 30
                },
                'cors_origins': [
                    'http://localhost:5173',
                    'http://localhost:5174',
                    'https://crop-recomandation-system.vercel.app'
                ]
            },
            'security': {
                'secret_key_required': True,
                'cors_allow_all_origins': False,
                'enable_security_headers': True,
                'enable_rate_limiting': True
            },
            'monitoring': {
                'enable_request_logging': True,
                'enable_performance_metrics': True,
                'log_slow_requests': True,
                'slow_request_threshold': 5.0  # seconds
            },
            'deployment': {
                'environment': os.environ.get('DEPLOYMENT_ENV', 'development'),
                'render_external_hostname': os.environ.get('RENDER_EXTERNAL_HOSTNAME'),
                'huggingface_url': os.environ.get('HF_MODEL_URL') or os.environ.get('HF_API_URL') or 'https://shingala-crs.hf.space',
                'huggingface_token': os.environ.get('HF_TOKEN', '')
            }
        }
        
        # Load from file if exists
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                self._deep_merge(config, file_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Could not load config file {config_path}: {e}")
        
        # Override with environment variables
        self._override_from_env(config)
        
        return config
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _override_from_env(self, config: Dict):
        """Override configuration with environment variables."""
        # Database
        if os.environ.get('DATABASE_URL'):
            config['database']['url'] = os.environ.get('DATABASE_URL')
        
        # Security
        if os.environ.get('DJANGO_SECRET_KEY'):
            config['security']['secret_key'] = os.environ.get('DJANGO_SECRET_KEY')
        
        if os.environ.get('DJANGO_DEBUG'):
            config['app']['debug'] = os.environ.get('DJANGO_DEBUG').lower() == 'true'
        
        # CORS
        if os.environ.get('CORS_ALLOWED_ORIGINS'):
            config['api']['cors_origins'] = os.environ.get('CORS_ALLOWED_ORIGINS').split(',')
        
        # API Keys
        if os.environ.get('API_KEYS'):
            config['api']['keys'] = os.environ.get('API_KEYS').split(',')
        
        # Model directory
        if os.environ.get('MODEL_DIR'):
            config['ml_models']['model_dir'] = os.environ.get('MODEL_DIR')
        
        # Logging
        if os.environ.get('LOG_LEVEL'):
            config['app']['log_level'] = os.environ.get('LOG_LEVEL')
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for Django."""
        db_config = self.get('database', {})
        
        if db_config.get('url'):
            import dj_database_url
            return dj_database_url.parse(db_config['url'])
        else:
            # SQLite fallback for development
            return {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'db.sqlite3'
            }
    
    def get_middleware_config(self) -> List[str]:
        """Get middleware configuration based on settings."""
        middleware = []
        
        if self.get('monitoring.enable_request_logging'):
            middleware.append('apps.middleware.RequestLoggingMiddleware')
        
        if self.get('security.enable_security_headers'):
            middleware.append('apps.middleware.SecurityHeadersMiddleware')
        
        # Always include CORS
        middleware.append('corsheaders.middleware.CorsMiddleware')
        
        # Django middleware
        middleware.extend([
            'django.middleware.security.SecurityMiddleware',
            'whitenoise.middleware.WhiteNoiseMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ])
        
        if self.get('security.enable_rate_limiting'):
            middleware.append('apps.middleware.RateLimitMiddleware')
            middleware.append('apps.middleware.ApiKeyMiddleware')
        
        return middleware
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on debug mode and configuration."""
        if self.get('app.debug') and self.get('security.cors_allow_all_origins'):
            return []
        return self.get('api.cors_origins', [])
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Check required security settings
        if self.get('security.secret_key_required') and not self.get('security.secret_key'):
            if not os.environ.get('DJANGO_SECRET_KEY'):
                errors.append('DJANGO_SECRET_KEY environment variable is required in production')
        
        # Check database configuration
        if not self.get('database.url') and not self.get('app.debug'):
            errors.append('DATABASE_URL environment variable is required in production')
        
        # Check ML model configuration
        model_dir = self.get('ml_models.model_dir')
        if model_dir and not Path(model_dir).exists():
            errors.append(f'Model directory does not exist: {model_dir}')
        
        # Check API configuration
        hf_url = self.get('deployment.huggingface_url')
        if hf_url and not hf_url.startswith(('http://', 'https://')):
            errors.append('HuggingFace URL must start with http:// or https://')
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Return full configuration as dictionary."""
        return self._config.copy()
    
    def save(self, file_path: Optional[str] = None):
        """Save current configuration to file."""
        path = file_path or self.config_file
        try:
            with open(path, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Configuration saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get global configuration instance."""
    return config

def reload_config(config_file: Optional[str] = None):
    """Reload configuration from file."""
    global config
    config = Config(config_file)
    return config
