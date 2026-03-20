"""
Train ML models for Expense Tracker.
Run once: python ml/train.py
Creates: ml/category_model.pkl
"""
import os, pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

TRAIN_DATA = [
    ("lunch canteen", "Food"), ("dinner restaurant", "Food"), ("breakfast cafe", "Food"),
    ("coffee starbucks", "Food"), ("pizza dominos", "Food"), ("burger mcdonalds", "Food"),
    ("biryani hotel", "Food"), ("swiggy order", "Food"), ("zomato food", "Food"),
    ("mess bill", "Food"), ("grocery vegetables", "Food"), ("milk bread", "Food"),
    ("tea snacks", "Food"), ("meal", "Food"), ("rice dal sabji", "Food"),
    ("eating out", "Food"), ("food delivery", "Food"), ("canteen food", "Food"),
    ("uber ride", "Travel"), ("ola cab", "Travel"), ("auto rickshaw", "Travel"),
    ("train ticket", "Travel"), ("bus pass", "Travel"), ("flight ticket", "Travel"),
    ("petrol fuel", "Travel"), ("hotel stay", "Travel"), ("airbnb", "Travel"),
    ("trip goa", "Travel"), ("travel expense", "Travel"), ("metro card", "Travel"),
    ("toll tax", "Travel"), ("taxi", "Travel"), ("rapido bike", "Travel"),
    ("shirt myntra", "Clothing"), ("jeans clothes", "Clothing"), ("dress shopping", "Clothing"),
    ("shoes footwear", "Clothing"), ("jacket winter", "Clothing"), ("saree", "Clothing"),
    ("kurta ethnic", "Clothing"), ("fashion outfit", "Clothing"), ("top tshirt", "Clothing"),
    ("clothing accessories", "Clothing"), ("pant trousers", "Clothing"),
    ("netflix subscription", "Entertainment"), ("spotify music", "Entertainment"),
    ("movie tickets", "Entertainment"), ("concert show", "Entertainment"),
    ("gaming steam", "Entertainment"), ("party club", "Entertainment"),
    ("amazon prime", "Entertainment"), ("hotstar", "Entertainment"),
    ("weekend outing", "Entertainment"), ("amusement park", "Entertainment"),
    ("youtube premium", "Entertainment"), ("cricket match", "Entertainment"),
    ("textbook college", "Books"), ("notes printing", "Books"), ("pen stationery", "Books"),
    ("course udemy", "Books"), ("exam fees", "Books"), ("library fine", "Books"),
    ("book novel", "Books"), ("notebook", "Books"), ("kindle ebook", "Books"),
    ("coaching class", "Books"), ("study material", "Books"),
    ("doctor visit", "Health"), ("medicine pharmacy", "Health"), ("hospital bill", "Health"),
    ("gym membership", "Health"), ("yoga class", "Health"), ("medical test", "Health"),
    ("protein supplement", "Health"), ("tablet capsule", "Health"),
    ("health checkup", "Health"), ("clinic consultation", "Health"),
    ("maintenance charges", "Other"), ("electricity bill", "Other"), ("wifi internet", "Other"),
    ("mobile recharge", "Other"), ("rent", "Other"), ("insurance", "Other"),
    ("gift", "Other"), ("donation", "Other"), ("miscellaneous", "Other"),
]

def train():
    texts  = [x[0] for x in TRAIN_DATA]
    labels = [x[1] for x in TRAIN_DATA]
    classes = sorted(set(labels))
    vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1)
    clf = MultinomialNB(alpha=0.5)
    X = vectorizer.fit_transform(texts)
    clf.fit(X, labels)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "category_model.pkl")
    with open(out, "wb") as f:
        pickle.dump({"vectorizer": vectorizer, "classifier": clf, "classes": classes}, f)
    print(f"Model trained and saved to {out}")
    print(f"Classes: {classes}")

if __name__ == "__main__":
    train()
