from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pydantic import BaseModel, field_validator, ValidationError
import json, os, re
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "expense_secret_2024"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
DB_FILE = os.path.join(os.path.dirname(__file__), "data", "db.json")

# ── Pydantic Models ───────────────────────────────────────────
class TransactionModel(BaseModel):
    title: str
    amount: float
    category: str
    date: str
    currency: str

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip(): raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('amount')
    @classmethod
    def amount_positive(cls, v):
        if v <= 0: raise ValueError('Amount must be positive')
        return v

    @field_validator('currency')
    @classmethod
    def currency_valid(cls, v):
        allowed = ['INR','USD','EUR','GBP','JPY','AED','SGD']
        if v not in allowed: raise ValueError(f'Currency must be one of {allowed}')
        return v

class UserModel(BaseModel):
    username: str
    password: str
    email: str
    mobile: str

    @field_validator('username')
    @classmethod
    def username_length(cls, v):
        if len(v.strip()) < 3: raise ValueError('Username must be at least 3 characters')
        return v.strip()

    @field_validator('email')
    @classmethod
    def email_format(cls, v):
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', v): raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('mobile')
    @classmethod
    def mobile_format(cls, v):
        if not re.match(r'^[6-9]\d{9}$', v): raise ValueError('Mobile must be 10 digits starting with 6-9')
        return v

# ── DB helpers ────────────────────────────────────────────────
def load_db():
    if not os.path.exists(DB_FILE):
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        with open(DB_FILE, "w") as f:
            json.dump({"users": [], "transactions": [], "splits": [], "mess_bills": [], "savings_goals": []}, f)
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

RATES = {'INR':1,'USD':83.5,'EUR':90.2,'GBP':105.8,'JPY':0.56,'AED':22.7,'SGD':62.1}

# ── Page routes ───────────────────────────────────────────────
@app.route("/")
def home():
    if "user_id" not in session: return redirect(url_for("login"))
    return render_template("index.html", username=session["username"])

@app.route("/history")
def history():
    if "user_id" not in session: return redirect(url_for("login"))
    return render_template("history.html", username=session["username"])

@app.route("/split")
def split_page():
    if "user_id" not in session: return redirect(url_for("login"))
    return render_template("split.html", username=session["username"])

@app.route("/mess")
def mess_page():
    if "user_id" not in session: return redirect(url_for("login"))
    return render_template("mess.html", username=session["username"])

@app.route("/profile")
def profile_page():
    if "user_id" not in session: return redirect(url_for("login"))
    data = load_db()
    user = next((u for u in data["users"] if u["id"] == session["user_id"]), {})
    return render_template("profile.html", username=session["username"], user=user)

# ── Auth ──────────────────────────────────────────────────────
@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method == "POST":
        try:
            user = UserModel(
                username=request.form.get("username",""),
                password=request.form.get("password",""),
                email=request.form.get("email",""),
                mobile=request.form.get("mobile","")
            )
            data = load_db()
            if any(u["username"]==user.username for u in data["users"]):
                error = "Username already exists."
            else:
                uid = max([u["id"] for u in data["users"]], default=0) + 1
                data["users"].append({
                    "id": uid, "username": user.username, "password": user.password,
                    "email": user.email, "mobile": user.mobile, "budget": 50000,
                    "language": "en", "dark_mode": False,
                    "profile_pic": "static/images/profile_placeholder.png",
                    "savings_goals": []
                })
                save_db(data)
                return redirect(url_for("login"))
        except ValidationError as e:
            error = e.errors()[0]["msg"]
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        data = load_db()
        user = next((u for u in data["users"] if u["username"]==username and u["password"]==password), None)
        if user:
            session.permanent = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Transactions API ──────────────────────────────────────────
@app.route("/api/transactions", methods=["GET"])
def api_get_transactions():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    txns = [t for t in data["transactions"] if t["user_id"]==session["user_id"]]
    return jsonify({"status":"success","count":len(txns),"transactions":txns})

@app.route("/api/summary", methods=["GET"])
def api_summary():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    txns = [t for t in data["transactions"] if t["user_id"]==session["user_id"]]
    total = sum(t["amount_inr"] for t in txns)
    user = next((u for u in data["users"] if u["id"]==session["user_id"]), {})
    return jsonify({"status":"success","total_expense_inr":round(total,2),
                    "transaction_count":len(txns),"budget":user.get("budget",50000)})

@app.route("/api/transactions", methods=["POST"])
def api_add_transaction():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    try:
        txn = TransactionModel(**request.json)
        data = load_db()
        txn_id = max([t["id"] for t in data["transactions"]], default=0) + 1
        record = {"id":txn_id,"user_id":session["user_id"],"title":txn.title,"amount":txn.amount,
                  "category":txn.category,"date":txn.date,"currency":txn.currency,
                  "amount_inr":round(txn.amount*RATES.get(txn.currency,1),2)}
        data["transactions"].append(record)
        save_db(data)
        return jsonify({"status":"success","transaction":record}), 201
    except ValidationError as e:
        return jsonify({"error":e.errors()[0]["msg"]}), 400

