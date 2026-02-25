# Crop Recommendation System V4 - Deployment Checklist

## Required Environment Variables

### Core Application
- `DEBUG=false` - Must be false in production
- `HOST=0.0.0.0` - Service bind address
- `PORT=7860` - Service port
- `WORKERS=4` - Gunicorn worker count

### Model Configuration
- `MODEL_REGISTRY_PATH=model_registry.json` - Path to model registry
- `NUTRIENTS_PATH=Nutrient.csv` - Path to nutrition data

### Security
- `SECRET_KEY=your-secret-key-here` - Must be changed in production
- `API_KEYS=api-key-1,api-key-2` - Comma-separated API keys (if required)

### Logging & Monitoring
- `LOG_LEVEL=INFO` - Logging level
- `STRUCTURED_LOGGING=true` - Enable JSON logging
- `SENTRY_DSN=https://your-sentry-dsn-here` - Optional Sentry integration

### Performance
- `MAX_REQUESTS=1000` - Max requests per worker
- `MAX_REQUESTS_JITTER=100` - Request jitter
- `TIMEOUT=120` - Request timeout in seconds

### Rate Limiting
- `RATE_LIMIT_PER_MINUTE=100` - Rate limit per minute
- `RATE_LIMIT_BURST=20` - Rate limit burst size

### Circuit Breaker
- `CIRCUIT_BREAKER_FAILURE_THRESHOLD=10` - Failure threshold
- `CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60` - Recovery timeout

## Required Ports

- **7860** - FastAPI ML Engine
- **8001** - Django Gateway (if deployed separately)
- **3000** - React Frontend (if deployed separately)

## Health Check URLs

### FastAPI ML Engine
- **Basic Health**: `GET /`
- **Detailed Health**: `GET /health`
- **Crops List**: `GET /crops`

### Django Gateway
- **API Health**: `GET /api/health`

## Pre-Deployment Validation

### 1. System Validation
```bash
cd /path/to/CRS
python scripts/validate_system.py
```

### 2. Build Docker Image
```bash
docker build -t crop-recommendation-v4:production .
```

### 3. Test Container locally
```bash
docker run --rm -p 7860:7860 --env-file environments/production.env crop-recommendation-v4:production
```

### 4. Health Check Verification
```bash
curl http://localhost:7860/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "4.0",
  "timestamp": "2024-01-01T12:00:00",
  "models": {
    "real": {"loaded": true, "crop_count": 19},
    "synthetic": {"loaded": true, "crop_count": 51},
    "both": {"loaded": true, "crop_count": 54}
  },
  "memory_usage": {
    "real_predictor_loaded": true,
    "synthetic_predictor_loaded": true,
    "both_predictor_loaded": true
  },
  "configuration": {
    "log_level": "INFO",
    "structured_logging": true,
    "workers": 4
  }
}
```

## Deployment Steps

### 1. Environment Setup
```bash
# Copy production environment
cp environments/production.env .env

# Edit .env with actual values
nano .env
```

### 2. Deploy Container
```bash
# Pull latest image
docker pull crop-recommendation-v4:production

# Stop existing container
docker stop crop-rec-v4 || true
docker rm crop-rec-v4 || true

# Start new container
docker run -d \
  --name crop-rec-v4 \
  -p 7860:7860 \
  --env-file .env \
  --restart unless-stopped \
  crop-recommendation-v4:production
```

### 3. Verify Deployment
```bash
# Check container status
docker ps | grep crop-rec-v4

# Check logs
docker logs crop-rec-v4

# Health check
curl -f http://localhost:7860/health || echo "Health check failed"
```

## Post-Deployment Verification

### 1. Test All Prediction Modes
```bash
# Real mode
curl -X POST http://localhost:7860/predict \
  -H "Content-Type: application/json" \
  -d '{
    "N": 50, "P": 30, "K": 40,
    "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
    "mode": "real", "top_n": 3
  }'

# Synthetic mode
curl -X POST http://localhost:7860/predict \
  -H "Content-Type: application/json" \
  -d '{"N": 50, "P": 30, "K": 40, "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100, "mode": "synthetic", "top_n": 3}'

# Both mode
curl -X POST http://localhost:7860/predict \
  -H "Content-Type: application/json" \
  -d '{"N": 50, "P": 30, "K": 40, "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100, "mode": "both", "top_n": 3}'
```

