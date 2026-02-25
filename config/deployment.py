"""
Deployment Configuration and Validation
=======================================
Provides deployment-specific configurations and validation checks.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import subprocess
import json

logger = logging.getLogger(__name__)

class DeploymentValidator:
    """Validates deployment configuration and environment."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate the deployment environment."""
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        
        # Check Python version
        self._check_python_version()
        
        # Check required environment variables
        self._check_environment_variables()
        
        # Check file permissions
        self._check_file_permissions()
        
        # Check dependencies
        self._check_dependencies()
        
        # Check network connectivity
        self._check_network_connectivity()
        
        # Check ML models
        self._check_ml_models()
        
        return {
            'status': 'valid' if not self.errors else 'invalid',
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }
    
    def _check_python_version(self):
        """Check Python version compatibility."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.errors.append(f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
        else:
            self.info.append(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    def _check_environment_variables(self):
        """Check required environment variables."""
        required_vars = {
            'production': ['DJANGO_SECRET_KEY', 'DATABASE_URL'],
            'staging': ['DJANGO_SECRET_KEY'],
            'development': []
        }
        
        env = os.environ.get('DEPLOYMENT_ENV', 'development')
        required = required_vars.get(env, [])
        
        for var in required:
            if not os.environ.get(var):
                self.errors.append(f"Required environment variable missing: {var}")
        
        # Check optional but recommended variables
        recommended_vars = ['HF_MODEL_URL', 'CORS_ALLOWED_ORIGINS']
        for var in recommended_vars:
            if os.environ.get(var):
                self.info.append(f"Environment variable set: {var}")
            else:
                self.warnings.append(f"Recommended environment variable missing: {var}")
    
    def _check_file_permissions(self):
        """Check file and directory permissions."""
        # Check writable directories
        writable_dirs = ['/tmp', 'logs', 'media']
        for dir_path in writable_dirs:
            path = Path(dir_path)
            if path.exists():
                if os.access(path, os.W_OK):
                    self.info.append(f"Directory is writable: {dir_path}")
                else:
                    self.errors.append(f"Directory is not writable: {dir_path}")
            else:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.info.append(f"Created directory: {dir_path}")
                except Exception as e:
                    self.errors.append(f"Cannot create directory {dir_path}: {e}")
    
    def _check_dependencies(self):
        """Check if required dependencies are installed."""
        required_packages = [
            'django', 'djangorestframework', 'corsheaders',
            'whitenoise', 'dj-database-url', 'pandas', 'numpy',
            'scikit-learn', 'joblib'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.info.append(f"Package available: {package}")
            except ImportError:
                self.errors.append(f"Required package missing: {package}")
        
        # Check optional packages
        optional_packages = ['xgboost', 'lightgbm', 'imbalanced-learn']
        for package in optional_packages:
            try:
                __import__(package)
                self.info.append(f"Optional package available: {package}")
            except ImportError:
                self.warnings.append(f"Optional package missing: {package}")
    
    def _check_network_connectivity(self):
        """Check network connectivity to external services."""
        import urllib.request
        import urllib.error
        
        # Check HuggingFace connectivity
        hf_url = os.environ.get('HF_MODEL_URL', 'https://shingala-crs.hf.space')
        try:
            response = urllib.request.urlopen(f"{hf_url}/health", timeout=10)
            if response.status == 200:
                self.info.append(f"HuggingFace service reachable: {hf_url}")
            else:
                self.warnings.append(f"HuggingFace service returned status {response.status}")
        except Exception as e:
            self.warnings.append(f"Cannot reach HuggingFace service: {e}")
    
    def _check_ml_models(self):
        """Check if ML model files exist and are accessible."""
        model_dir = Path(os.environ.get('MODEL_DIR', '.'))
        
        required_models = [
            'stacked_ensemble_v3.joblib',
            'label_encoder_v3.joblib',
            'stacked_v3_config.joblib'
        ]
        
        for model_file in required_models:
            model_path = model_dir / model_file
            if model_path.exists():
                try:
                    # Try to load the model
                    import joblib
                    joblib.load(model_path)
                    self.info.append(f"Model file accessible: {model_file}")
                except Exception as e:
                    self.errors.append(f"Cannot load model {model_file}: {e}")
            else:
                self.warnings.append(f"Model file missing: {model_file}")

class DeploymentConfig:
    """Deployment-specific configuration management."""
    
    def __init__(self):
        self.environment = os.environ.get('DEPLOYMENT_ENV', 'development')
        self.config = self._get_deployment_config()
    
    def _get_deployment_config(self) -> Dict[str, Any]:
        """Get configuration based on deployment environment."""
        configs = {
            'development': {
                'debug': True,
                'log_level': 'DEBUG',
                'database': {
                    'engine': 'sqlite',
                    'name': 'db.sqlite3'
                },
                'security': {
                    'secret_key_required': False,
                    'cors_allow_all_origins': True,
                    'enable_https': False
                },
                'monitoring': {
                    'enable_metrics': True,
                    'log_slow_requests': True,
                    'slow_request_threshold': 2.0
                },
                'ml': {
                    'load_models_on_startup': True,
                    'enable_model_validation': True
                }
            },
            'staging': {
                'debug': False,
                'log_level': 'INFO',
                'database': {
                    'engine': 'postgresql',
                    'pool_size': 5,
                    'max_overflow': 10
                },
                'security': {
                    'secret_key_required': True,
                    'cors_allow_all_origins': False,
                    'enable_https': True
                },
                'monitoring': {
                    'enable_metrics': True,
                    'log_slow_requests': True,
                    'slow_request_threshold': 3.0
                },
                'ml': {
                    'load_models_on_startup': True,
                    'enable_model_validation': True
                }
            },
            'production': {
                'debug': False,
                'log_level': 'WARNING',
                'database': {
                    'engine': 'postgresql',
                    'pool_size': 20,
                    'max_overflow': 40
                },
                'security': {
                    'secret_key_required': True,
                    'cors_allow_all_origins': False,
                    'enable_https': True
                },
                'monitoring': {
                    'enable_metrics': True,
                    'log_slow_requests': True,
                    'slow_request_threshold': 1.0
                },
                'ml': {
                    'load_models_on_startup': True,
                    'enable_model_validation': True
                }
            }
        }
        
        return configs.get(self.environment, configs['development'])
    
    def get_django_settings(self) -> Dict[str, Any]:
        """Get Django-specific settings."""
        settings = {}
        
        # Basic settings
        settings['DEBUG'] = self.config['debug']
        settings['SECRET_KEY'] = os.environ.get('DJANGO_SECRET_KEY')
        
        # Database settings
        if self.environment == 'development':
            settings['DATABASES'] = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': 'db.sqlite3'
                }
            }
        else:
            import dj_database_url
            settings['DATABASES'] = {
                'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
            }
        
        # Security settings
        if not self.config['security']['enable_https']:
            settings['SECURE_SSL_REDIRECT'] = False
            settings['SESSION_COOKIE_SECURE'] = False
            settings['CSRF_COOKIE_SECURE'] = False
        else:
            settings['SECURE_SSL_REDIRECT'] = True
            settings['SESSION_COOKIE_SECURE'] = True
            settings['CSRF_COOKIE_SECURE'] = True
            settings['SECURE_HSTS_SECONDS'] = 31536000
            settings['SECURE_HSTS_INCLUDE_SUBDOMAINS'] = True
            settings['SECURE_HSTS_PRELOAD'] = True
        
        # CORS settings
        if self.config['security']['cors_allow_all_origins']:
            settings['CORS_ALLOW_ALL_ORIGINS'] = True
        else:
            origins = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
            settings['CORS_ALLOWED_ORIGINS'] = [o.strip() for o in origins if o.strip()]
        
        # Logging settings
        settings['LOGGING'] = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '{levelname} {asctime} {module} {message}',
                    'style': '{',
                },
                'json': {
                    'format': '{"level": "{levelname}", "time": "{asctime}", "module": "{module}", "message": "{message}"}',
                    'style': '{',
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'json' if self.environment != 'development' else 'verbose',
                },
            },
            'root': {
                'handlers': ['console'],
                'level': self.config['log_level'],
            },
        }
        
        return settings
    
    def generate_dockerfile(self) -> str:
        """Generate Dockerfile for deployment."""
        dockerfile = f"""
# Crop Recommendation System - {self.environment.title()} Deployment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEPLOYMENT_ENV={self.environment}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p logs media

# Set permissions
RUN chmod +x scripts/*.sh 2>/dev/null || true

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
"""
        return dockerfile.strip()
    
    def generate_render_yaml(self) -> str:
        """Generate render.yaml for Render deployment."""
        yaml = f"""
services:
  # Django Backend
  - type: web
    name: crop-recommendation-backend
    env: {self.environment}
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python manage.py runserver 0.0.0.0:8000
    envVars:
      - key: DEPLOYMENT_ENV
        value: {self.environment}
      - key: DJANGO_SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: crop-recommendation-db
          property: connectionString
      - key: HF_MODEL_URL
        value: https://shingala-crs.hf.space

databases:
  - name: crop-recommendation-db
    databaseName: crop_recommendations
    user: crop_user
"""
        return yaml.strip()

def validate_deployment() -> Dict[str, Any]:
    """Run full deployment validation."""
    validator = DeploymentValidator()
    return validator.validate_environment()

def get_deployment_config() -> DeploymentConfig:
    """Get deployment configuration."""
    return DeploymentConfig()
