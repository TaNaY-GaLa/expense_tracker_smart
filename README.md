Smart Expense Tracker

A full-stack web application built with Flask, Bootstrap 5, and Chart.js.

## Setup

```bash
cd expense_tracker
pip install -r requirements.txt
python app.py
```

Then open: http://localhost:5000

## Features

- Register / Login / Logout with session management
- Add **expenses** and **income** with title, category, amount, currency, date
- **7 currencies**: INR, USD, EUR, GBP, JPY, AED, SGD — all converted to INR
- **Dashboard**: Month expenses, year expenses, month income, net balance
- **Budget goal** with progress bar
- **Last 5 transactions** with edit + delete
- **Pie chart** (category breakdown) + **Line graph** (spending over time)
- **History page**: Full table with search, filter by category/type/date, sortable columns
- **Bar chart** (monthly expenses) + **Doughnut chart** (category breakdown)
- **Spending warnings**: ₹25,000 / ₹50,000 / ₹1,00,000 thresholds
- **Export to CSV**
- **About page** with API documentation

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions` | Get all transactions |
| POST | `/api/transactions` | Add transaction |
| PUT | `/api/transactions/<id>` | Edit transaction |
| DELETE | `/api/transactions/<id>` | Delete transaction |
| GET | `/api/summary` | Income/expense summary |
| PUT | `/api/budget` | Set monthly budget |
| POST | `/api/validate/transaction` | Validate data (Pydantic/FastAPI-style) |

## Project Structure

```
expense_tracker/
├── app.py               ← Flask app + API + Pydantic validation
├── requirements.txt
├── data/
│   └── db.json          ← JSON database
├── templates/
│   ├── base.html        ← Bootstrap navbar + footer
│   ├── index.html       ← Dashboard
│   ├── history.html     ← Full transaction history
│   ├── login.html       ← Login with JS validation
│   ├── register.html    ← Register with JS validation
│   └── about.html       ← About + API docs
└── static/
    ├── css/style.css    ← Custom styles
    └── js/
        ├── app.js       ← Shared utilities
        ├── dashboard.js ← Dashboard charts + logic
        └── history.js   ← History table + charts
```