@app.route("/api/transactions/<int:id>", methods=["PUT"])
def api_edit_transaction(id):
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    try:
        txn = TransactionModel(**request.json)
        data = load_db()
        for t in data["transactions"]:
            if t["id"]==id and t["user_id"]==session["user_id"]:
                t.update({"title":txn.title,"amount":txn.amount,"category":txn.category,
                          "date":txn.date,"currency":txn.currency,
                          "amount_inr":round(txn.amount*RATES.get(txn.currency,1),2)})
                save_db(data)
                return jsonify({"status":"updated","transaction":t})
        return jsonify({"error":"Not found"}), 404
    except ValidationError as e:
        return jsonify({"error":e.errors()[0]["msg"]}), 400

@app.route("/api/transactions/<int:id>", methods=["DELETE"])
def api_delete_transaction(id):
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    before = len(data["transactions"])
    data["transactions"] = [t for t in data["transactions"] if not (t["id"]==id and t["user_id"]==session["user_id"])]
    if len(data["transactions"])==before: return jsonify({"error":"Not found"}), 404
    save_db(data)
    return jsonify({"status":"deleted"})

@app.route("/api/budget", methods=["PUT"])
def api_set_budget():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    budget = request.json.get("budget",0)
    if budget <= 0: return jsonify({"error":"Budget must be positive"}), 400
    data = load_db()
    for u in data["users"]:
        if u["id"]==session["user_id"]: u["budget"] = budget
    save_db(data)
    return jsonify({"status":"budget updated","budget":budget})

@app.route("/api/validate/transaction", methods=["POST"])
def api_validate_transaction():
    try:
        txn = TransactionModel(**request.json)
        return jsonify({"valid":True,"data":txn.model_dump()})
    except ValidationError as e:
        return jsonify({"valid":False,"errors":e.errors()}), 422

# ── Analytics API ─────────────────────────────────────────────
@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    txns = [t for t in data["transactions"] if t["user_id"]==session["user_id"]]
    user = next((u for u in data["users"] if u["id"]==session["user_id"]), {})
    budget = user.get("budget", 50000)

    from collections import defaultdict
    from datetime import datetime

    # Monthly totals
    monthly = defaultdict(float)
    for t in txns:
        monthly[t["date"][:7]] += t["amount_inr"]

    # Category totals
    cat_totals = defaultdict(float)
    for t in txns:
        cat_totals[t["category"]] += t["amount_inr"]

    # Day of week
    dow = defaultdict(float)
    for t in txns:
        try:
            d = datetime.strptime(t["date"][:10], "%Y-%m-%d")
            dow[d.strftime("%a")] += t["amount_inr"]
        except: pass

    # This month vs last month
    now = datetime.now()
    this_month = now.strftime("%Y-%m")
    last_month_dt = (now.replace(day=1) - timedelta(days=1))
    last_month = last_month_dt.strftime("%Y-%m")

    this_cat = defaultdict(float)
    last_cat = defaultdict(float)
    for t in txns:
        if t["date"][:7] == this_month: this_cat[t["category"]] += t["amount_inr"]
        if t["date"][:7] == last_month: last_cat[t["category"]] += t["amount_inr"]

    return jsonify({
        "monthly": dict(sorted(monthly.items())),
        "categories": dict(sorted(cat_totals.items(), key=lambda x: -x[1])),
        "day_of_week": dict(dow),
        "this_month": dict(this_cat),
        "last_month": dict(last_cat),
        "budget": budget,
        "total": round(sum(cat_totals.values()), 2)
    })

# ── Profile API ───────────────────────────────────────────────
@app.route("/api/profile", methods=["PUT"])
def api_update_profile():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    body = request.json
    data = load_db()
    for u in data["users"]:
        if u["id"] == session["user_id"]:
            if "email" in body: u["email"] = body["email"]
            if "mobile" in body: u["mobile"] = body["mobile"]
            if "language" in body: u["language"] = body["language"]
            if "dark_mode" in body: u["dark_mode"] = body["dark_mode"]
            if "budget" in body: u["budget"] = float(body["budget"])
            if "password" in body and body["password"]:
                u["password"] = body["password"]
            save_db(data)
            return jsonify({"status":"updated"})
    return jsonify({"error":"User not found"}), 404

# ── Savings Goals API ─────────────────────────────────────────
@app.route("/api/savings-goals", methods=["GET"])
def api_get_goals():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    user = next((u for u in data["users"] if u["id"]==session["user_id"]), {})
    return jsonify({"goals": user.get("savings_goals", [])})

@app.route("/api/savings-goals", methods=["POST"])
def api_add_goal():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    body = request.json
    data = load_db()
    for u in data["users"]:
        if u["id"] == session["user_id"]:
            if "savings_goals" not in u: u["savings_goals"] = []
            gid = max([g["id"] for g in u["savings_goals"]], default=0) + 1
            goal = {"id": gid, "title": body["title"], "target": float(body["target"]),
                    "saved": float(body.get("saved", 0)), "deadline": body.get("deadline","")}
            u["savings_goals"].append(goal)
            save_db(data)
            return jsonify({"status":"created","goal":goal}), 201
    return jsonify({"error":"User not found"}), 404

