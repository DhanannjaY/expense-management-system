# 💰 Expense Management System (EMS)

> **AI-Powered Personal Finance Manager**  
> BCA 6th Semester Project II | Tribhuvan University, Nepal

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-Academic-orange.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Complete-success.svg)]()

**Developed by:** Dhananjay Sah  
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

The **Expense Management System (EMS)** is a full-stack personal finance web application that centralizes expense tracking, category budgeting, savings goal milestones, interactive data visualization, and ML-powered spending forecasts.

Built as the capstone **Project-II** for the BCA program at Tribhuvan University, the system is tailored for the **Nepalese context** — defaulting to **NPR (`Rs.`)** currency and local digital wallets (**eSewa**, **Khalti**) while also supporting international currencies (**USD**, **EUR**, **INR**, **GBP**).

### Problem Statement

Individuals — particularly students and young professionals — struggle with:

- ❌ Fragmented expense records across cash, mobile wallets, and bank cards
- ❌ No real-time spending visibility, tagging, or pattern awareness
- ❌ Lack of predictive insights for future financial planning
- ❌ Manual and error-prone budget and savings goal tracking
- ❌ No single lightweight tool combining tracking, analysis, and forecasting

### Our Solution

- ✅ **Centralized Ledger** — Track expenses with tags, receipt notes, and recurring schedules
- ✅ **Real-Time Analytics** — Interactive Chart.js dashboards and automated spending insights
- ✅ **AI Forecasting** — Multi-window Ordinary Least Squares (OLS) Linear Regression
- ✅ **Smart Budgets** — Category-specific budgets with configurable alert thresholds
- ✅ **Savings Goals** — Milestone tracking with incremental deposits and progress bars
- ✅ **Portable Reports** — CSV, Excel (`.xls`), JSON, and print-ready PDF exports
- ✅ **Nepal-Ready + Global** — NPR (`Rs.`), eSewa, Khalti, plus USD, EUR, INR, and GBP

---

## ✨ Key Features

### 🔐 Authentication & Security

- User registration and login with client- and server-side validation
- Token-based authentication via Django REST Framework (`Authorization: Token <key>`)
- Password hashing using Django's **PBKDF2-SHA256**
- Strict per-user data isolation across expenses, budgets, tags, and savings goals
- Password-verified account deletion (`DELETE /api/users/{id}/`)

### 💸 Expense Management

- **Full CRUD & Bulk Actions** — Add, edit, delete, and bulk-delete transactions
- **Custom Tags & Receipt Notes** — Organize transactions with user-scoped `#tags`, locations, and receipt notes
- **Recurring Expense Automation** — Schedule daily, weekly, monthly, or yearly expenses that materialize automatically when due
- **12 Default Categories** — Bills, Bills & Utilities, Education, Entertainment, Food, Food & Dining, Healthcare, Housing, Others, Personal Care, Shopping, Transportation
- **6 Payment Channels** — Cash, eSewa, Khalti, Credit Card, Debit Card, Net Banking
- **Advanced Filtering** — Filter by period, custom date range, category, tag, payment method, and debounced search

### 📊 Budget Management

- Category-specific budgets (**Weekly / Monthly / Yearly**)
- Configurable alert thresholds (**50%–100%**, default **80%**)
- Real-time budget vs. actual spending analysis with status indicators:
  - 🟢 **On Track** (`< threshold`)
  - 🟡 **Near Limit** (`≥ threshold` and `≤ 100%`)
  - 🔴 **Over Budget** (`> 100%`)

### 🎯 Savings Goals

- Create dedicated savings targets with optional target deadlines and notes
- One-click **Add Funds** deposits with automatic completion status updates
- Visual progress bars, remaining balance, and days-remaining countdowns

### 📈 Analytics & AI Forecasting

- **Interactive Charts (Chart.js 4)**:
  - 📈 Spending Timeline (daily trend)
  - 📊 Spending by Day of Week
  - 📊 Horizontal Category Distribution
  - 🍩 Payment Method Breakdown
