# Expense Tracker

A full-stack financial management web application built with Django, FastAPI, and machine learning. Designed for students and individuals who want to track, understand, and take control of their spending habits.

---

## Overview

Most expense trackers are simple ledgers. This one goes further — it analyzes spending patterns, predicts future expenses, detects anomalies, and provides AI-generated financial health scores. The backend is split into two services: a Django application handling all user data and business logic, and a FastAPI service running the machine learning pipeline independently.

---

## Features

### Core Expense Management
- Add, edit, and delete transactions with title, category, amount, date, and currency
- Supports 7 currencies (INR, USD, EUR, GBP, JPY, AED, SGD) with automatic INR conversion
- Set and track a monthly budget with a visual progress indicator
- Input validation prevents invalid entries such as future dates or empty fields

### Dashboard and Analytics
- Monthly, yearly, and all-time expense summaries with animated number counters
- Budget tracking with a real-time progress bar
- Recent transactions overview with edit and delete actions
- Category-wise pie chart and monthly spending trend chart
- AI-generated spending summary and financial health score

### Advanced Visual Insights
- GitHub-style heatmap calendar showing daily spending intensity
- Day-of-week spending pattern analysis
- Month-to-month category comparison with percentage difference
- Bar and doughnut charts across Dashboard and History pages

### Split Bills
- Split expenses among friends with equal, custom, or percentage-based division
- Track who paid and who owes what
- Settle individual shares or the entire bill at once
- Balance summary showing total owed and total you owe across all splits

### Mess Bill Tracker
- Track monthly hostel or canteen expenses
- Mark bills as paid or unpaid
- View yearly total, monthly total, unpaid count, and average bill
- Export all records to CSV

### Savings Goals
- Set financial goals with a target amount and deadline
- Track progress with an animated progress bar
- Auto-calculates required daily savings to reach the goal on time

### Blog
- Write, read, and delete posts
- All users can view posts; only the author can delete their own
- Integrated into the main application with the same design system

### User Profile
- Update email, mobile number, and language preference
- Change password securely via Django built-in authentication
- Toggle dark mode (persists across sessions via localStorage)

---

## Machine Learning Features

The FastAPI ML service provides six intelligent features:

| Feature | Model | Description |
|---|---|---|
| Category Prediction | TF-IDF + Naive Bayes | Predicts the expense category as the user types the title |
| Spending Sentiment | HuggingFace DistilBERT | Analyzes transaction history and rates financial health |
| Anomaly Detection | Isolation Forest | Flags transactions that are unusually high or low for their category |
| Expense Forecasting | Linear Regression | Predicts next month total spending based on historical trends |
| Auto Summarizer | Template-based NLG | Generates a readable summary of monthly spending behavior |
| Duplicate Detection | Fuzzy word matching | Warns the user before saving a potentially duplicate entry |

All features include fallback logic. If the ML service is offline or the model is unavailable, the application continues to function normally using rule-based alternatives.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6 |
| ML Service | FastAPI + Uvicorn |
| Database | SQLite via Django ORM |
| Authentication | Django built-in auth (hashed passwords) |
| Frontend | Bootstrap 5, Chart.js, Vanilla JS |
| ML Libraries | scikit-learn, HuggingFace Transformers, PyTorch |
| Fonts | Playfair Display, DM Sans |
| Icons | Bootstrap Icons |

---

## Project Structure

```
expense_django/
├── manage.py
├── run.py                        # Starts Django and FastAPI together
├── ml_api.py                     # FastAPI ML server (port 8001)
├── requirements.txt
│
├── expense_tracker/              # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── tracker/                      # Main Django application
│   ├── models.py                 # UserProfile, Transaction, MessBill, SavingsGoal, Split, Post
│   ├── views.py                  # All page views and API endpoints
│   ├── urls.py                   # URL routing
│   └── admin.py                  # Django admin configuration
│
├── ml/
│   └── train.py                  # Trains and saves the category prediction model
│
├── templates/
│   ├── base.html                 # Navbar, dark mode, CSRF patch, animation setup
│   ├── index.html                # Dashboard
│   ├── history.html              # Transaction history and charts
│   ├── split.html                # Split bills
│   ├── mess.html                 # Mess bill tracker
│   ├── profile.html              # User profile and savings goals
│   ├── blog_list.html            # Blog post list
│   ├── blog_detail.html          # Single blog post
│   ├── blog_create.html          # Write new post
│   ├── login.html
│   └── register.html
│
└── static/
    ├── css/
    │   ├── style.css             # Main stylesheet (brown/cream theme)
    │   └── animations.css        # All animation keyframes and transitions
    ├── js/
    │   ├── app.js                # Shared utilities, transaction modal
    │   ├── dashboard.js          # Dashboard charts and data
    │   ├── history.js            # History table, filters, charts
    │   ├── heatmap.js            # Heatmap calendar and day-of-week chart
    │   ├── ml.js                 # FastAPI ML integration
    │   ├── profile.js            # Profile form and savings goals
    │   └── animations.js         # Counter, toast, scroll reveal, skeleton
    └── images/                   # Category icons
```