### 2. Verify Structured Logging
```bash
# Check logs are JSON formatted
docker logs crop-rec-v4 | tail -5 | python -m json.tool
```

### 3. Verify No PII in Logs
```bash
# Check logs for sensitive data
docker logs crop-rec-v4 | grep -i "password\|secret\|key\|token" || echo "No PII found in logs"
```

### 4. Performance Validation
```bash
# Test response time
time curl -X POST http://localhost:7860/predict \
  -H "Content-Type: application/json" \
  -d '{"N": 50, "P": 30, "K": 40, "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100, "mode": "real", "top_n": 3}'
```

## Rollback Procedure

### 1. Quick Rollback
```bash
# Stop current container
docker stop crop-rec-v4

# Start previous version
docker run -d \
  --name crop-rec-v4-rollback \
  -p 7860:7860 \
  --env-file .env \
  --restart unless-stopped \
  crop-recommendation-v4:previous

# Update load balancer to point to rollback container
```

### 2. Full Rollback
```bash
# If issues persist, rollback to known good version
docker tag crop-recommendation-v4:known-good crop-recommendation-v4:production
docker restart crop-rec-v4
```

## Monitoring & Alerting

### 1. Health Monitoring
- Monitor `/health` endpoint every 30 seconds
- Alert if status != "healthy"
- Monitor memory usage trends

### 2. Performance Monitoring
- Monitor response times (P95 < 200ms)
- Monitor error rates (> 1% triggers alert)
- Monitor request throughput

### 3. Log Monitoring
- Monitor for error logs
- Monitor for circuit breaker activations
- Monitor for rate limit hits

## Log Locations

### Container Logs
```bash
# Real-time logs
docker logs -f crop-rec-v4

# Last 100 lines
docker logs --tail 100 crop-rec-v4

# Logs since specific time
docker logs --since="2024-01-01T12:00:00" crop-rec-v4
```

### Structured Log Fields
- `event`: Event type (prediction, model_load, health_check, error)
- `mode`: Prediction mode (real, synthetic, both)
- `latency_ms`: Request latency in milliseconds
- `cache_hit`: Whether prediction was cached
- `error_type`: Type of error if applicable
- `timestamp`: ISO timestamp

## Security Verification

### 1. Container Security
```bash
# Verify non-root user
docker exec crop-rec-v4 whoami  # Should return "appuser"

# Verify no debug mode
docker exec crop-rec-v4 env | grep DEBUG  # Should be "false"
```

### 2. Network Security
```bash
# Verify only required ports exposed
docker port crop-rec-v4  # Should only show 7860
```

## Troubleshooting

### Common Issues

#### 1. Container Fails to Start
```bash
# Check logs
docker logs crop-rec-v4

# Common causes:
# - Missing environment variables
# - Invalid model registry
# - Missing model files
```

#### 2. Health Check Fails
```bash
# Check health endpoint directly
curl http://localhost:7860/health

# Common causes:
# - Model loading failures
# - Memory issues
# - Configuration errors
```

#### 3. Prediction Errors
```bash
# Test prediction manually
curl -X POST http://localhost:7860/predict \
  -H "Content-Type: application/json" \
  -d '{"N": 50, "P": 30, "K": 40, "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100, "mode": "real", "top_n": 3}'

# Common causes:
# - Invalid input data
# - Model not loaded
# - Season inference issues
```

## Maintenance

### Weekly Tasks
- Check memory usage trends
- Review error logs
- Verify performance metrics
- Update dependencies if needed

### Monthly Tasks
- Run full benchmark suite
- Review and rotate secrets
- Update model registry if needed
- Security audit

## Emergency Contacts

- **DevOps Team**: [Contact Information]
- **Development Team**: [Contact Information]
- **On-Call Engineer**: [Contact Information]

## Final Verification Checklist

- [ ] All environment variables set
- [ ] DEBUG=false in production
- [ ] SECRET_KEY changed from default
- [ ] Health endpoint responding
- [ ] All prediction modes working
- [ ] Structured logging enabled
- [ ] No PII in logs
- [ ] Container running as non-root
- [ ] Rate limiting configured
- [ ] Circuit breaker configured
- [ ] Monitoring alerts configured
- [ ] Rollback procedure tested
- [ ] Documentation updated
