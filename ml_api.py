"""
FastAPI ML Server — Port 8000
All 6 ML features for Expense Tracker
Run via: python run.py (starts both servers)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pickle, os
from datetime import datetime

# ── HuggingFace DistilBERT (lazy-loaded on first call) ───────
_sentiment_pipeline = None
def get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        try:
            from transformers import pipeline
            print("⏳ Loading DistilBERT sentiment model (~250MB, first run only)...")
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                truncation=True, max_length=512
            )
            print("✅ DistilBERT loaded!")
        except Exception as e:
            print(f"⚠️  DistilBERT unavailable: {e} — using rule-based fallback")
            _sentiment_pipeline = "unavailable"
    return _sentiment_pipeline

app = FastAPI(title="Expense Tracker ML API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "ml", "category_model.pkl")

model_data = None

def load_model():
    global model_data
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                model_data = pickle.load(f)
            print("✅ ML model loaded successfully")
        except Exception as e:
            print(f"⚠️  Could not load model: {e} — rule-based fallback active")
    else:
        print("ℹ️  No trained model found — rule-based fallback active (run ml/train.py to train)")

load_model()

# ── Schemas ───────────────────────────────────────────────────
class TitleIn(BaseModel):
    title: str

class TransactionIn(BaseModel):
    title: str
    amount: float
    category: str
    date: str

class TransactionsIn(BaseModel):
    transactions: List[TransactionIn]

class SentimentIn(BaseModel):
    transactions: List[TransactionIn]
    budget: Optional[float] = 50000

class ForecastIn(BaseModel):
    transactions: List[TransactionIn]

class DuplicateIn(BaseModel):
    transactions: List[TransactionIn]
    new_title: str
    new_amount: float

# ── Health check ──────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Expense Tracker ML API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model_data is not None}

# ── 1. Category Predictor ─────────────────────────────────────
@app.post("/ml/predict-category")
def predict_category(data: TitleIn):
    title = data.title.lower().strip()

    if model_data:
        try:
            vec = model_data["vectorizer"].transform([title])
            probs = model_data["classifier"].predict_proba(vec)[0]
            best_idx = probs.argmax()
            confidence = round(float(probs[best_idx]) * 100, 1)
            category = model_data["classes"][best_idx]
            if confidence >= 35:
                return {"category": category, "confidence": confidence, "source": "ml"}
        except Exception as e:
            print(f"ML predict error: {e}")

    rules = {
        "Food":          ["food","lunch","dinner","breakfast","snack","coffee","tea","restaurant","cafe","pizza","burger","biryani","swiggy","zomato","mess","canteen","eat","meal","grocery","vegetable","fruit","milk","bread","rice","dal"],
        "Travel":        ["travel","trip","flight","train","bus","cab","uber","ola","auto","petrol","fuel","hotel","hostel","airbnb","ticket","tour","metro","rapido","toll"],
        "Clothing":      ["cloth","shirt","pant","dress","shoes","jeans","jacket","saree","kurta","top","fashion","myntra","wear","outfit"],
        "Entertainment": ["movie","netflix","spotify","game","concert","show","party","club","outing","fun","prime","hotstar","youtube premium","gaming"],
        "Books":         ["book","textbook","notes","stationery","pen","pencil","notebook","course","udemy","exam","fees","college","study","library","kindle"],
        "Health":        ["doctor","medicine","pharmacy","hospital","gym","fitness","yoga","medical","health","clinic","test","scan","tablet","protein"],
    }
    for cat, keywords in rules.items():
        if any(k in title for k in keywords):
            return {"category": cat, "confidence": 72.0, "source": "rules"}

    return {"category": "Other", "confidence": 40.0, "source": "rules"}


# ── 2. Sentiment / Spending Health (HuggingFace DistilBERT) ──
@app.post("/ml/sentiment")
def analyze_sentiment(data: SentimentIn):
    txns = data.transactions
    budget = data.budget or 50000

    if not txns:
        return {"score": 50, "label": "Neutral", "emoji": "😐",
                "message": "No transactions yet. Start tracking to get insights!",
                "color": "warning", "model": "none"}

    now = datetime.now()
    month_txns = [t for t in txns if t.date[:7] == now.strftime("%Y-%m")]
    month_total = sum(t.amount for t in month_txns)
    budget_ratio = month_total / budget if budget > 0 else 0

    # ── Try HuggingFace DistilBERT ────────────────────────────
    nlp = get_sentiment_pipeline()
    bert_score = None
    model_used = "rules"

    if nlp and nlp != "unavailable":
        try:
            # Build a natural language spending summary for BERT to analyse
            top_cats = {}
            for t in txns:
                top_cats[t.category] = top_cats.get(t.category, 0) + t.amount
            top = sorted(top_cats.items(), key=lambda x: -x[1])[:3]
            top_str = ", ".join(f"{c} ₹{int(a):,}" for c, a in top)
            pct = round(budget_ratio * 100)
            text = (
                f"This month I spent ₹{int(month_total):,} which is {pct}% of my ₹{int(budget):,} budget. "
                f"Top spending: {top_str}. "
                f"{'I exceeded my budget.' if budget_ratio > 1 else 'I am within my budget.'}"
            )
            result = nlp(text)[0]
            # POSITIVE = good financial health, NEGATIVE = concerning
            raw = result["score"]  # confidence 0–1
            if result["label"] == "POSITIVE":
                bert_score = int(raw * 100)        # e.g. 0.92 → 92
            else:
                bert_score = int((1 - raw) * 60)   # e.g. 0.85 negative → score ~9
            model_used = "distilbert"
        except Exception as e:
            print(f"DistilBERT inference error: {e}")

    # ── Compute final score ────────────────────────────────────
    if bert_score is not None:
        # Blend BERT (60%) with budget ratio (40%)
        rule_score = max(10, 100 - int(budget_ratio * 80))
        score = int(0.6 * bert_score + 0.4 * rule_score)
    else:
        score = 100
        if budget_ratio > 1.0:   score -= 40
        elif budget_ratio > 0.8: score -= 20
        elif budget_ratio > 0.6: score -= 10
        cats = set(t.category for t in txns)
        if len(cats) <= 1: score -= 10
        if len(txns) > 30: score -= 5

    score = max(10, min(100, score))

    if score >= 75:
        label, emoji, color = "Healthy", "😊", "success"
        msg = f"Great job! Spent ₹{month_total:,.0f} this month — well within your ₹{budget:,.0f} budget."
    elif score >= 50:
        label, emoji, color = "Moderate", "😐", "warning"
        msg = f"Moderate spending at ₹{month_total:,.0f} this month. Watch discretionary expenses."
    elif score >= 30:
        label, emoji, color = "Concerning", "😟", "danger"
        msg = f"High spending at ₹{month_total:,.0f} ({budget_ratio*100:.0f}% of budget). Consider cutting back."
    else:
        label, emoji, color = "Critical", "🚨", "danger"
        msg = f"Budget exceeded! ₹{month_total:,.0f} vs ₹{budget:,.0f} budget. Immediate review needed."

    return {"score": score, "label": label, "emoji": emoji, "message": msg, "color": color,
            "month_total": round(month_total, 2), "budget_ratio": round(budget_ratio * 100, 1),
            "model": model_used}


# ── 3. Anomaly Detector (Isolation Forest) ───────────────────
@app.post("/ml/anomaly")
def detect_anomalies(data: TransactionsIn):
    txns = data.transactions
    if len(txns) < 5:
        return {"anomalies": [], "model": "insufficient_data",
                "message": "Need at least 5 transactions to detect anomalies."}

    try:
        import numpy as np
        from sklearn.ensemble import IsolationForest
        from collections import defaultdict

        # Build feature matrix: [amount, day_of_week, day_of_month, category_encoded]
        cat_map = {c: i for i, c in enumerate(sorted(set(t.category for t in txns)))}
        features = []
        for t in txns:
            try:
                d = datetime.strptime(t.date[:10], "%Y-%m-%d")
                features.append([
                    t.amount,
                    d.weekday(),          # 0=Mon … 6=Sun
                    d.day,                # 1–31
                    cat_map.get(t.category, 0)
                ])
            except Exception:
                features.append([t.amount, 0, 1, cat_map.get(t.category, 0)])

        X = np.array(features)
        # Normalize amount column so it doesn't dominate
        X[:, 0] = (X[:, 0] - X[:, 0].mean()) / (X[:, 0].std() + 1e-9)

        clf = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
        preds = clf.fit_predict(X)          # -1 = anomaly, 1 = normal
        scores = clf.score_samples(X)       # lower = more anomalous

        # Category-level stats for human-readable reason
        cat_amounts = defaultdict(list)
        for t in txns:
            cat_amounts[t.category].append(t.amount)
        cat_avg = {c: sum(v)/len(v) for c, v in cat_amounts.items()}

        anomalies = []
        for i, (t, pred, score) in enumerate(zip(txns, preds, scores)):
            if pred == -1:
                avg = cat_avg.get(t.category, t.amount)
                direction = "high" if t.amount > avg else "low"
                anomalies.append({
                    "index": i,
                    "title": t.title,
                    "amount": t.amount,
                    "category": t.category,
                    "date": t.date,
                    "anomaly_score": round(float(score), 4),
                    "reason": f"Unusually {direction} for {t.category} (avg ₹{avg:,.0f})"
                })

        # Sort by most anomalous first
        anomalies.sort(key=lambda x: x["anomaly_score"])
        return {"anomalies": anomalies[:5], "model": "isolation_forest",
                "total_scanned": len(txns)}

    except Exception as e:
        # Fallback to z-score method
        import statistics
        from collections import defaultdict
        cat_amounts = defaultdict(list)
        for t in txns:
            cat_amounts[t.category].append(t.amount)
        anomalies = []
        for i, t in enumerate(txns):
            amounts = cat_amounts[t.category]
            if len(amounts) < 3:
                continue
            mean = statistics.mean(amounts)
            stdev = statistics.stdev(amounts)
            if stdev > 0 and abs(t.amount - mean) > 2 * stdev:
                anomalies.append({
                    "index": i, "title": t.title, "amount": t.amount,
                    "category": t.category, "date": t.date,
                    "reason": f"Unusually {'high' if t.amount > mean else 'low'} for {t.category} (avg ₹{mean:,.0f})"
                })
        return {"anomalies": anomalies[:5], "model": "zscore_fallback"}


# ── 4. Spend Forecaster ───────────────────────────────────────
@app.post("/ml/forecast")
def forecast_spending(data: ForecastIn):
    txns = data.transactions
    if not txns:
        return {"forecast": 0, "trend": "neutral", "message": "Not enough data to forecast."}

    from collections import defaultdict
    monthly = defaultdict(float)
    for t in txns:
        monthly[t.date[:7]] += t.amount

    months = sorted(monthly.keys())
    if len(months) < 2:
        only = list(monthly.values())[0]
        return {"forecast": round(only, 2), "trend": "neutral",
                "message": f"Only 1 month of data. Estimated: ₹{only:,.0f}",
                "monthly_data": [{"month": m, "amount": round(monthly[m], 2)} for m in months]}

    values = [monthly[m] for m in months]
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0
    forecast = max(0, (y_mean - slope * x_mean) + slope * n)
    pct = (slope / y_mean * 100) if y_mean > 0 else 0

    if pct > 5:    trend, note = "up",      f"📈 Trending UP ~{abs(pct):.0f}% per month"
    elif pct < -5: trend, note = "down",    f"📉 Trending DOWN ~{abs(pct):.0f}% — great job!"
    else:          trend, note = "neutral", "📊 Spending is stable"

    return {"forecast": round(forecast, 2), "trend": trend,
            "message": f"Next month forecast: ₹{forecast:,.0f}. {note}",
            "monthly_data": [{"month": m, "amount": round(monthly[m], 2)} for m in months],
            "slope": round(slope, 2)}


# ── 5. Auto-Summarizer ────────────────────────────────────────
@app.post("/ml/summarize")
def summarize(data: SentimentIn):
    txns = data.transactions
    budget = data.budget or 50000
    if not txns:
        return {"summary": "No expenses recorded yet. Add your first expense to get started!"}

    from collections import defaultdict
    now = datetime.now()
    month_txns = [t for t in txns if t.date[:7] == now.strftime("%Y-%m")]
    month_total = sum(t.amount for t in month_txns)
    cat_totals = defaultdict(float)
    for t in txns:
        cat_totals[t.category] += t.amount
    top_cat = max(cat_totals, key=cat_totals.get) if cat_totals else "None"
    top_amount = cat_totals.get(top_cat, 0)
    budget_pct = (month_total / budget * 100) if budget > 0 else 0

    lines = [
        f"You have {len(txns)} expense{'s' if len(txns)>1 else ''} recorded in total.",
        f"This month: ₹{month_total:,.0f} ({budget_pct:.0f}% of ₹{budget:,.0f} budget).",
        f"Top category: {top_cat} at ₹{top_amount:,.0f}.",
    ]
    if budget_pct > 90:
        lines.append("⚠️ Close to budget limit — review discretionary spending.")
    elif budget_pct < 50:
        lines.append("👍 Staying comfortably within budget this month.")

    return {"summary": " ".join(lines)}


# ── 6. Duplicate Detector ─────────────────────────────────────
@app.post("/ml/duplicate-check")
def check_duplicate(data: DuplicateIn):
    txns = data.transactions
    new_title = data.new_title.lower().strip()
    new_amount = data.new_amount

    def similarity(a: str, b: str) -> float:
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())
        if not a_words or not b_words: return 0.0
        return len(a_words & b_words) / max(len(a_words), len(b_words))

    duplicates = []
    for t in txns:
        title_sim = similarity(new_title, t.title)
        amount_sim = 1.0 if abs(t.amount - new_amount) < 1 else max(0, 1 - abs(t.amount - new_amount) / max(new_amount, 1))
        combined = 0.6 * title_sim + 0.4 * amount_sim
        if combined >= 0.65:
            duplicates.append({"title": t.title, "amount": t.amount,
                                "date": t.date, "similarity": round(combined * 100, 1)})

    duplicates.sort(key=lambda x: -x["similarity"])
    return {
        "is_duplicate": len(duplicates) > 0,
        "matches": duplicates[:3],
        "message": f"⚠️ Possible duplicate: '{duplicates[0]['title']}' on {duplicates[0]['date']}" if duplicates else ""
    }