- **Multi-Window Linear Regression (Pure Python, No NumPy)**:
  - Combines **3-month** (weight `0.5`), **6-month** (weight `0.3`), and **12-month** (weight `0.2`) windows
  - Computes **R² confidence scores**, min–max confidence intervals, and trend direction (`increasing`, `decreasing`, `stable`)
  - Supports 14-day, 30-day, and 90-day forecast horizons plus per-category predictions

### 📄 Reports & Settings

- **Report Exports** — Period and category-filtered reports exportable to **CSV**, **Excel (`.xls`)**, **JSON**, and **Print / PDF**
- **Full Account Backup** — One-click JSON export of all expenses, budgets, tags, and savings goals
- **Personalization** — Live currency switching (**NPR**, **USD**, **EUR**, **INR**, **GBP**) and theme switching (**Light**, **Dark**, **System**)

---

## 🛠 Technology Stack

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| HTML5 | — | Semantic multi-page architecture (`index`, `dashboard`, `expenses`, `budget`, `savings`, `analytics`, `reports`, `settings`) |
| CSS3 | — | Custom design system (`assets/css/main.css`) with Light/Dark/System theme tokens |
| JavaScript | ES6+ | Modular `AppCore` (`core.js`) with API caching, request deduplication, and auth guards |
| Chart.js | 4.4 | Interactive line, bar, and doughnut charts |
| Google Fonts | — | `DM Sans` (UI typography) & `DM Mono` (tabular financial figures) |
| Font Awesome | 6.4 | Vector iconography |

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core runtime & pure-Python ML engine |
| Django | 5.0 | Web framework & ORM |
| Django REST Framework | 3.14 | RESTful API & token authentication |
| django-cors-headers | 4.x | Cross-origin frontend/backend communication |
| SQLite | 3 | Relational database |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- `pip` & Git
- Modern web browser (Chrome / Firefox / Edge)

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

# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Optional: create admin superuser
python manage.py createsuperuser

# Start Django API server
python manage.py runserver
```

**3. Import Sample Dataset (250 Records)**

```bash
# Creates testuser + imports 250 sample expense records
python manage.py import_dataset --username testuser

# To reset and re-import fresh data:
python manage.py import_dataset --username testuser --clear
```

**4. Frontend Setup**

```bash
cd ../frontend
python -m http.server 5500
```

**5. Access Application**

| Interface | URL |
|---|---|
| Landing Page | http://localhost:5500/index.html |
| Dashboard | http://localhost:5500/dashboard.html |
| Django Admin | http://localhost:8000/admin/ |
| REST API Root | http://localhost:8000/api/ |

**Demo Credentials**

- **Username:** `testuser`
- **Password:** `testpass123`

---

## 📁 Project Structure

```text
expense-management-system/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── expense_dataset_250_clean.csv     ← Sample dataset
│   ├── expense_project/
│   │   └── settings.py                   ← Django & DRF settings
│   └── expenses/
│       ├── models.py                     ← Category, Tag, Expense, Budget, SavingsGoal, UserPreference
│       ├── serializers.py                ← DRF serializers & validation
│       ├── views.py                      ← ViewSets, analytics, auth & recurring logic
│       ├── urls.py                       ← API route definitions
│       ├── ml_predictions.py             ← Multi-window OLS Linear Regression engine
│       ├── tests.py                      ← Automated unit, system & security test suite
│       └── management/
│           └── commands/
│               └── import_dataset.py     ← CSV dataset importer
├── frontend/
│   ├── index.html                        ← Landing page with live interactive preview
│   ├── login.html                        ← User sign-in
│   ├── register.html                     ← User registration
│   ├── dashboard.html                    ← Main overview, KPIs & quick-add expense
│   ├── expenses.html                     ← Full ledger, tags, filters & bulk delete
│   ├── budget.html                       ← Category budgets & threshold progress
│   ├── savings.html                      ← Savings goals & deposit tracker
│   ├── analytics.html                    ← Charts, smart insights & AI forecast
│   ├── reports.html                      ← Custom report builder & CSV/Excel/JSON/PDF export
│   ├── settings.html                     ← Profile, currency, theme, password & backup
│   ├── core.js                           ← AuthManager, APIManager, CacheManager, ThemeManager & Utils
│   └── assets/
│       └── css/
│           └── main.css                  ← EMS design tokens, responsive layout & dark mode
└── README.md
```

---

## 🏗 System Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│   HTML5, Custom CSS Design System, ES6+, Chart.js 4      │
│   • Responsive Sidebar & Mobile Drawer                   │
│   • Client-Side Caching & Request Deduplication          │
│   • Dynamic Currency & Theme Management                  │
└────────────────────────────┬─────────────────────────────┘
                             │ HTTP / JSON + Token Auth
                             ↓
┌──────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                      │
│   Django 5 + Django REST Framework                       │
│   • ViewSets, Filtering & Bulk Operations                │
│   • Automatic Recurring Expense Materialization          │
│   • Multi-Window OLS ML Prediction Engine                │
└────────────────────────────┬─────────────────────────────┘
                             │ Django ORM
                             ↓
┌──────────────────────────────────────────────────────────┐
│                      DATA LAYER                          │
│                   SQLite3 Database                       │
│   • 6 Relational Models with Per-User Isolation          │
└──────────────────────────────────────────────────────────┘
```

