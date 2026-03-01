# 💰 Expense Management System

> **AI-Powered Personal Finance Manager**  
> BCA 6th Semester Project II | Tribhuvan University, Nepal

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-Academic-orange.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Complete-success.svg)]()

**Developed by:** Dhananjay Sah · Aanchal Manandhar  
**College:** VS International College, Minbhawan, Kathmandu  
**Supervisor:** Mr. Santosh Pokharel  
**Program:** Bachelor of Computer Application (BCA) — Tribhuvan University  
**Duration:** 12 Weeks (December 2025 – March 2026)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [System Architecture](#-system-architecture)
- [Database Schema](#-database-schema)
- [API Documentation](#-api-documentation)
- [Machine Learning](#-machine-learning)
- [Testing](#-testing)
- [Future Enhancements](#-future-enhancements)
- [License](#-license)

---

## 🎯 Overview

The **Expense Management System (EMS)** is a comprehensive web-based application that centralizes personal financial management through intelligent expense tracking, budget monitoring, data visualization, and ML-powered expense forecasting.

Built as the capstone **Project-II** for the BCA program at Tribhuvan University, the system is designed specifically for the **Nepalese context** — supporting NPR currency and local digital payment methods including eSewa and Khalti.

### Problem Statement

Individuals — particularly students and young professionals — struggle with:
- ❌ Fragmented expense records across multiple platforms
- ❌ No real-time spending visibility or pattern awareness
- ❌ Lack of predictive insights for future financial planning
- ❌ Manual and error-prone budget tracking
- ❌ No single tool that combines tracking, analysis, and forecasting

### Our Solution

✅ **Centralized Platform** — Track all expenses in one place  
✅ **Real-time Analytics** — Interactive dashboards with Chart.js visualizations  
✅ **AI Predictions** — Multi-window Linear Regression forecasting  
✅ **Smart Budgets** — Category-specific budgets with proactive alerts  
✅ **Secure Authentication** — Token-based security with PBKDF2-SHA256  
✅ **Multi-format Reports** — PDF, CSV, and HTML exports  
✅ **Nepal-specific** — NPR currency, eSewa, Khalti, local expense categories  

---

## ✨ Key Features

### 🔐 Authentication & Security
- Secure user registration with real-time validation
- Token-based authentication (Django REST Framework)
- Password hashing: PBKDF2-SHA256
- CSRF & XSS protection
- Per-user data isolation — users cannot access each other's data

### 💸 Expense Management
- **CRUD Operations** — Add, edit, delete expenses
- **12 Categories** — Bills, Bills & Utilities, Education, Entertainment, Food, Food & Dining, Healthcare, Housing, Others, Personal Care, Shopping, Transportation
- **6 Payment Methods** — Cash, eSewa, Khalti, Credit Card, Debit Card, Net Banking
- **Advanced Filters** — Date range, category, amount, payment method
- **Real-time Search** — With debouncing for performance
- **Bulk Delete** — Select and remove multiple expenses

### 📊 Budget Management
- Category-specific budgets (Weekly / Monthly / Yearly)
- Configurable alert thresholds (50–100%, default 80%)
- Real-time budget vs. actual comparison
- Color-coded status indicators:
  - 🟢 **Safe** (< 80% used)
  - 🟡 **Warning** (80–100% used)
  - 🔴 **Over Budget** (> 100% used)

### 📈 Analytics Dashboard
- **Summary Stats** — Total expenses, transaction count, daily average
- **Interactive Charts**:
  - 📈 Line Chart — 7-day expense trend
  - 🍩 Doughnut Chart — Category distribution
  - 📊 Bar Chart — Day-of-week spending patterns
  - 📊 Bar Chart — Category-wise analysis (amount + count)

### 🤖 ML-Powered Predictions
- **Algorithm** — Multi-window Linear Regression (pure Python, no NumPy)
- **3 Time Windows** — 3-month (weight: 0.5), 6-month (weight: 0.3), 12-month (weight: 0.2)
- **Confidence Scoring** — High / Medium / Low based on R² metric
- **Trend Detection** — Increasing / Decreasing / Stable
- **Category Forecasts** — Per-category predictions
- **Monthly Forecast** — Weekly breakdown with confidence levels

### 📄 Report Generation
- **4 Templates** — Summary, Detailed, Budget Analysis, Category Breakdown
- **3 Export Formats** — PDF (print-to-PDF), CSV, HTML
- **Customizable** — Date ranges and period selection

### ⚙️ User Settings
- Profile management (name, email)
- Password change
- Currency preference (NPR / USD / EUR)
- Theme selection (Light / Dark)
- Notification preferences

---

## 🛠 Technology Stack

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| HTML5 | — | Semantic markup |
| CSS3 | — | Responsive styling |
| JavaScript | ES6+ | Client-side logic |
| Bootstrap | 5.3 | UI framework |
| Chart.js | 4.x | Data visualization |
| Font Awesome | 6.4 | Icons |

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Programming language |
| Django | 5.0 | Web framework |
| Django REST Framework | 3.14 | API development |
| SQLite | 3 | Development database |

### Development Tools
| Tool | Purpose |
|---|---|
| VS Code | Primary IDE |
| Git & GitHub | Version control |
| Postman | API testing |
| Draw.io | System diagrams |
| DB Browser for SQLite | Database inspection |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip (latest)
- Git
- Web browser (Chrome / Firefox / Edge)

### Installation

**1. Clone Repository**
```bash
git clone https://github.com/dhananjaysah46/expense-management-system.git
cd expense-management-system
```

**2. Backend Setup**
```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py makemigrations
python manage.py migrate

# Create superuser (for admin panel)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

**3. Import Sample Dataset (250 records)**
```bash
# Creates testuser + imports 250 expense records (Dec 2025 – Feb 2026)
python manage.py import_dataset --username testuser

# To re-import fresh data:
python manage.py import_dataset --username testuser --clear
```

**4. Frontend Setup**
```bash
cd frontend
python -m http.server 5500
```

**5. Access Application**
| Page | URL |
|---|---|
| Frontend | http://localhost:5500/index.html |
| Dashboard | http://localhost:5500/dashboard.html |
| Admin Panel | http://localhost:8000/admin |
| API Root | http://localhost:8000/api/ |

**Test Credentials**
```
Username: testuser
Password: testpass123
```

---

## 📁 Project Structure

```
expense_management_system/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── expense_dataset_250_clean.csv     ← sample dataset
│   ├── expense-project/
│   │   └── settings.py
│   └── expenses/
│       ├── models.py                     ← Category, Expense, Budget, UserPreference
│       ├── views.py                      ← ViewSets + API views
│       ├── serializers.py                ← DRF serializers
│       ├── urls.py                       ← URL routing
│       ├── ml_predictions.py             ← ML engine (Linear Regression)
│       ├── tests.py                      ← Unit + system tests
│       └── management/
│           └── commands/
│               └── import_dataset.py     ← CSV import command
├── frontend/
│   ├── dashboard.html
│   ├── expenses.html
│   ├── budget.html
│   ├── analytics.html
│   ├── reports.html
│   ├── settings.html
│   ├── login.html
│   ├── register.html
│   └── core.js                           ← Shared utilities, API manager, CategoryLoader
└── README.md
```

---

## 🏗 System Architecture

### Three-Tier Architecture

```
┌──────────────────────────────────────────┐
│         PRESENTATION LAYER               │
│   HTML5, CSS3, Bootstrap 5, Chart.js     │
│   • UI Components & Forms                │
│   • Client-side Validation               │
│   • Chart Rendering (Chart.js)           │
└─────────────────┬────────────────────────┘
                  │ HTTP/JSON + Token Auth
                  ↓
┌──────────────────────────────────────────┐
│           APPLICATION LAYER              │
│   Django + Django REST Framework         │
│   • RESTful API Endpoints                │
│   • Business Logic & Validation          │
│   • ML Prediction Engine                 │
│   • Report Generation                    │
└─────────────────┬────────────────────────┘
                  │ Django ORM
                  ↓
┌──────────────────────────────────────────┐
│             DATA LAYER                   │
│            SQLite Database               │
│   • Persistent Storage                   │
│   • Relational Data (5 models)           │
└──────────────────────────────────────────┘
```

---

## 🗄 Database Schema

### Models

| Model | Key Fields | Relationships |
|---|---|---|
| **User** | username, email, password (hashed) | Django built-in |
| **Category** | name, icon, color | Shared across users |
| **Expense** | title, amount, date, payment_method | → User, → Category |
| **Budget** | amount, period, alert_threshold | → User, → Category |
| **UserPreference** | currency, theme, notifications | → User (OneToOne) |

### Payment Methods Supported
`cash` · `esewa` · `khalti` · `card` · `netbanking` · `other`

### Expense Categories (12)
`Bills` · `Bills & Utilities` · `Education` · `Entertainment` · `Food` · `Food & Dining` · `Healthcare` · `Housing` · `Others` · `Personal Care` · `Shopping` · `Transportation`

---

## 📡 API Documentation

### Base URL
```
Development:  http://localhost:8000/api/
```

### Authentication
All protected endpoints require:
```http
Authorization: Token <your_token_here>
```

### Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register/` | Register new user | ❌ |
| POST | `/auth/login/` | User login, returns token | ❌ |
| POST | `/auth/logout/` | Invalidate token | ✅ |
| GET | `/auth/verify/` | Verify token validity | ✅ |
| POST | `/auth/change-password/` | Change password | ✅ |
| GET/POST | `/expenses/` | List / create expenses | ✅ |
| GET/PUT/DELETE | `/expenses/{id}/` | Retrieve / edit / delete expense | ✅ |
| GET | `/expenses/dashboard/` | Dashboard summary stats | ✅ |
| GET/POST | `/budgets/` | List / create budgets | ✅ |
| GET/PUT/DELETE | `/budgets/{id}/` | Retrieve / edit / delete budget | ✅ |
| GET | `/budgets/analysis/` | Budget vs spending analysis | ✅ |
| GET/POST | `/categories/` | List / create categories | ✅ |
| GET | `/analytics/predictions/` | ML expense predictions | ✅ |
| GET | `/analytics/monthly-forecast/` | Monthly forecast + weekly breakdown | ✅ |
| GET | `/analytics/category-predictions/` | Per-category predictions | ✅ |
| GET/PUT | `/preferences/` | User preferences | ✅ |
| GET/PUT | `/users/{id}/` | User profile update | ✅ |

### Example: Create Expense

**Request**
```http
POST /api/expenses/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json

{
    "title": "Grocery Shopping",
    "amount": "2500.00",
    "category": 1,
    "date": "2025-12-20",
    "payment_method": "esewa",
    "description": "Weekly groceries from Bhatbhateni"
}
```

**Response (201 Created)**
```json
{
    "id": 1,
    "title": "Grocery Shopping",
    "amount": "2500.00",
    "category": 1,
    "category_name": "Food",
    "date": "2025-12-20",
    "payment_method": "esewa",
    "description": "Weekly groceries from Bhatbhateni",
    "created_at": "2025-12-20T10:30:00Z"
}
```

### Example: ML Prediction Response

**Request**
```http
GET /api/analytics/predictions/?days=7
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Response (200 OK)**
```json
{
    "prediction_days": 7,
    "recommended_prediction": 24912.49,
    "confidence": "low",
    "confidence_score": 0.0821,
    "trend": "increasing",
    "algorithms": {
        "linear_regression": { "daily": 830.42, "total": 5812.91 },
        "simple_average":    { "daily": 830.42, "total": 5812.91 },
        "weighted_prediction":{ "daily": 830.42, "total": 5812.91 }
    },
    "statistics": {
        "historical_daily_average": 830.42,
        "non_zero_days": 91,
        "windows_used": 1
    },
    "window_breakdown": [
        { "window": "3-month", "days": 90, "weight": 1.0,
          "lr_daily": 830.42, "r_squared": 0.0821, "non_zero": 91 }
    ]
}
```

---

## 🤖 Machine Learning

### Algorithm: Multi-Window Linear Regression

The prediction module implements **two core algorithms** in pure Python without NumPy or Pandas:

---

#### Algorithm 1 — Linear Regression (OLS)

Finds the best-fit line through historical daily expense data using the **Ordinary Least Squares** method.

```
y = mx + b

m (slope)     = (n∑xy − ∑x∑y) / (n∑x² − (∑x)²)
b (intercept) = (∑y − m∑x) / n
```

---

#### Algorithm 2 — Multi-Window Weighted Prediction

Three independent LR models are trained on different historical windows and combined:

```
Final Prediction = (3-month × 0.5) + (6-month × 0.3) + (12-month × 0.2)
```

| Window | Days | Weight | Rationale |
|---|---|---|---|
| 3-month | 90 days | **0.5** | Most recent — highest priority |
| 6-month | 180 days | **0.3** | Medium-term pattern |
| 12-month | 365 days | **0.2** | Long-term baseline |

> **Weight normalization:** If a window has insufficient data (< 3 active days), it is excluded and remaining weights are re-normalized to always sum to 1.0.

---

#### Supporting Metric — R² (Coefficient of Determination)

Measures how well the regression line fits historical data:

```
R² = 1 − (SS_res / SS_tot)

SS_res = Σ(y_actual − y_predicted)²   ← Residual sum of squares
SS_tot = Σ(y_actual − y_mean)²        ← Total sum of squares
```

| R² Value | Confidence Level | Meaning |
|---|---|---|
| R² > 0.7 | **High** | Clear trend — reliable prediction |
| R² > 0.4 | **Medium** | Reasonable estimate |
| R² ≤ 0.4 | **Low** | Irregular data — rough estimate |

---

#### Prediction Accuracy by Data Volume

| Data Available | Windows Active | Confidence |
|---|---|---|
| < 3 active days | None | Insufficient data |
| 3 – 89 days | 3-month only | Low |
| 90 – 179 days | 3-month + 6-month | Medium |
| 180+ days | All 3 windows | High |

---

#### Why Pure Python (No NumPy)?

- ✅ **Educational value** — demonstrates deep algorithm understanding
- ✅ **Lightweight** — no heavy dependencies
- ✅ **Portable** — runs on any standard Python environment
- ✅ **Academic integrity** — shows implementation knowledge, not library usage

---

## 🧪 Testing

### Test Summary

| Test Type | Cases | Initial Failures | Final Result |
|---|---|---|---|
| Unit Testing | 14 | 4 | ✅ 14/14 Pass |
| System Testing | 12 | 3 | ✅ 12/12 Pass |
| Security Testing | 4 | 0 | ✅ 4/4 Pass |
| **Total** | **30** | **7** | **✅ 30/30 Pass** |

### Key Test Areas

**Unit Tests (14)**
- User model validation (create, duplicate, invalid email)
- Expense API (create, unauthorized access, negative amount, future date)
- Prediction algorithm (normal data, constant data, insufficient data)
- Budget model (create, duplicate, zero amount, invalid threshold)

**System Tests (12)**
- User registration and login flows
- Expense CRUD with dashboard update
- Budget alert thresholds (79% / 80% / 100%)
- Forecast generation with sufficient and insufficient data
- Unauthorized access protection

**Security Tests (4)**
- Unauthorized dashboard access → redirect to login
- API access without token → HTTP 403
- SQL injection attempt → input rejected
- Password storage → confirmed hashed (PBKDF2-SHA256)

### Performance Metrics
```
Page Load Time:     < 2 seconds   ✅
API Response Time:  < 500ms       ✅
Database Queries:   < 10 per page ✅
Chart Render Time:  < 500ms       ✅
```

---

## 🔮 Future Enhancements

1. **Mobile Application** — React Native companion app for iOS and Android
2. **Automated Transaction Import** — Bank API integration (eSewa, Khalti APIs)
3. **Advanced ML Models** — ARIMA or Prophet for seasonal pattern detection
4. **Collaborative Budgets** — Shared wallets for families or roommates
5. **Multi-Currency Support** — For international transactions
6. **Receipt Scanning** — OCR-based expense entry from photos
7. **Two-Factor Authentication** — SMS/TOTP for enhanced security
8. **Cloud Deployment** — Production deployment on AWS or Azure

---

## 📜 License

This project is developed strictly for academic purposes under the BCA curriculum of **Tribhuvan University, Nepal**.

**Academic Use Only** — Not licensed for commercial use.

---

## 🙏 Acknowledgments

- **Tribhuvan University** — Academic framework and curriculum
- **VS International College** — Institutional support and resources
- **Mr. Santosh Pokharel** — Project supervision and guidance
- **Django & DRF Communities** — Excellent documentation
- **Bootstrap & Chart.js Teams** — UI/UX and visualization frameworks

---

## 📞 Contact

**Dhananjay Sah**  
BCA 6th Semester | VS International College  
📧 dhananjay07sah@gmail.com  
🐙 [github.com/dhananjaysah46](https://github.com/dhananjaysah46)

**Aanchal Manandhar**  
BCA 6th Semester | VS International College

---

*Made with ❤️ for BCA Project II — Tribhuvan University, Nepal 🇳🇵*