@app.route("/api/savings-goals/<int:id>", methods=["PUT"])
def api_update_goal(id):
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    body = request.json
    data = load_db()
    for u in data["users"]:
        if u["id"] == session["user_id"]:
            for g in u.get("savings_goals", []):
                if g["id"] == id:
                    g.update({k: body[k] for k in body if k in g})
                    save_db(data)
                    return jsonify({"status":"updated","goal":g})
    return jsonify({"error":"Not found"}), 404

@app.route("/api/savings-goals/<int:id>", methods=["DELETE"])
def api_delete_goal(id):
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    for u in data["users"]:
        if u["id"] == session["user_id"]:
            u["savings_goals"] = [g for g in u.get("savings_goals",[]) if g["id"] != id]
            save_db(data)
            return jsonify({"status":"deleted"})
    return jsonify({"error":"Not found"}), 404

# ── Mess API ──────────────────────────────────────────────────
@app.route("/api/mess", methods=["GET"])
def api_get_mess():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    bills = [b for b in data.get("mess_bills",[]) if b.get("user_id")==session["user_id"]]
    return jsonify({"bills": bills})

@app.route("/api/mess", methods=["POST"])
def api_add_mess():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    body = request.json
    data = load_db()
    if "mess_bills" not in data: data["mess_bills"] = []
    mid = max([b["id"] for b in data["mess_bills"]], default=0) + 1
    bill = {"id":mid,"user_id":session["user_id"],"month":body.get("month",""),
            "amount":float(body.get("amount",0)),"paid":body.get("paid",False),"note":body.get("note","")}
    data["mess_bills"].append(bill)
    save_db(data)
    return jsonify({"status":"created","bill":bill}), 201

@app.route("/api/mess/<int:id>", methods=["PUT"])
def api_update_mess(id):
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    body = request.json
    data = load_db()
    for b in data.get("mess_bills",[]):
        if b["id"]==id and b["user_id"]==session["user_id"]:
            b.update({k: body[k] for k in body if k in b})
            save_db(data)
            return jsonify({"status":"updated","bill":b})
    return jsonify({"error":"Not found"}), 404

@app.route("/api/mess/<int:id>", methods=["DELETE"])
def api_delete_mess(id):
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    data["mess_bills"] = [b for b in data.get("mess_bills",[]) if not (b["id"]==id and b["user_id"]==session["user_id"])]
    save_db(data)
    return jsonify({"status":"deleted"})

# ── Splits API ────────────────────────────────────────────────
@app.route("/api/splits", methods=["GET"])
def api_get_splits():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    splits = [s for s in data.get("splits",[]) if s.get("user_id")==session["user_id"]]
    return jsonify({"splits": splits})

@app.route("/api/splits", methods=["POST"])
def api_add_split():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    body = request.json
    if not body.get("title") or not body.get("total") or not body.get("friends"):
        return jsonify({"error":"title, total, and friends are required"}), 400
    data = load_db()
    if "splits" not in data: data["splits"] = []
    sid = max([s["id"] for s in data["splits"]], default=0) + 1
    record = {
        "id": sid, "user_id": session["user_id"],
        "title": body["title"], "total": float(body["total"]),
        "date": body.get("date",""),
        "paid_by": body.get("paid_by", session["username"]),
        "friends": body.get("friends",[]),
        "split_type": body.get("split_type","equal"),
        "shares": body.get("shares",{}),
        "settlements": body.get("settlements",{}),
    }
    data["splits"].append(record)
    save_db(data)
    return jsonify({"status":"created","split":record}), 201

@app.route("/api/splits/<int:id>", methods=["DELETE"])
def api_delete_split(id):
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    data["splits"] = [s for s in data.get("splits",[]) if not (s["id"]==id and s["user_id"]==session["user_id"])]
    save_db(data)
    return jsonify({"status":"deleted"})

@app.route("/api/splits/<int:id>/settle", methods=["POST"])
def api_settle_person(id):
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    person = request.json.get("person")
    data = load_db()
    for s in data.get("splits",[]):
        if s["id"]==id and s["user_id"]==session["user_id"]:
            if person in s.get("settlements",{}):
                s["settlements"][person]["settled"] = True
            save_db(data)
            return jsonify({"status":"settled","person":person})
    return jsonify({"error":"Not found"}), 404

@app.route("/api/splits/<int:id>/settle-all", methods=["POST"])
def api_settle_all(id):
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = load_db()
    for s in data.get("splits",[]):
        if s["id"]==id and s["user_id"]==session["user_id"]:
            for person in s.get("settlements",{}):
                s["settlements"][person]["settled"] = True
            save_db(data)
            return jsonify({"status":"all settled"})
    return jsonify({"error":"Not found"}), 404

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    app.run(debug=True, port=5000)