---

## 🗄 Database Schema

| Model | Key Fields | Relationships |
|---|---|---|
| **User** | `username`, `email`, `first_name`, `last_name`, `password` | Django built-in |
| **Category** | `name`, `icon`, `color`, `description` | Shared across users |
| **Tag** | `name`, `color` | → User (unique per user) |
| **Expense** | `title`, `amount`, `date`, `payment_method`, `location`, `receipt_note`, `is_recurring`, `recurring_frequency`, `next_recurring_date` | → User, → Category, ↔ Tag (M2M) |
| **Budget** | `amount`, `period`, `alert_threshold`, `is_active`, `notes` | → User, → Category |
| **SavingsGoal** | `title`, `target_amount`, `current_amount`, `target_date`, `status`, `notes` | → User |
| **UserPreference** | `currency`, `theme`, `enable_budget_alerts`, `enable_notifications` | → User (OneToOne) |

**Supported Payment Methods**

`cash` · `esewa` · `khalti` · `card` · `netbanking` · `other`

**Supported Currencies**

`NPR (Rs.)` · `USD ($)` · `EUR (€)` · `INR (₹)` · `GBP (£)`

---

## 📡 API Documentation

### Base URL & Authentication

```http
Base URL: http://localhost:8000/api/
Authorization: Token <your_token_here>
```

### Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register/` | Register a new user and return auth token | ❌ |
| POST | `/auth/login/` | Authenticate user and return token + profile | ❌ |
| POST | `/auth/logout/` | Invalidate current auth token | ✅ |
| GET | `/auth/verify/` | Verify token validity and fetch current user | ✅ |
| POST | `/auth/change-password/` | Change password and rotate token | ✅ |
| GET/POST | `/expenses/` | List (filtered/paginated) or create expenses | ✅ |
| GET/PUT/PATCH/DELETE | `/expenses/{id}/` | Retrieve, update, or delete an expense | ✅ |
| POST | `/expenses/bulk-delete/` | Delete multiple expenses by ID list | ✅ |
| GET | `/expenses/dashboard/` | Dashboard KPIs, trends, and category totals | ✅ |
| GET/POST | `/budgets/` | List or create category budgets | ✅ |
| GET/PUT/PATCH/DELETE | `/budgets/{id}/` | Retrieve, update, or delete a budget | ✅ |
| GET | `/budgets/analysis/` | Real-time budget vs. actual spending breakdown | ✅ |
| GET/POST | `/savings-goals/` | List or create savings goals | ✅ |
| GET/PUT/PATCH/DELETE | `/savings-goals/{id}/` | Retrieve, update, or delete a savings goal | ✅ |
| POST | `/savings-goals/{id}/add_funds/` | Deposit funds into a savings goal | ✅ |
| GET/POST | `/categories/` | List or create expense categories | ✅ |
| GET/POST/DELETE | `/tags/` | List, create, or delete user tags | ✅ |
| GET | `/analytics/overview/` | Period summary, weekly pattern & payment breakdown | ✅ |
| GET | `/analytics/predictions/` | Multi-window ML expense forecast | ✅ |
| GET | `/analytics/monthly-forecast/` | Monthly forecast with weekly breakdown | ✅ |
| GET | `/analytics/category-predictions/` | Per-category spending predictions | ✅ |
| GET/POST/PUT | `/preferences/` | Retrieve or update user currency & theme preferences | ✅ |
| GET/PATCH/DELETE | `/users/{id}/` | Update profile or permanently delete account | ✅ |

