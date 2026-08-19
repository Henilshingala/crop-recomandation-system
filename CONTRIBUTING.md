# 🤝 Contributing to Crop Recommendation System (CRS)

Thank you for your interest in contributing. This project follows a structured approach to maintain code quality, security, and consistency.

---

## 📌 Contribution Guidelines

### 1. Fork and Clone

* Fork the repository
* Clone your fork locally

```bash
git clone https://github.com/your-username/crop-recomandation-system.git
cd crop-recomandation-system
```

---

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:

* `feature/...` → New features
* `fix/...` → Bug fixes
* `refactor/...` → Code improvements
* `docs/...` → Documentation updates

---

### 3. Setup the Project

#### Frontend

```bash
cd Frontend
npm install
npm run dev
```

#### Backend

```bash
cd Backend/app
pip install -r requirements.txt
python manage.py runserver
```

#### ML Engine (Optional)

```bash
cd Aiml
pip install -r requirements.txt
uvicorn app:app --port 7860
```

---

## 🧪 Code Quality Standards

### General

* Follow existing project structure
* Keep functions small and readable
* Avoid unnecessary complexity

### Frontend (React + TypeScript)

* No `any` types
* Use reusable components
* Follow consistent naming

### Backend (Django)

* Use serializers for validation
* Do not expose secrets
* Keep business logic in services

### ML / Python

* Validate input ranges
* Avoid hardcoded values
* Keep inference logic clean

---

## 🔒 Security Rules (Strict)

* Never commit `.env` files
* Never expose API keys
* Validate all user inputs
* Do not bypass backend validation

Any PR violating security rules will be rejected immediately.

---

## 🧾 Commit Message Format

Use clear and structured commits:

```bash
feat: add crop filtering API
fix: resolve prediction validation bug
refactor: optimize scheme filtering logic
docs: update README with API details
```

---

## 🚀 Pull Request Process

1. Push your branch:

```bash
git push origin feature/your-feature-name
```

2. Create a Pull Request

3. Ensure:

* Code builds successfully
* No errors or warnings
* Follows project structure

4. PR must include:

* Clear description
* What problem it solves
* Screenshots (if UI change)

---

## ❌ What Will Be Rejected

* Poorly written or untested code
* Large unrelated changes in one PR
* Breaking existing functionality
* Ignoring coding standards

---

## 📊 Recommended Contributions

* Improve UI/UX
* Optimize API performance
* Add new datasets
* Improve ML model accuracy
* Enhance documentation

---

## 🧠 Final Note

This is a production-oriented project. Contributions should reflect real-world engineering practices, not experimental or incomplete work.

Maintain clarity, consistency, and quality in every contribution.
