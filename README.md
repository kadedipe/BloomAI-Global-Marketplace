<!-- ============================================================= -->

<!--                        BLOOMAI README                          -->

<!-- ============================================================= -->

<p align="center">

# 🌸 BloomAI Global Marketplace

### *An Enterprise AI-Powered Floral & Botanical Marketplace*

AI • Deep Learning • Microservices • Docker • Kubernetes • Service Mesh • DevOps • Cloud Native

</p>

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| 📋 Trello Scrum Board | https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board |
| 📖 Documentation | docs/ |
| 🤖 AI Models | ai-services/ |
| 🐳 Docker | infrastructure/docker/ |
| ☸ Kubernetes | infrastructure/kubernetes/ |
| 🔷 Istio | infrastructure/istio/ |

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-red?logo=pytorch)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestration-326CE5?logo=kubernetes)
![Istio](https://img.shields.io/badge/Istio-Service%20Mesh-466BB0)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)
![MIT License](https://img.shields.io/badge/License-MIT-green)

</p>

---

# 🌸 Banner

> Replace the placeholder below with your own project banner.

```
docs/images/banner.png
```

---

# 📋 Project Management

BloomAI Global Marketplace follows an **Agile Scrum** development methodology. Project planning, sprint management, user stories, product backlog, task tracking, sprint reviews, and capstone deliverables are managed using a Trello Scrum Board.

### Trello Board (MSSE Capstone)

**BloomAI Global Marketplace – Product Backlog Board**

🔗 https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board

The Trello board includes:

- 📌 Product Backlog
- 📝 User Stories
- 🚀 Sprint 1 Backlog
- 🚀 Sprint 2 Backlog
- 🚀 Sprint 3 Backlog
- 🚀 Sprint 4 Backlog
- 🔄 In Progress
- 🚧 Blocked
- 👨‍💻 Code Review
- 🧪 Testing
- 📋 Sprint Review
- 📚 Documentation
- ☁️ Deployment
- ✅ Done
- 🎓 Capstone Deliverables

The board documents the complete Agile development lifecycle for the BloomAI Global Marketplace MSSE Capstone Project.

---

# 📖 Overview

BloomAI Global Marketplace is an AI-powered cloud-native marketplace connecting customers, florists, botanical gardens, universities, agricultural research institutes, nurseries, wholesalers and corporate buyers across the world.

The platform combines:

* 🌸 AI Flower Classification
* 🌿 Plant Disease Detection
* 💡 Intelligent Recommendation Engine
* 🛒 Marketplace Platform
* 💳 Multi-Payment Gateway
* 📦 Order Management
* 📈 Vendor Analytics
* ☁ Docker + Kubernetes
* 🔗 REST APIs
* 🚀 CI/CD

---

# ✨ Features

| Module                   | Description                 |
| ------------------------ | --------------------------- |
| Customer Portal          | Registration, Login, Orders |
| Vendor Marketplace       | Global Vendor Management    |
| Business Portal          | Corporate Accounts          |
| AI Flower Classification | PyTorch + VGG16             |
| Disease Detection        | Deep Learning               |
| Recommendation Engine    | Personalized Suggestions    |
| API Marketplace          | Secure API Access           |
| RFQ System               | Request for Quotation       |
| Payment Gateway          | Cards, PayPal, Mobile Money |
| Email Platform           | Notifications               |
| Dashboard                | Analytics                   |
| Cloud Deployment         | Kubernetes                  |

---

# 🏗 System Architecture

```
                    Users
                       │
      ┌────────────────────────────────┐
      │ React / Next.js Frontend       │
      └────────────────────────────────┘
                       │
                API Gateway
                       │
        ┌──────────────┼──────────────┐
        │              │              │
 Authentication   Marketplace     AI Services
        │              │              │
        │              │      Flower Classification
        │              │      Disease Detection
        │              │      Recommendation Engine
        │              │
        └──────────────┼──────────────┘
                       │
              PostgreSQL + Redis
                       │
             Docker + Kubernetes
                       │
               Istio Service Mesh
```

---

# 📸 Screenshots

Replace placeholders with actual screenshots.

| Screenshot                              | Description        |
| --------------------------------------- | ------------------ |
| `docs/images/homepage.png`              | Homepage           |
| `docs/images/customer-dashboard.png`    | Customer Dashboard |
| `docs/images/vendor-dashboard.png`      | Vendor Dashboard   |
| `docs/images/admin-dashboard.png`       | Admin Dashboard    |
| `docs/images/flower-classification.png` | AI Prediction      |
| `docs/images/disease-detection.png`     | Disease Detection  |
| `docs/images/recommendation-engine.png` | Recommendations    |
| `docs/images/api-marketplace.png`       | API Marketplace    |

Example:

```markdown
![Homepage](docs/images/homepage.png)
```

---

# 🌍 Vendor Categories

* 👤 Individuals
* 🏪 Small Businesses
* 🏢 Medium Businesses
* 🏭 Large Corporations
* 🌺 Botanical Gardens
* 🎓 Universities
* 🔬 Research Institutes
* 🌱 Conservation Organizations

---

# 🤖 Artificial Intelligence

## Flower Classification

* PyTorch
* Transfer Learning
* VGG16
* ImageNet

### Workflow

```
Image Upload

      │

      ▼

Pre-processing

      │

      ▼

VGG16 Model

      │

      ▼

Prediction

      │

      ▼

Flower Species
```

---

## Disease Detection

```
Leaf Image

      │

      ▼

CNN Model

      │

      ▼

Disease Prediction

      │

      ▼

Treatment Recommendation
```

---

## Recommendation Engine

```
Purchase History

Customer Preferences

Season

Inventory

↓

Recommendation Model

↓

Suggested Products
```

---

# ☁ Microservices

```
Frontend

↓

API Gateway

├── Authentication Service

├── Customer Service

├── Vendor Service

├── Product Service

├── Inventory Service

├── Payment Service

├── Email Service

├── Notification Service

├── AI Flower Service

├── Disease Detection

└── Recommendation Engine
```

---

# 🐳 Docker Deployment

```
Frontend Container

Backend Container

AI Container

Database Container

Redis Container

Nginx

↓

Docker Compose
```

---

# ☸ Kubernetes Deployment

```
Internet

↓

Ingress

↓

API Gateway

↓

Microservices Pods

↓

Persistent Volume

↓

PostgreSQL
```

---

# 🔷 Istio Service Mesh

```
Ingress Gateway

↓

Envoy Proxy

↓

Microservices

↓

Telemetry

↓

Grafana

Prometheus

Jaeger
```

---

# 🔄 CI/CD Workflow

```
Developer

↓

GitHub

↓

GitHub Actions

↓

Unit Tests

↓

Integration Tests

↓

Docker Build

↓

Docker Registry

↓

Kubernetes Deployment

↓

Production
```

---

# 📂 Repository Structure

```text
BloomAI-Global-Marketplace/

frontend/

backend/

ai-services/

infrastructure/

docs/

tests/

models/

datasets/

scripts/

README.md
```

---

# ⚙ Technology Stack

## Frontend

* React
* TypeScript
* Tailwind CSS

## Backend

* Python
* FastAPI

## AI

* PyTorch
* torchvision
* OpenCV

## Database

* PostgreSQL
* Redis

## DevOps

* Docker
* Kubernetes
* Istio
* GitHub Actions

---

# 🚀 Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/BloomAI-Global-Marketplace.git

cd BloomAI-Global-Marketplace

pip install -r requirements.txt
```

Download AI models

```bash
python ai-services/download_models.py
```

Run

```bash
python main.py
```

---

# 🧪 Testing

```bash
pytest
```

---

# 📊 Project Workflow

```
Requirements

↓

Agile Planning

↓

Sprint Backlogs

↓

Development

↓

Testing

↓

Docker

↓

Kubernetes

↓

Deployment

↓

Production
```

---

# 📈 Roadmap

* [x] AI Flower Classification
* [x] Vendor Marketplace
* [x] Recommendation Engine
* [x] Docker
* [x] Kubernetes
* [x] Service Mesh
* [ ] Mobile Application
* [ ] Blockchain Supply Chain
* [ ] AR Bouquet Preview
* [ ] AI Chatbot

---

# 👨‍💻 Author

**Kolapo Adedipe**

AI Engineer • Software Engineer • Cloud Engineer • DevOps Engineer

Email:

[kolapoadedipe36@gmail.com](mailto:kolapoadedipe36@gmail.com)

---

# 📄 License

MIT License

---

# ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub.