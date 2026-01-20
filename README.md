📊 Expense Management System

BCA 6th Semester – Project II
Tribhuvan University, Nepal

📌 Project Overview

The Expense Management System is a web-based application developed as part of the BCA 6th Semester Project II under Tribhuvan University.
The system helps users record, manage, and analyze personal expenses using a modern frontend and a secure backend powered by Django REST Framework.

The project follows an Iterative Development Model, allowing continuous improvement and feature enhancement across development cycles.

✨ Features
Core Features

✅ User Authentication – Secure login using token-based authentication

✅ Expense Tracking – Add, update, delete, and categorize expenses

✅ Budget Management – Define and monitor spending limits

✅ Analytics Dashboard – Visual expense summaries and insights

✅ Report Viewing – Structured expense data for analysis

✅ Responsive Design – Accessible on desktop and mobile devices

Advanced Features

🔐 Secure REST APIs – Token-protected endpoints using DRF

📡 Postman API Testing – Verified CRUD operations and authentication

📊 Interactive Charts – Line, Bar, Pie, Doughnut (Chart.js)

🎯 Budget Threshold Alerts – Warning indicators for high usage

📱 Mobile-Friendly UI – Built with Bootstrap 5

🧩 Modular Backend Design – Easy to extend and scale

🧠 Development Methodology
Iterative Development Model
- The system was developed using the Iterative Model, where the application was built and refined through multiple development cycles.

Iterations:
Iteration 1 – UI design and authentication setup

Iteration 2 – Expense and category management

Iteration 3 – Dashboard analytics and charts

Iteration 4 – API testing, debugging, and refinement

Why Iterative Model?
-Supports continuous improvement
-Allows feedback-based enhancements
-Suitable for medium-scale academic projects

🛠 Technologies Used
Frontend
-HTML5
-CSS3
-Bootstrap 5.3
-JavaScript (ES6+)
-Chart.js

Backend
-Python 3.11
-Django 5.0
-Django REST Framework
-SQLite3 / MySQL

Development & Testing Tools
-Visual Studio Code
-Git & GitHub
-Chrome DevTools
-Postman (API Testing & Validation)

🔐 Backend & API Testing (Postman)
All backend APIs were tested using Postman to ensure:
-Secure token-based authentication
-Correct request–response handling
-Proper CRUD functionality
-Error handling (401, 404 responses)

Authentication Flow

User logs in via /auth/login/

Server returns authentication token

Token is included in headers for protected APIs

Authorization: Token <your_token>

⚙ Installation & Setup
Prerequisites
Python 3.10+
pip
Web browser (Chrome recommended)

Backend Setup
git clone <repository-url>
cd expense_management_system/backend

python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

Frontend Setup
cd frontend
python -m http.server 5500

▶ Running the Project

Frontend: http://localhost:5500/index.html

Dashboard: http://localhost:5500/dashboard.html

Expenses: http://localhost:5500/expenses.html

Admin Panel: http://localhost:8000/admin

API Root: http://localhost:8000/api/

Default Login
Username: admin
Password: admin123

📡 API Documentation
Authentication
POST /api/auth/login/
GET  /api/auth/verify/

Categories
GET    /api/categories/
POST   /api/categories/
DELETE /api/categories/{id}/

Expenses
GET    /api/expenses/
POST   /api/expenses/
PATCH  /api/expenses/{id}/
DELETE /api/expenses/{id}/

Budgets
GET    /api/budgets/
POST   /api/budgets/
PATCH  /api/budgets/{id}/
DELETE /api/budgets/{id}/

🧩 System Architecture
User
 ↓
Frontend (HTML, CSS, JS)
 ↓
Django REST API
 ↓
Database (SQLite/MySQL)

📘 Academic Details

Student

Name: [Dhananjay Sah]

Symbol No: [12232074]

College: [VS College]

Supervisor

Name: [Santosh Pokharel]

Department: Computer Application(BCA)

📌 Conclusion
-The Expense Management System successfully provides a secure, efficient, and user-friendly platform for managing personal expenses.
-The use of Django REST Framework, token-based authentication, and Postman testing ensures robustness and scalability.

🔮 Future Enhancements
-Mobile application (Android/iOS)
-Expense prediction using advanced ML models
-Cloud deployment
-Multi-user roles
-Bank API integration
-Receipt scanning (OCR)

📝 License
-This project is developed strictly for academic purposes under the BCA curriculum of Tribhuvan University.

🙏 Acknowledgments

-Tribhuvan University
-Django & DRF Documentation
-Bootstrap & Chart.js
-Stack Overflow Community