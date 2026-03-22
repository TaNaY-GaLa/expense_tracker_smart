"""
Expense Tracker - Single Command Launcher
Starts both Django (port 8000 → moved to 5000) and FastAPI ML (port 8001).

Usage:
    python run.py

Django UI:     http://localhost:5000
ML API docs:   http://localhost:8001/docs
"""
import subprocess, sys, os, time, threading

BASE   = os.path.dirname(os.path.abspath(__file__))
python = sys.executable

def run_fastapi():
    print("⚡ FastAPI ML server starting on port 8001...")
    subprocess.run(
        [python, "-m", "uvicorn", "ml_api:app", "--host", "0.0.0.0", "--port", "8001"],
        cwd=BASE
    )

def run_django():
    print("🌐 Django app starting on port 5000...")
    subprocess.run(
        [python, "manage.py", "runserver", "5000"],
        cwd=BASE
    )

def setup_django():
    print("⚙️  Running Django migrations...")
    subprocess.run([python, "manage.py", "migrate", "--run-syncdb"], cwd=BASE)
    print("✅ Database ready!\n")

def train_if_needed():
    model = os.path.join(BASE, "ml", "category_model.pkl")
    if not os.path.exists(model):
        print("🤖 Training ML models (first run only)...")
        r = subprocess.run([python, "ml/train.py"], cwd=BASE)
        if r.returncode == 0: print("✅ ML models trained!\n")
        else: print("⚠️  Model training failed — rule-based fallback active\n")
    else:
        print("✅ ML models ready\n")

if __name__ == "__main__":
    print("=" * 55)
    print("   Expense Tracker (Django) — Starting Up")
    print("=" * 55)

    try:
        import django, fastapi, uvicorn
        print(f"✅ Django {django.__version__} | FastAPI {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        sys.exit(1)

    setup_django()
    train_if_needed()

    print("🚀 Starting FastAPI ML server → http://localhost:8001")
    print("🚀 Starting Django app         → http://localhost:5000")
    print("🔑 Django Admin                → http://localhost:5000/admin")
    print("📖 ML API docs                 → http://localhost:8001/docs")
    print("-" * 55)
    print("Press Ctrl+C to stop\n")

    t = threading.Thread(target=run_fastapi, daemon=True)
    t.start()
    time.sleep(1)

    try:
        run_django()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