---

## Getting Started

### Prerequisites
- Python 3.11 or 3.12 (recommended)
- pip

### Installation

```bash
# 1. Navigate to the project folder
cd expense_django

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Create an admin account (one time only)
python manage.py createsuperuser

# 5. Start the application
python run.py
```

### Access Points

| URL | Description |
|---|---|
| http://localhost:5000 | Main application |
| http://localhost:5000/admin | Django admin panel |
| http://localhost:8001/docs | FastAPI ML API documentation |

---

## API Reference

### Transactions

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/transactions/` | List all transactions |
| POST | `/api/transactions/` | Add a new transaction |
| PUT | `/api/transactions/<id>/` | Edit a transaction |
| DELETE | `/api/transactions/<id>/` | Delete a transaction |
| GET | `/api/summary/` | Total, count, and budget |
| GET | `/api/analytics/` | Monthly, category, and day-of-week breakdown |
| PUT | `/api/budget/` | Update monthly budget |

### Other Resources

| Method | Endpoint | Description |
|---|---|---|
| GET, POST | `/api/splits/` | List and create splits |
| POST | `/api/splits/<id>/settle/` | Settle one person |
| POST | `/api/splits/<id>/settle-all/` | Settle entire bill |
| GET, POST | `/api/mess/` | List and add mess bills |
| PUT, DELETE | `/api/mess/<id>/` | Update or delete a mess bill |
| GET, POST | `/api/savings-goals/` | List and create savings goals |
| PUT, DELETE | `/api/savings-goals/<id>/` | Update or delete a goal |
| PUT | `/api/profile/` | Update user profile |

### ML Endpoints (port 8001)

| Endpoint | Description |
|---|---|
| POST `/ml/predict-category` | Predict category from title |
| POST `/ml/sentiment` | Analyze spending health |
| POST `/ml/anomaly` | Detect unusual transactions |
| POST `/ml/forecast` | Forecast next month spending |
| POST `/ml/summarize` | Generate spending summary |
| POST `/ml/duplicate-check` | Check for duplicate entries |

---

## Database Models

| Model | Key Fields |
|---|---|
| UserProfile | budget, mobile, language, dark_mode |
| Transaction | title, amount, category, date, currency, amount_inr |
| MessBill | month, amount, paid, note |
| SavingsGoal | title, target, saved, deadline |
| Split | title, total, paid_by, friends, shares, settlements |
| Post | title, content, author, created_at |

---

## Django Admin

The admin panel at `/admin` gives full visibility and control over all application data. After creating a superuser, you can view and manage transactions, users, mess bills, savings goals, splits, and blog posts without writing any code or SQL.

---

## Notes

- The ML category model is trained automatically on first run if no saved model is found
- The DistilBERT sentiment model downloads approximately 250MB on first use and is cached locally after that
- All API endpoints require authentication; unauthenticated requests return 401
- Dark mode preference is stored in the browser localStorage and persists across sessions
- The application uses Django CSRF protection; all fetch requests include the CSRF token automatically

---

## Possible Improvements

- Replace SQLite with PostgreSQL for production use
- Add JWT-based API authentication for external client access
- Deploy to a cloud platform such as Railway or Render
- Migrate the frontend to React for better state management
- Add receipt scanning via OCR for automatic expense entry
- Implement email notifications for budget threshold alerts
- Add PDF report generation for monthly expense summaries

---
