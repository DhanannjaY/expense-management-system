📊 Expense Management System

BCA 6th Semester – Project II
Tribhuvan University, Nepal

📌 Project Overview

The Expense Management System is a web-based application developed as part of the BCA 6th Semester Project II under Tribhuvan University.
It enables users to record, manage, and analyze personal expenses through an intuitive frontend and a secure backend powered by Django REST Framework (DRF).

The system is designed following an Iterative Development Model, allowing continuous improvement, feature enhancement, and refinement throughout multiple development cycles.

✨ Features
✅ Core Features

User Authentication – Secure login using token-based authentication

Expense Tracking – Add, update, delete, and categorize expenses

Budget Management – Define and monitor spending limits

Analytics Dashboard – Visual summaries and spending insights

Report Viewing – Structured expense data for analysis

Responsive Design – Works seamlessly on desktop and mobile devices

🚀 Advanced Features

Secure REST APIs – Token-protected endpoints using DRF

Postman API Testing – Verified CRUD operations and authentication

Interactive Charts – Line, Bar, Pie, and Doughnut charts (Chart.js)

Budget Threshold Alerts – Warning indicators for high budget usage

Mobile-Friendly UI – Built using Bootstrap 5

Modular Backend Architecture – Scalable and easy to extend

🧠 Development Methodology
Iterative Development Model

The project follows the Iterative Development Model, where the system is developed in multiple cycles. Each iteration introduces new features and improvements based on feedback and testing.

Development Iterations

Iteration 1 – UI design and authentication setup

Iteration 2 – Expense and category management

Iteration 3 – Dashboard analytics and data visualization

Iteration 4 – API testing, debugging, and refinement

Why Iterative Model?

Supports continuous improvement

Allows feedback-driven enhancements

Well-suited for medium-scale academic projects

🛠 Technologies Used
🎨 Frontend

HTML5

CSS3

Bootstrap 5.3

JavaScript (ES6+)

Chart.js

⚙ Backend

Python 3.11

Django 5.0

Django REST Framework (DRF)

SQLite / MySQL

🧪 Development & Testing Tools

Visual Studio Code

Git & GitHub

Chrome DevTools

Postman (API Testing & Validation)

🔐 Backend & API Testing (Postman)

All backend APIs were tested using Postman to ensure:

Secure token-based authentication

Proper request–response handling

Complete CRUD functionality

Robust error handling (401, 404 responses)

Authentication Flow

User logs in via /api/auth/login/

Server returns an authentication token

Token is included in request headers for protected APIs

Authorization: Token <your_token>

⚙ Installation & Setup
Prerequisites

Python 3.10 or higher

pip (Python package manager)

Web browser (Chrome recommended)

Backend Setup
git clone <repository-url>
cd expense_management_system/backend

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate    # Linux/macOS

pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

Frontend Setup
cd frontend
python -m http.server 5500

▶ Running the Project
Component	URL
Frontend	http://localhost:5500/index.html

Dashboard	http://localhost:5500/dashboard.html

Expenses Page	http://localhost:5500/expenses.html

Admin Panel	http://localhost:8000/admin

API Root	http://localhost:8000/api/
Default Login
Username: admin  
Password: admin123

📡 API Documentation
Authentication

POST /api/auth/login/

GET /api/auth/verify/

Categories

GET /api/categories/

POST /api/categories/

DELETE /api/categories/{id}/

Expenses

GET /api/expenses/

POST /api/expenses/

PATCH /api/expenses/{id}/

DELETE /api/expenses/{id}/

Budgets

GET /api/budgets/

POST /api/budgets/

PATCH /api/budgets/{id}/

DELETE /api/budgets/{id}/

🧩 System Architecture
User
  ↓
Frontend (HTML, CSS, JavaScript)
  ↓
Django REST API
  ↓
Database (SQLite / MySQL)

📘 Academic Details
👨‍🎓 Student

Name: Dhananjay Sah

Symbol No: 12232074

College: VS International College

👨‍🏫 Supervisor

Name: Santosh Pokharel

Department: Computer Application (BCA)

📌 Conclusion

The Expense Management System successfully delivers a secure, efficient, and user-friendly platform for managing personal expenses.
The integration of Django REST Framework, token-based authentication, and Postman-based API testing ensures reliability, scalability, and maintainability.

🔮 Future Enhancements

Mobile application (Android / iOS)

Expense prediction using advanced ML models

Cloud deployment

Multi-user roles and permissions

Bank API integration

Receipt scanning using OCR

📝 License

This project is developed strictly for academic purposes under the BCA curriculum of Tribhuvan University.

🙏 Acknowledgments

Tribhuvan University

Django & Django REST Framework Documentation

Bootstrap & Chart.js

Stack Overflow Community