---

## 🤖 Machine Learning

### Multi-Window Linear Regression (Pure Python)

The forecasting engine (`backend/expenses/ml_predictions.py`) uses Ordinary Least Squares (OLS) Linear Regression implemented purely in Python's standard library:

```text
y = mx + b

m (slope)     = (n∑xy − ∑x∑y) / (n∑x² − (∑x)²)
b (intercept) = (∑y − m∑x) / n
```

Three independent models are trained across rolling historical windows and combined using normalized weights:

| Window | Days | Default Weight | Purpose |
|---|---|---|---|
| 3-month | 90 days | `0.5` | Captures recent spending shifts |
| 6-month | 180 days | `0.3` | Smooths medium-term variance |
| 12-month | 365 days | `0.2` | Anchors long-term baseline habits |

Confidence is evaluated using the **Coefficient of Determination (R²)**:

- **R² > 0.7** → High confidence
- **R² > 0.4** → Medium confidence
- **R² ≤ 0.4** → Low confidence

---

## 🧪 Testing

Run the full automated Django test suite covering authentication, expense CRUD, tags, recurring expenses, budget thresholds, savings goals, ML forecasting, and security isolation:

```bash
cd backend
python manage.py test expenses -v 2
```

### Coverage Areas

- **Unit Tests:** Model constraints, currency formatting, serializer validation, and OLS edge cases (constant series, insufficient data)
- **System Tests:** Registration/login token lifecycle, recurring expense generation, budget threshold status transitions (safe → warning → over), savings deposits, and bulk deletion
- **Security Tests:** Cross-user isolation (404/403 on unauthorized access), password-verified account deletion, and PBKDF2-SHA256 password hashing

---

## 🔮 Future Enhancements

- **Mobile Companion App** — React Native / Flutter client for iOS and Android
- **Automated Wallet Sync** — Direct statement import / webhook integration for eSewa, Khalti, and ConnectIPS
- **Seasonal Time-Series Models** — SARIMA / Prophet forecasting for festival seasons (Dashain, Tihar)
- **Shared Family Wallets** — Multi-user household budgets with role-based permissions
- **OCR Receipt Scanning** — Automatic merchant, date, and amount extraction from receipt photos
- **Two-Factor Authentication (2FA)** — TOTP authenticator app support
- **Cloud Deployment** — Dockerized deployment with PostgreSQL and HTTPS

---

## 📜 License

Developed strictly for academic evaluation under the **Bachelor of Computer Application (BCA)** curriculum of **Tribhuvan University, Nepal**.

---

## 🙏 Acknowledgments

- **Tribhuvan University** — Academic curriculum and evaluation framework
- **VS International College** — Institutional support and lab resources
- **Mr. Santosh Pokharel** — Project supervision and guidance
- **Django & Django REST Framework Communities** — Documentation and ecosystem tools

---

## 📞 Contact

**Dhananjay Sah**

BCA 6th Semester | VS International College

- 📧 [dhananjay07sah@gmail.com](mailto:dhananjay07sah@gmail.com)
- 🐙 [github.com/dhananjaysah46](https://github.com/DhanannjaY)

---

Made with ❤️ for BCA Project II — Tribhuvan University, Nepal
