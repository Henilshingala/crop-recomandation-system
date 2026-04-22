# 🔒 Security Policy

## 📌 Supported Versions

We actively maintain and provide security updates only for the latest stable version of the Crop Recommendation System (CRS).

| Version        | Supported          |
| -------------- | ------------------ |
| 10.x (Current) | ✅                  |
| 9.x            | ⚠️ Limited support |
| < 9.0          | ❌ Not supported    |

> Users are strongly advised to upgrade to the latest version to receive security patches and improvements.

---

## 🛡️ Security Measures

The CRS project follows modern security practices across all layers:

### Backend (Django API)

* Strict input validation using serializers and validators
* Rate limiting (per-IP) to prevent abuse
* No wildcard CORS (only allowlisted origins)
* Secure environment variable handling (no secrets in code)
* HSTS and secure cookies enabled in production
* Protection against SQL injection via Django ORM

### Frontend (React)

* No exposure of sensitive API keys
* Sanitization of dynamic content (XSS prevention)
* Secure API communication via HTTPS only

### ML Engine (FastAPI)

* Input range validation to prevent malformed requests
* Controlled inference pipeline (no arbitrary execution)
* Isolated deployment (Docker container)

### Infrastructure

* API keys stored securely in environment variables
* Backend acts as proxy for third-party services (e.g., geocoding)
* No direct client access to sensitive services

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability, report it responsibly.

### 📩 How to report

* Email: **[henilshingala2462@example.com](mailto:henilshingala2462@example.com)**
* Subject: `Security Vulnerability Report - CRS`

### 📝 Include the following details:

* Description of the vulnerability
* Steps to reproduce
* Potential impact
* Screenshots or proof-of-concept (if available)

---

## ⏱️ Response Timeline

| Stage               | Expected Time       |
| ------------------- | ------------------- |
| Initial response    | Within 48 hours     |
| Investigation       | 3–7 days            |
| Fix & patch release | Depends on severity |

---

## 📢 Disclosure Policy

* Do **not** publicly disclose the vulnerability before it is fixed
* Responsible disclosure will be acknowledged
* Critical contributors may be credited (optional)

---

## ⚠️ Scope

This policy applies to:

* Backend API (`/api/*`)
* Frontend application
* ML inference engine
* Deployment configurations

Out of scope:

* Issues caused by improper local setup
* Third-party service vulnerabilities (unless misused in this project)

---

## ✅ Best Practices for Users

* Always use HTTPS endpoints
* Do not expose API keys publicly
* Keep your deployment environment variables secure
* Regularly update to the latest version

---

## 📌 Final Note

Security is a shared responsibility. While we implement strong safeguards, users and contributors must follow secure development and deployment practices.
