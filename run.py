"""
Expense Tracker - Single Command Launcher
Starts both Flask (port 5000) and FastAPI (port 8000).

Usage:
    python run.py

Flask UI:      http://localhost:5000
ML API docs:   http://localhost:8000/docs
"""
import subprocess, sys, os, time, threading

BASE   = os.path.dirname(os.path.abspath(__file__))
python = sys.executable

def run_fastapi():
    print("⚡ FastAPI ML server starting...")
    result = subprocess.run(
        [python, "-m", "uvicorn", "ml_api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=BASE
    )
    if result.returncode != 0:
        print("\n❌ FastAPI failed to start!")
        print("   Fix: pip install -r requirements.txt")

def run_flask():
    print("🌐 Flask app starting...")
    subprocess.run([python, "app.py"], cwd=BASE)

def train_if_needed():
    model = os.path.join(BASE, "ml", "category_model.pkl")
    if not os.path.exists(model):
        print("🤖 Training ML models (first run only)...")
        r = subprocess.run([python, "ml/train.py"], cwd=BASE)
        if r.returncode == 0:
            print("✅ ML models trained!\n")
        else:
            print("⚠️  Model training failed — rule-based fallback will be used\n")
    else:
        print("✅ ML models ready\n")

if __name__ == "__main__":
    print("=" * 55)
    print("   Expense Tracker — Starting Up")
    print("=" * 55)
    print()

    # Step 1: check dependencies
    try:
        import fastapi, uvicorn, pydantic
        print(f"✅ FastAPI {fastapi.__version__} | Pydantic {pydantic.__version__}")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        sys.exit(1)

    # Step 2: train if needed
    train_if_needed()

    print("🚀 Starting FastAPI ML server → http://localhost:8000")
    print("🚀 Starting Flask app         → http://localhost:5000")
    print("📖 ML API docs                → http://localhost:8000/docs")
    print("-" * 55)
    print("Press Ctrl+C to stop\n")

    t = threading.Thread(target=run_fastapi, daemon=True)
    t.start()
    time.sleep(2)

    try:
        run_flask()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
